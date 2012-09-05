#!/usr/bin/env python
# coding=utf-8
"""
irc.py - A Utility IRC Bot
Copyright 2008, Sean B. Palmer, inamidst.com
Copyright 2012, Edward Powell, http://embolalia.net
Copyright © 2012, Elad Alfassa <elad@fedoraproject.org>

Licensed under the Eiffel Forum License 2.

Willie: http://willie.dftba.net/
"""

import sys, re, time, traceback
import socket, asyncore, asynchat
import os, codecs
import traceback
try:
    import ssl, select
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
        match = Origin.source.match(source or '')
        self.nick, self.user, self.host = match.groups()

        if len(args) > 1:
            target = args[1]
        else: target = None

        mappings = {bot.nick: self.nick, None: None}
        self.sender = mappings.get(target, target)

def create_logdir():
    try: os.mkdir("logs")
    except Exception, e:
        print >> sys.stderr, 'There was a problem creating the logs directory.'
        print >> sys.stderr, e.__class__, str(e)
        print >> sys.stderr, 'Please fix this and then run Willie again.'
        os._exit(1)

def check_logdir():
    if not os.path.isdir("logs"):
        create_logdir()

def log_raw(line):
    check_logdir()
    f = codecs.open("logs/raw.log", 'a', encoding='utf-8')
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

