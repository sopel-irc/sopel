# coding=utf-8
"""
irc.py - A Utility IRC Bot
Copyright 2008, Sean B. Palmer, inamidst.com
Copyright 2012, Edward Powell, http://embolalia.net
Copyright © 2012, Elad Alfassa <elad@fedoraproject.org>

Licensed under the Eiffel Forum License 2.

Willie: http://willie.dftba.net/

When working on core IRC protocol related features, consult protocol
documentation at http://www.irchelp.org/irchelp/rfc/
"""

import sys
import re
import time
import traceback
import socket
import asyncore
import asynchat
import os
import codecs
import traceback
from tools import stderr, stdout
try:
    import select
    import ssl
    has_ssl = True
except:
    #no SSL support
    has_ssl = False
import errno
import threading
from datetime import datetime
from tools import verify_ssl_cn


class Origin(object):
    source = re.compile(r'([^!]*)!?([^@]*)@?(.*)')

    def __init__(self, bot, source, args):
        #Split out the nick, user, and host from hostmask per the regex above.
        match = Origin.source.match(source or '')
        self.nick, self.user, self.host = match.groups()

        # If we have more than one argument, the second one is the sender
        if len(args) > 1:
            target = args[1]
        else:
            target = None

        # Unless we're messaging the bot directly, in which case that second
        # arg will be our bot's name.
        if target and target.lower() == bot.nick.lower():
            target = self.nick
        self.sender = target


