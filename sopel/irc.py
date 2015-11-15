# coding=utf-8
"""
irc.py - An Utility IRC Bot
Copyright 2008, Sean B. Palmer, inamidst.com
Copyright 2012, Edward Powell, http://embolalia.net
Copyright © 2012, Elad Alfassa <elad@fedoraproject.org>

Licensed under the Eiffel Forum License 2.

Sopel: http://sopel.chat/

When working on core IRC protocol related features, consult protocol
documentation at http://www.irchelp.org/irchelp/rfc/
"""
from __future__ import unicode_literals, absolute_import, print_function, division

import sys
import re
import time
import socket
import asyncore
import asynchat
import os
import codecs
import traceback
from sopel.logger import get_logger
from sopel.tools import stderr, Identifier
from sopel.trigger import PreTrigger, Trigger
try:
    import select
    import ssl
    if not hasattr(ssl, 'match_hostname'):
        # Attempt to import ssl_match_hostname from python-backports
        import backports.ssl_match_hostname
        ssl.match_hostname = backports.ssl_match_hostname.match_hostname
        ssl.CertificateError = backports.ssl_match_hostname.CertificateError
    has_ssl = True
except ImportError:
    # no SSL support
    has_ssl = False

import errno
import threading
from datetime import datetime
if sys.version_info.major >= 3:
    unicode = str

LOGGER = get_logger(__name__)