class Bot(asynchat.async_chat):
    def __init__(self, nick, name, channels, password=None, logchan_pm=None, use_ssl = False, verify_ssl=False, ca_certs='', serverpass=None):
        asynchat.async_chat.__init__(self)
        self.set_terminator('\n')
        self.buffer = ''

        self.nick = nick
        """Willie's current nick. Changing this while Willie is running is untested."""
        self.user = nick
        self.name = name
        """Willie's "real name", as used for whois."""
        self.password = password
        """Willie's NickServ password"""

        self.verbose = True
        """True if Willie is running in verbose mode."""
        self.channels = channels or []
        """The list of channels Willie joins on startup."""
        
        self.stack = []
        self.logchan_pm = logchan_pm
        self.serverpass = serverpass
        self.verify_ssl = verify_ssl
        self.ca_certs = ca_certs
        self.use_ssl = use_ssl
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
        """A dictionary mapping channels to a list of their half-ops and ops."""
        
        #We need this to prevent error loops in handle_error
        self.error_count = 0
        self.last_error_timestamp = None

    def __write(self, args, text=None):
        try:
            self.writing_lock.acquire() #Blocking lock, can't send two things at a time
            if text is not None:
                # 510 because CR and LF count too, as nyuszika7h points out
                temp = (' '.join(args) + ' :' + text)[:510] + '\r\n'
            else:
                temp = ' '.join(args)[:510] + '\r\n'
            log_raw(temp)
            self.send(temp)
        finally:
            self.writing_lock.release()

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
        sending. Additionally, if the joined ``args`` and ``text`` are more than
        510 characters, any remaining characters will not be sent.
        """
        args = [self.safe(arg) for arg in args]
        if text is not None:
            text = self.safe(text)
        self.__write(args, text)


    def run(self, host, port=6667):
        self.initiate_connect(host, port)

    def initiate_connect(self, host, port):
        if self.verbose:
            message = 'Connecting to %s:%s...' % (host, port)
            print >> sys.stderr, message,
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        if hasattr(self.config, 'bind_host') and self.config.bind_host is not None:
            self.socket.bind((self.config.bind_host,0))
        if self.use_ssl and ssl:
            self.send = self._ssl_send
            self.recv = self._ssl_recv
        elif not has_ssl and self.use_ssl:
            print >> sys.stderr, 'SSL is not avilable on your system, attempting connection without it'
        self.connect((host, port))
        try: asyncore.loop()
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
        if self.use_ssl and has_ssl:
            if not self.verify_ssl:
                self.ssl = ssl.wrap_socket(self.socket, do_handshake_on_connect=False, suppress_ragged_eofs=True)
            else:
                verification = verify_ssl_cn(self.config.host, self.config.port)
                if verification is not None:
                    print >> sys.stderr, '\nSSL Cret information: %s' % verification[1]
                    if verification[0] == False:
                        print >> sys.stderr, "Invalid cretficate, CN mismatch!"
                        sys.exit(1)
                else:
                    print >> sys.stderr, 'WARNING! certficate information and CN validation are not avilable.'
                    print >> sys.stderr, 'Possible reasons: OpenSSL might be missing, or server throtteling connections.'
                    print >> sys.stderr, 'Trying to connect anyway:'
                self.ssl = ssl.wrap_socket(self.socket, do_handshake_on_connect=False, suppress_ragged_eofs=True, cert_reqs=ssl.CERT_REQUIRED, ca_certs=self.ca_certs)
            print >> sys.stderr, '\nSSL Handshake intiated...'
            error_count=0
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
                        print >> sys.stderr, 'SSL Handshake failed with error: %s' % err.args[1]
                        os._exit(1)
                    else:
                        error_count=error_count+1
                        if error_count > 5:
                            print >> sys.stderr, 'SSL Handshake failed (%d failed attempts)' % error_count
                            os._exit(1)
                        raise
                except Exception as e:
                    print >> sys.stderr, 'SSL Handshake failed with error: %s' % e
                    os._exit(1)
            self.set_socket(self.ssl)
        self.write(('NICK', self.nick))
        self.write(('USER', self.user, '+iw', self.nick), self.name)

        if self.serverpass is not None:
            self.write(('PASS', self.serverpass))
        print >> sys.stderr, 'Connected.'
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
        """ Replacement for self.recv() during SSL connections. From: http://www.evanfosmark.com/2010/09/ssl-support-in-asynchatasync_chat/ """
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
        print >> sys.stderr, 'Closed!'

    def collect_incoming_data(self, data):
        if data:
            log_raw(data)
            if hasattr(self, "logchan_pm") and self.logchan_pm and "PRIVMSG" in data and "#" not in data.split()[2]:
                self.msg(self.logchan_pm, data)
        self.buffer += data

    def found_terminator(self):
        line = self.buffer
        if line.endswith('\r'):
            line = line[:-1]
        self.buffer = ''

        #Adding a way to get a raw line for .whois
        self.raw = line


        # print line
        if line.startswith(':'):
            source, line = line[1:].split(' ', 1)
        else: source = None

        if ' :' in line:
            argstr, text = line.split(' :', 1)
        else: argstr, text = line, ''
        args = argstr.split()
        
        if args[0] == 'PING':
            self.write(('PONG', text))
        if args[0] == '433':
            print >>sys.stderr, 'Nickname already in use!'
            self.hasquit = True
            self.handle_close()

        origin = Origin(self, source, args)
        self.dispatch(origin, tuple([text] + args))

    def dispatch(self, origin, args):
        pass

    def msg(self, recipient, text):
        try:
            self.sending.acquire()

            # Cf. http://swhack.com/logs/2006-03-01#T19-43-25
            if isinstance(text, unicode):
                try: text = text.encode('utf-8')
                except UnicodeEncodeError, e:
                    text = e.__class__ + ': ' + str(e)
            if isinstance(recipient, unicode):
                try: recipient = recipient.encode('utf-8')
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
                    self.sending.release()
                    return

            self.write(('PRIVMSG', recipient), text)
            self.stack.append((time.time(), text))
            self.stack = self.stack[-10:]
        finally:
            self.sending.release()
            
    def notice(self, dest, text):
        '''Send an IRC NOTICE to a user or a channel. See IRC protocol documentation for more information'''
        self.write(('NOTICE', dest), text)

    def error(self, origin, trigger):
        ''' Called internally when a module causes an error '''
        try:
            trace = traceback.format_exc()
            try:
                trace = trace.decode('utf-8')
            except:
                pass # Can't do much about it
            try:
                print >> sys.stderr, trace
            except:
                raise
            try:
                logfile = codecs.open(os.path.join(self.config.logdir, 'exceptions.log'), 'a', encoding='utf-8') #todo: make not hardcoded
                logfile.write(u'from %s at %s:\n' % (origin.sender, str(datetime.now())))
                logfile.write(u'Message was: <%s> %s\n' % (trigger.nick, trigger.group(0)))
                try:
                    logfile.write(trace.encode('utf-8'))
                except:
                    logfile.write(trace)
                logfile.write('----------------------------------------\n\n')
                logfile.close()
            except Exception as e:
                print >> sys.stderr, "Could not save full traceback!"
                self.debug("core: error reporting", "(From: "+origin.sender+"), can't save traceback: "+str(e), 'always')
            lines = list(reversed(trace.splitlines()))

            report = [lines[0].strip()]
            for line in lines:
                line = line.strip()
                if line.startswith('File "/'):
                    report.append(line[0].lower() + line[1:])
                    break
            else: report.append('source unknown')

            self.msg(origin.sender, report[0] + ' (' + report[1] + ')')
        except Exception as e:
            self.msg(origin.sender, "Got an error.")
            self.debug("core: error reporting", "(From: "+origin.sender+") "+str(e), 'always')

    def handle_error(self):
        ''' Handle any uncaptured error in the core. Overrides asyncore's handle_error '''
        trace = traceback.format_exc()
        try:
            print >> sys.stderr, trace
        except:
            pass
        self.debug("core", 'Fatal error in core, please review exception log', 'always')
        logfile = open(os.path.join(self.config.logdir, 'exceptions.log'), 'a') #todo: make not hardcoded
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
        self.error_count=self.error_count+1

    #Helper functions to maintain the oper list.
    def addOp(self, channel, name):
        self.ops[channel].add(name.lower())
    def addHalfOp(self, channel, name):
        self.halfplus[channel].add(name.lower())
    def delOp(self, channel, name):
        self.ops[channel].discard(name.lower())
    def delHalfOp(self, channel, name):
        self.halfplus[channel].discard(name.lower())
    def flushOps(self, channel):
        self.ops[channel] = set()
        self.halfplus[channel] = set()
    def startOpsList(self, channel):
        if not channel in self.halfplus: self.halfplus[channel] = set()
        if not channel in self.ops: self.ops[channel] = set()

class TestBot(Bot):
    def f_ping(self, origin, match, args):
        delay = m.group(1)
        if delay is not None:
            import time
            time.sleep(int(delay))
            self.msg(origin.sender, 'pong (%s)' % delay)
        else: self.msg(origin.sender, 'pong')
    f_ping.rule = r'^\.ping(?:[ \t]+(\d+))?$'

def main():
    # bot = TestBot('testbot', ['#d8uv.com'])
    # bot.run('irc.freenode.net')
    print __doc__

if __name__=="__main__":
    main()