class Bot(asynchat.async_chat):
    def __init__(self, config):
        if config.ca_certs is not None:
            ca_certs = config.ca_certs
        else:
            ca_certs = '/etc/pki/tls/cert.pem'

        if config.log_raw is None:
            #Default is to log raw data, can be disabled in config
            config.log_raw = True
        asynchat.async_chat.__init__(self)
        self.set_terminator('\n')
        self.buffer = ''

        self.nick = config.nick
        """Willie's current nick. Changing this while Willie is running is
        untested."""
        self.user = config.user
        """Willie's user/ident."""
        self.name = config.name
        """Willie's "real name", as used for whois."""

        self.verbose = True
        """True if Willie is running in verbose mode."""
        self.channels = []
        """The list of channels Willie is currently in."""

        self.stack = []
        self.ca_certs = ca_certs
        self.hasquit = False

        self.sending = threading.RLock()
        self.writing_lock = threading.Lock()
        self.raw = None

        #Right now, only accounting for two op levels.
        #This might be expanded later.
        #These lists are filled in startup.py, as of right now.
        self.ops = dict()
        """A dictionary mapping channels to a list of their operators."""
        self.halfplus = dict()
        """A dictionary mapping channels to a list of their half-ops and
        ops."""

        #We need this to prevent error loops in handle_error
        self.error_count = 0
        self.last_error_timestamp = None

    def log_raw(self, line):
        ''' Log raw line to the raw log '''
        if not self.config.core.log_raw:
            return
        if not self.config.core.logdir:
            self.config.core.logdir = os.path.join(self.config.dotdir,
                                                   'logs')
        if not os.path.isdir(self.config.core.logdir):
            try:
                os.mkdir(self.config.core.logdir)
            except Exception, e:
                stderr('There was a problem creating the logs directory.')
                stderr(e.__class__, str(e))
                stderr('Please fix this and then run Willie again.')
                os._exit(1)
        f = codecs.open(os.path.join(self.config.core.logdir, 'raw.log'),
                        'a', encoding='utf-8')
        f.write(str(time.time()) + "\t")
        temp = line.replace('\n', '')
        try:
            temp = temp.decode('utf-8')
        except UnicodeDecodeError:
            try:
                temp = temp.decode('iso-8859-1')
            except UnicodeDecodeError:
                temp = temp.decode('cp1252')
        f.write(temp)
        f.write("\n")
        f.close()

    def safe(self, string):
        '''Remove newlines from a string and make sure it is utf8'''
        string = str(string)
        string = string.replace('\n', '')
        string = string.replace('\r', '')
        try:
            return string.encode('utf-8')
        except:
            return string

    def write(self, args, text=None):
        """
        Send a command to the server. In the simplest case, ``args`` is a list
        containing just the command you wish to send, and ``text`` the argument
        to that command {e.g. write(['JOIN'], '#channel')}

        More specifically, ``args`` will be joined together, separated by a
        space. If text is given, it will be added preceeded by a space and a
        colon (' :').

        Newlines and carriage returns ('\\n' and '\\r') are removed before
        sending. Additionally, if the joined ``args`` and ``text`` are more
        than 510 characters, any remaining characters will not be sent.
        """
        args = [self.safe(arg) for arg in args]
        if text is not None:
            text = self.safe(text)
        try:
            self.writing_lock.acquire()  # Blocking lock, can't send two things
                                         # at a time

            #From RFC2812 Internet Relay Chat: Client Protocol
            #Section 2.3
            #
            #https://tools.ietf.org/html/rfc2812.html
            #
            #IRC messages are always lines of characters terminated with a
            #CR-LF (Carriage Return - Line Feed) pair, and these messages SHALL
            #NOT exceed 512 characters in length, counting all characters
            #including the trailing CR-LF. Thus, there are 510 characters
            #maximum allowed for the command and its parameters.  There is no
            #provision for continuation of message lines.

            if text is not None:
                temp = (' '.join(args) + ' :' + text)[:510] + '\r\n'
            else:
                temp = ' '.join(args)[:510] + '\r\n'
            self.log_raw(temp)
            self.send(temp)
        finally:
            self.writing_lock.release()

    def run(self, host, port=6667):
        self.initiate_connect(host, port)

    def initiate_connect(self, host, port):
        if self.verbose:
            message = 'Connecting to %s:%s...' % (host, port)
            stderr(message)
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        if self.config.core.bind_host is not None:
            self.socket.bind((self.config.core.bind_host, 0))
        if self.config.core.use_ssl and has_ssl:
            self.send = self._ssl_send
            self.recv = self._ssl_recv
        elif not has_ssl and self.config.core.use_ssl:
            stderr('SSL is not avilable on your system, attempting connection '
                   'without it')
        self.connect((host, port))
        try:
            asyncore.loop()
        except KeyboardInterrupt:
            print 'KeyboardInterrupt'
            self.quit('KeyboardInterrupt')

    def quit(self, message):
        '''Disconnect from IRC and close the bot'''
        self.write(['QUIT'], message)
        self.hasquit = True

    def part(self, channel):
        '''Part a channel'''
        self.write(['PART'], channel)

    def join(self, channel, password=None):
        '''Join a channel'''
        if password is None:
            self.write(['JOIN'], channel)
        else:
            self.write(['JOIN', channel, password])

    def handle_connect(self):
        if self.config.core.use_ssl and has_ssl:
            if not self.config.core.verify_ssl:
                self.ssl = ssl.wrap_socket(self.socket,
                                           do_handshake_on_connect=False,
                                           suppress_ragged_eofs=True)
            else:
                verification = verify_ssl_cn(self.config.host,
                                             int(self.config.port))
                if verification is 'NoCertFound':
                    stderr('Can\'t get server certificate, SSL might be '
                           'disabled on the server.')
                    sys.exit(1)
                elif verification is not None:
                    stderr('\nSSL Cret information: %s' % verification[1])
                    if verification[0] is False:
                        stderr("Invalid cretficate, CN mismatch!")
                        sys.exit(1)
                else:
                    stderr('WARNING! certficate information and CN validation '
                           'are not avilable. Is pyOpenSSL installed?')
                    stderr('Trying to connect anyway:')
                self.ssl = ssl.wrap_socket(self.socket,
                                           do_handshake_on_connect=False,
                                           suppress_ragged_eofs=True,
                                           cert_reqs=ssl.CERT_REQUIRED,
                                           ca_certs=self.ca_certs)
            stderr('\nSSL Handshake intiated...')
            error_count = 0
            while True:
                try:
                    self.ssl.do_handshake()
                    break
                except ssl.SSLError, err:
                    if err.args[0] == ssl.SSL_ERROR_WANT_READ:
                        select.select([self.ssl], [], [])
                    elif err.args[0] == ssl.SSL_ERROR_WANT_WRITE:
                        select.select([], [self.ssl], [])
                    elif err.args[0] == 1:
                        stderr('SSL Handshake failed with error: %s' %
                               err.args[1])
                        os._exit(1)
                    else:
                        error_count = error_count + 1
                        if error_count > 5:
                            stderr('SSL Handshake failed (%d failed attempts)'
                                   % error_count)
                            os._exit(1)
                        raise
                except Exception as e:
                    print >> sys.stderr, ('SSL Handshake failed with error: %s'
                                          % e)
                    os._exit(1)
            self.set_socket(self.ssl)
        self.write(('NICK', self.nick))
        self.write(('USER', self.user, '+iw', self.nick), self.name)

        if self.config.core.server_password is not None:
            self.write(('PASS', self.config.core.server_password))
        stderr('Connected.')

    def _ssl_send(self, data):
        """ Replacement for self.send() during SSL connections. """
        try:
            result = self.socket.send(data)
            return result
        except ssl.SSLError, why:
            if why[0] in (asyncore.EWOULDBLOCK, errno.ESRCH):
                return 0
            else:
                raise ssl.SSLError, why
            return 0

    def _ssl_recv(self, buffer_size):
        """ Replacement for self.recv() during SSL connections. From:
        http://evanfosmark.com/2010/09/ssl-support-in-asynchatasync_chat """
        try:
            data = self.read(buffer_size)
            if not data:
                self.handle_close()
                return ''
            return data
        except ssl.SSLError, why:
            if why[0] in (asyncore.ECONNRESET, asyncore.ENOTCONN,
                          asyncore.ESHUTDOWN):
                self.handle_close()
                return ''
            elif why[0] == errno.ENOENT:
                # Required in order to keep it non-blocking
                return ''
            else:
                raise

    def handle_close(self):
        self.close()
        stderr('Closed!')

    def collect_incoming_data(self, data):
        if data:
            self.log_raw(data)
        self.buffer += data

    def found_terminator(self):
        line = self.buffer
        if line.endswith('\r'):
            line = line[:-1]
        self.buffer = ''
        self.raw = line
        if line.startswith(':'):
            source, line = line[1:].split(' ', 1)
        else:
            source = None

        if ' :' in line:
            argstr, text = line.split(' :', 1)
        else:
            argstr, text = line, ''
        args = argstr.split()

        if args[0] == 'PING':
            self.write(('PONG', text))
        elif args[0] == 'ERROR':
            self.debug('IRC Server Error', text, 'always')
        elif args[0] == '433':
            stderr('Nickname already in use!')
            self.hasquit = True
            self.handle_close()

        origin = Origin(self, source, args)
        self.dispatch(origin, text, args)

    def dispatch(self, origin, text, args):
        pass

    def msg(self, recipient, text):
        try:
            self.sending.acquire()

            # Cf. http://swhack.com/logs/2006-03-01#T19-43-25
            if isinstance(text, unicode):
                try:
                    text = text.encode('utf-8')
                except UnicodeEncodeError, e:
                    text = e.__class__ + ': ' + str(e)
            if isinstance(recipient, unicode):
                try:
                    recipient = recipient.encode('utf-8')
                except UnicodeEncodeError, e:
                    return

            text = str(text)

            # No messages within the last 3 seconds? Go ahead!
            # Otherwise, wait so it's been at least 0.8 seconds + penalty
            if self.stack:
                elapsed = time.time() - self.stack[-1][0]
                if elapsed < 3:
                    penalty = float(max(0, len(text) - 50)) / 70
                    wait = 0.8 + penalty
                    if elapsed < wait:
                        time.sleep(wait - elapsed)

            # Loop detection
            messages = [m[1] for m in self.stack[-8:]]
            if messages.count(text) >= 5:
                text = '...'
                if messages.count('...') >= 3:
                    return

            self.write(('PRIVMSG', recipient), text)
            self.stack.append((time.time(), text))
            self.stack = self.stack[-10:]
        finally:
            self.sending.release()

    def notice(self, dest, text):
        '''Send an IRC NOTICE to a user or a channel. See IRC protocol
        documentation for more information'''
        self.write(('NOTICE', dest), text)

    def error(self, origin, trigger):
        ''' Called internally when a module causes an error '''
        try:
            trace = traceback.format_exc()
            try:
                trace = trace.decode('utf-8')
            except:
                pass  # Can't do much about it
            stderr(trace)
            try:
                lines = list(reversed(trace.splitlines()))
                report = [lines[0].strip()]
                for line in lines:
                    line = line.strip()
                    if line.startswith('File "/'):
                        report.append(line[0].lower() + line[1:])
                        break
                else:
                    report.append('source unknown')

                signature = '%s (%s)' % (report[0], report[1])
                logfile = codecs.open(os.path.join(self.config.logdir,
                                                   'exceptions.log'),
                                      'a', encoding='utf-8')  # TODO: make not
                                                              # hardcoded
                logfile.write(u'Signature: %s\n' % signature)
                logfile.write(u'from %s at %s:\n' % (origin.sender,
                                                     str(datetime.now())))
                logfile.write(u'Message was: <%s> %s\n' % (trigger.nick,
                                                           trigger.group(0)))
                try:
                    logfile.write(trace.encode('utf-8'))
                except:
                    logfile.write(trace)
                logfile.write('----------------------------------------\n\n')
                logfile.close()
            except Exception as e:
                stderr("Could not save full traceback!")
                self.debug("core: error reporting", "(From: " + origin.sender +
                           "), can't save traceback: " + str(e), 'always')

            self.msg(origin.sender, signature)
        except Exception as e:
            self.msg(origin.sender, "Got an error.")
            self.debug("core: error reporting", "(From: " + origin.sender +
                       ") " + str(e), 'always')

    def handle_error(self):
        ''' Handle any uncaptured error in the core. Overrides asyncore's
        handle_error '''
        trace = traceback.format_exc()
        stderr(trace)
        self.debug("core", 'Fatal error in core, please review exception log',
                   'always')
        logfile = open(os.path.join(self.config.logdir,
                                    'exceptions.log'), 'a')  # TODO: make not
                                                             # hardcoded
        logfile.write('Fatal error in core, handle_error() was called')
        logfile.write('last raw line was %s' % self.raw)
        logfile.write(trace)
        logfile.write('----------------------------------------\n\n')
        logfile.close()
        if self.error_count > 10:
            if (datetime.now() - self.last_error_timestamp).seconds < 5:
                print >> sys.stderr, "Too many errors, can't continue"
                os._exit(1)
        self.last_error_timestamp = datetime.now()
        self.error_count = self.error_count + 1

    #Helper functions to maintain the oper list.
    def add_op(self, channel, name):
        self.ops[channel].add(name.lower())

    def add_halfop(self, channel, name):
        self.halfplus[channel].add(name.lower())

    def del_op(self, channel, name):
        self.ops[channel].discard(name.lower())

    def del_halfop(self, channel, name):
        self.halfplus[channel].discard(name.lower())

    def flush_ops(self, channel):
        self.ops[channel] = set()
        self.halfplus[channel] = set()

    def init_ops_list(self, channel):
        if not channel in self.halfplus:
            self.halfplus[channel] = set()
        if not channel in self.ops:
            self.ops[channel] = set()


if __name__ == "__main__":
    print __doc__