class Bot(asynchat.async_chat):
    def __init__(self, config):
        ca_certs = config.core.ca_certs

        asynchat.async_chat.__init__(self)
        self.set_terminator(b'\n')
        self.buffer = ''

        self.nick = Identifier(config.core.nick)
        """Sopel's current ``Identifier``. Changing this while Sopel is running is
        untested."""
        self.user = config.core.user
        """Sopel's user/ident."""
        self.name = config.core.name
        """Sopel's "real name", as used for whois."""

        self.channels = []
        """The list of channels Sopel is currently in."""

        self.stack = {}
        self.ca_certs = ca_certs
        self.hasquit = False

        self.sending = threading.RLock()
        self.writing_lock = threading.Lock()
        self.raw = None

        # Right now, only accounting for two op levels.
        # This might be expanded later.
        # These lists are filled in startup.py, as of right now.
        self.ops = dict()
        """
        A dictionary mapping channels to a ``Identifier`` list of their operators.
        """
        self.halfplus = dict()
        """
        A dictionary mapping channels to a ``Identifier`` list of their half-ops and
        ops.
        """
        self.voices = dict()
        """
        A dictionary mapping channels to a ``Identifier`` list of their voices,
        half-ops and ops.
        """

        # We need this to prevent error loops in handle_error
        self.error_count = 0

        self.connection_registered = False
        """ Set to True when a server has accepted the client connection and
        messages can be sent and received. """

        # Work around bot.connecting missing in Python older than 2.7.4
        if not hasattr(self, "connecting"):
            self.connecting = False

    def log_raw(self, line, prefix):
        """Log raw line to the raw log."""
        if not self.config.core.log_raw:
            return
        if not os.path.isdir(self.config.core.logdir):
            try:
                os.mkdir(self.config.core.logdir)
            except Exception as e:
                stderr('There was a problem creating the logs directory.')
                stderr('%s %s' % (str(e.__class__), str(e)))
                stderr('Please fix this and then run Sopel again.')
                os._exit(1)
        f = codecs.open(os.path.join(self.config.core.logdir, 'raw.log'),
                        'a', encoding='utf-8')
        f.write(prefix + unicode(time.time()) + "\t")
        temp = line.replace('\n', '')

        f.write(temp)
        f.write("\n")
        f.close()

    def safe(self, string):
        """Remove newlines from a string."""
        if sys.version_info.major >= 3 and isinstance(string, bytes):
                string = string.decode('utf8')
        elif sys.version_info.major < 3:
            if not isinstance(string, unicode):
                string = unicode(string, encoding='utf8')
        string = string.replace('\n', '')
        string = string.replace('\r', '')
        return string

    def write(self, args, text=None):
        """Send a command to the server.

        ``args`` is an iterable of strings, which are joined by spaces.
        ``text`` is treated as though it were the final item in ``args``, but
        is preceeded by a ``:``. This is a special case which  means that
        ``text``, unlike the items in ``args`` may contain spaces (though this
        constraint is not checked by ``write``).

        In other words, both ``sopel.write(('PRIVMSG',), 'Hello, world!')``
        and ``sopel.write(('PRIVMSG', ':Hello, world!'))`` will send
        ``PRIVMSG :Hello, world!`` to the server.

        Newlines and carriage returns ('\\n' and '\\r') are removed before
        sending. Additionally, if the message (after joining) is longer than
        than 510 characters, any remaining characters will not be sent.

        """
        args = [self.safe(arg) for arg in args]
        if text is not None:
            text = self.safe(text)
        try:
            self.writing_lock.acquire()  # Blocking lock, can't send two things
                                         # at a time

            # From RFC2812 Internet Relay Chat: Client Protocol
            # Section 2.3
            #
            # https://tools.ietf.org/html/rfc2812.html
            #
            # IRC messages are always lines of characters terminated with a
            # CR-LF (Carriage Return - Line Feed) pair, and these messages SHALL
            # NOT exceed 512 characters in length, counting all characters
            # including the trailing CR-LF. Thus, there are 510 characters
            # maximum allowed for the command and its parameters.  There is no
            # provision for continuation of message lines.

            if text is not None:
                temp = (' '.join(args) + ' :' + text)[:510] + '\r\n'
            else:
                temp = ' '.join(args)[:510] + '\r\n'
            self.log_raw(temp, '>>')
            self.send(temp.encode('utf-8'))
        finally:
            self.writing_lock.release()

    def run(self, host, port=6667):
        try:
            self.initiate_connect(host, port)
        except socket.error as e:
            stderr('Connection error: %s' % e)
            self.hasquit = True

    def initiate_connect(self, host, port):
        stderr('Connecting to %s:%s...' % (host, port))
        source_address = ((self.config.core.bind_host, 0)
                          if self.config.core.bind_host else None)
        self.set_socket(socket.create_connection((host, port),
                        source_address=source_address))
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
            print('KeyboardInterrupt')
            self.quit('KeyboardInterrupt')

    def quit(self, message):
        """Disconnect from IRC and close the bot."""
        self.write(['QUIT'], message)
        self.hasquit = True
        # Wait for acknowledgement from the server. By RFC 2812 it should be
        # an ERROR msg, but many servers just close the connection. Either way
        # is fine by us.
        # Closing the connection now would mean that stuff in the buffers that
        # has not yet been processed would never be processed. It would also
        # release the main thread, which is problematic because whomever called
        # quit might still want to do something before main thread quits.

    def handle_close(self):
        self.connection_registered = False

        self._shutdown()
        stderr('Closed!')

        # This will eventually call asyncore dispatchers close method, which
        # will release the main thread. This should be called last to avoid
        # race conditions.
        self.close()

    def part(self, channel, msg=None):
        """Part a channel."""
        self.write(['PART', channel], msg)

    def join(self, channel, password=None):
        """Join a channel

        If `channel` contains a space, and no `password` is given, the space is
        assumed to split the argument into the channel to join and its
        password.  `channel` should not contain a space if `password` is given.

        """
        if password is None:
            self.write(('JOIN', channel))
        else:
            self.write(['JOIN', channel, password])

    def handle_connect(self):
        if self.config.core.use_ssl and has_ssl:
            if not self.config.core.verify_ssl:
                self.ssl = ssl.wrap_socket(self.socket,
                                           do_handshake_on_connect=True,
                                           suppress_ragged_eofs=True)
            else:
                self.ssl = ssl.wrap_socket(self.socket,
                                           do_handshake_on_connect=True,
                                           suppress_ragged_eofs=True,
                                           cert_reqs=ssl.CERT_REQUIRED,
                                           ca_certs=self.ca_certs)
                try:
                    ssl.match_hostname(self.ssl.getpeercert(), self.config.core.host)
                except ssl.CertificateError:
                    stderr("Invalid certficate, hostname mismatch!")
                    os.unlink(self.config.core.pid_file_path)
                    os._exit(1)
            self.set_socket(self.ssl)

        # Request list of server capabilities. IRCv3 servers will respond with
        # CAP * LS (which we handle in coretasks). v2 servers will respond with
        # 421 Unknown command, which we'll ignore
        self.write(('CAP', 'LS', '302'))

        if self.config.core.auth_method == 'server':
            password = self.config.core.auth_password
            self.write(('PASS', password))
        self.write(('NICK', self.nick))
        self.write(('USER', self.user, '+iw', self.nick), self.name)

        stderr('Connected.')
        self.last_ping_time = datetime.now()
        timeout_check_thread = threading.Thread(target=self._timeout_check)
        timeout_check_thread.start()
        ping_thread = threading.Thread(target=self._send_ping)
        ping_thread.start()

    def _timeout_check(self):
        while self.connected or self.connecting:
            if (datetime.now() - self.last_ping_time).seconds > int(self.config.core.timeout):
                stderr('Ping timeout reached after %s seconds, closing connection' % self.config.core.timeout)
                self.handle_close()
                break
            else:
                time.sleep(int(self.config.core.timeout))

    def _send_ping(self):
        while self.connected or self.connecting:
            if self.connected and (datetime.now() - self.last_ping_time).seconds > int(self.config.core.timeout) / 2:
                try:
                    self.write(('PING', self.config.core.host))
                except socket.error:
                    pass
            time.sleep(int(self.config.core.timeout) / 2)

    def _ssl_send(self, data):
        """Replacement for self.send() during SSL connections."""
        try:
            result = self.socket.send(data)
            return result
        except ssl.SSLError as why:
            if why[0] in (asyncore.EWOULDBLOCK, errno.ESRCH):
                return 0
            else:
                raise why
            return 0

    def _ssl_recv(self, buffer_size):
        """Replacement for self.recv() during SSL connections.

        From: http://evanfosmark.com/2010/09/ssl-support-in-asynchatasync_chat

        """
        try:
            data = self.socket.read(buffer_size)
            if not data:
                self.handle_close()
                return ''
            return data
        except ssl.SSLError as why:
            if why[0] in (asyncore.ECONNRESET, asyncore.ENOTCONN,
                          asyncore.ESHUTDOWN):
                self.handle_close()
                return ''
            elif why[0] == errno.ENOENT:
                # Required in order to keep it non-blocking
                return ''
            else:
                raise

    def collect_incoming_data(self, data):
        # We can't trust clients to pass valid unicode.
        try:
            data = unicode(data, encoding='utf-8')
        except UnicodeDecodeError:
            # not unicode, let's try cp1252
            try:
                data = unicode(data, encoding='cp1252')
            except UnicodeDecodeError:
                # Okay, let's try ISO8859-1
                try:
                    data = unicode(data, encoding='iso8859-1')
                except:
                    # Discard line if encoding is unknown
                    return

        if data:
            self.log_raw(data, '<<')
        self.buffer += data

    def found_terminator(self):
        line = self.buffer
        if line.endswith('\r'):
            line = line[:-1]
        self.buffer = ''
        self.last_ping_time = datetime.now()
        pretrigger = PreTrigger(self.nick, line)

        if pretrigger.event == 'PING':
            self.write(('PONG', pretrigger.args[-1]))
        elif pretrigger.event == 'ERROR':
            LOGGER.error("ERROR recieved from server: %s", pretrigger.args[-1])
            if self.hasquit:
                self.close_when_done()
        elif pretrigger.event == '433':
            stderr('Nickname already in use!')
            self.handle_close()

        self.dispatch(pretrigger)

    def dispatch(self, pretrigger):
        pass

    def msg(self, recipient, text, max_messages=1):
        # Deprecated, but way too much of a pain to remove.
        self.say(text, recipient, max_messages)

    def say(self, text, recipient, max_messages=1):
        # We're arbitrarily saying that the max is 400 bytes of text when
        # messages will be split. Otherwise, we'd have to acocunt for the bot's
        # hostmask, which is hard.
        max_text_length = 400
        # Encode to bytes, for propper length calculation
        if isinstance(text, unicode):
            encoded_text = text.encode('utf-8')
        else:
            encoded_text = text
        excess = ''
        if max_messages > 1 and len(encoded_text) > max_text_length:
            last_space = encoded_text.rfind(' '.encode('utf-8'), 0, max_text_length)
            if last_space == -1:
                excess = encoded_text[max_text_length:]
                encoded_text = encoded_text[:max_text_length]
            else:
                excess = encoded_text[last_space + 1:]
                encoded_text = encoded_text[:last_space]
        # We'll then send the excess at the end
        # Back to unicode again, so we don't screw things up later.
        text = encoded_text.decode('utf-8')
        try:
            self.sending.acquire()

            # No messages within the last 3 seconds? Go ahead!
            # Otherwise, wait so it's been at least 0.8 seconds + penalty

            recipient_id = Identifier(recipient)

            if recipient_id not in self.stack:
                self.stack[recipient_id] = []
            elif self.stack[recipient_id]:
                elapsed = time.time() - self.stack[recipient_id][-1][0]
                if elapsed < 3:
                    penalty = float(max(0, len(text) - 50)) / 70
                    wait = 0.7 + penalty
                    if elapsed < wait:
                        time.sleep(wait - elapsed)

                # Loop detection
                messages = [m[1] for m in self.stack[recipient_id][-8:]]

                # If what we about to send repeated at least 5 times in the
                # last 2 minutes, replace with '...'
                if messages.count(text) >= 5 and elapsed < 120:
                    text = '...'
                    if messages.count('...') >= 3:
                        # If we said '...' 3 times, discard message
                        return

            self.write(('PRIVMSG', recipient), text)
            self.stack[recipient_id].append((time.time(), self.safe(text)))
            self.stack[recipient_id] = self.stack[recipient_id][-10:]
        finally:
            self.sending.release()
        # Now that we've sent the first part, we need to send the rest. Doing
        # this recursively seems easier to me than iteratively
        if excess:
            self.msg(recipient, excess, max_messages - 1)

    def notice(self, text, dest):
        """Send an IRC NOTICE to a user or a channel.

        See IRC protocol documentation for more information.

        """
        self.write(('NOTICE', dest), text)

    def action(self, text, dest):
        self.say('\001ACTION {}\001'.format(text), dest)

    def reply(self, text, dest, reply_to, notice=False):
        text = '%s: %s' % (reply_to, text)
        if notice:
            self.notice(text, dest)
        else:
            self.say(text, dest)

    def error(self, trigger=None):
        """Called internally when a module causes an error."""
        try:
            trace = traceback.format_exc()
            if sys.version_info.major < 3:
                trace = trace.decode('utf-8', errors='xmlcharrefreplace')
            stderr(trace)
            try:
                lines = list(reversed(trace.splitlines()))
                report = [lines[0].strip()]
                for line in lines:
                    line = line.strip()
                    if line.startswith('File "'):
                        report.append(line[0].lower() + line[1:])
                        break
                else:
                    report.append('source unknown')

                signature = '%s (%s)' % (report[0], report[1])
                # TODO: make not hardcoded
                log_filename = os.path.join(self.config.core.logdir, 'exceptions.log')
                with codecs.open(log_filename, 'a', encoding='utf-8') as logfile:
                    logfile.write('Signature: %s\n' % signature)
                    if trigger:
                        logfile.write('from {} at {}. Message was: {}\n'.format(
                            trigger.nick, str(datetime.now()), trigger.group(0)))
                    logfile.write(trace)
                    logfile.write(
                        '----------------------------------------\n\n'
                    )
            except Exception as e:
                stderr("Could not save full traceback!")
                LOGGER.error("Could not save traceback from %s to file: %s", trigger.sender, str(e))

            if trigger:
                self.msg(trigger.sender, signature)
        except Exception as e:
            if trigger:
                self.msg(trigger.sender, "Got an error.")
                LOGGER.error("Exception from %s: %s", trigger.sender, str(e))

    def handle_error(self):
        """Handle any uncaptured error in the core.

        Overrides asyncore's handle_error.

        """
        trace = traceback.format_exc()
        stderr(trace)
        LOGGER.error('Fatal error in core, please review exception log')
        # TODO: make not hardcoded
        logfile = codecs.open(
            os.path.join(self.config.core.logdir, 'exceptions.log'),
            'a',
            encoding='utf-8'
        )
        logfile.write('Fatal error in core, handle_error() was called\n')
        logfile.write('last raw line was %s' % self.raw)
        logfile.write(trace)
        logfile.write('Buffer:\n')
        logfile.write(self.buffer)
        logfile.write('----------------------------------------\n\n')
        logfile.close()
        if self.error_count > 10:
            if (datetime.now() - self.last_error_timestamp).seconds < 5:
                print >> sys.stderr, "Too many errors, can't continue"
                os._exit(1)
        self.last_error_timestamp = datetime.now()
        self.error_count = self.error_count + 1

