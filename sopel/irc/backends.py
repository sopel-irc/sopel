# coding=utf-8
# Copyright 2019, Florian Strzelecki <florian.strzelecki@gmail.com>
#
# Licensed under the Eiffel Forum License 2.
# When working on core IRC protocol related features, consult protocol
# documentation at http://www.irchelp.org/irchelp/rfc/
from __future__ import unicode_literals, absolute_import, print_function, division

import asynchat
import asyncore
import datetime
import errno
import logging
import os
import socket
import sys
from threading import current_thread

from sopel.tools.jobs import JobScheduler, Job
from .abstract_backends import AbstractIRCBackend
from .utils import get_cnames

try:
    import ssl
    if not hasattr(ssl, 'match_hostname'):
        # Attempt to import ssl_match_hostname from python-backports
        # TODO: Remove when dropping Python 2 support
        import backports.ssl_match_hostname
        ssl.match_hostname = backports.ssl_match_hostname.match_hostname
        ssl.CertificateError = backports.ssl_match_hostname.CertificateError
    has_ssl = True
except ImportError:
    # no SSL support
    has_ssl = False

if sys.version_info.major >= 3:
    unicode = str


LOGGER = logging.getLogger(__name__)


def _send_ping(backend):
    if not backend.connected:
        return
    time_passed = (datetime.datetime.utcnow() - backend.last_event_at).seconds
    if time_passed > backend.ping_timeout:
        try:
            backend.send_ping(backend.host)
        except socket.error:
            LOGGER.exception('Socket error on PING')


def _check_timeout(backend):
    if not backend.connected:
        return
    time_passed = (datetime.datetime.utcnow() - backend.last_event_at).seconds
    if time_passed > backend.server_timeout:
        LOGGER.error(
            'Server timeout detected after %ss; closing.', time_passed)
        backend.handle_close()


_send_ping.thread = False
_check_timeout.thread = False


class AsynchatBackend(AbstractIRCBackend, asynchat.async_chat):
    """IRC backend implementation using :mod:`asynchat` (:mod:`asyncore`).

    :param bot: a Sopel instance
    :type bot: :class:`sopel.bot.Sopel`
    :param int server_timeout: connection timeout in seconds
    :param int ping_timeout: ping timeout in seconds
    """
    def __init__(self, bot, server_timeout=None, ping_timeout=None, **kwargs):
        AbstractIRCBackend.__init__(self, bot)
        asynchat.async_chat.__init__(self)
        self.set_terminator(b'\n')
        self.buffer = ''
        self.server_timeout = server_timeout or 120
        self.ping_timeout = ping_timeout or (self.server_timeout / 2)
        self.last_event_at = None
        self.host = None
        self.port = None
        self.source_address = None

        ping_job = Job(self.ping_timeout, _send_ping)
        timeout_job = Job(self.server_timeout, _check_timeout)

        self.timeout_scheduler = JobScheduler(self)
        self.timeout_scheduler.add_job(ping_job)
        self.timeout_scheduler.add_job(timeout_job)

    def run_forever(self):
        """Run forever."""
        asyncore.loop()

    def initiate_connect(self, host, port, source_address):
        """Initiate IRC connection.

        :param str host: IRC server hostname
        :param int port: IRC server port
        :param str source_address: the source address from which to initiate
                                   the connection attempt
        """
        self.host = host
        self.port = port
        self.source_address = source_address

        LOGGER.info('Connecting to %s:%s...', host, port)
        try:
            LOGGER.debug('Set socket')
            self.set_socket(socket.create_connection((host, port),
                            source_address=source_address))
            LOGGER.debug('Connection attempt')
            self.connect((host, port))
        except socket.error as e:
            LOGGER.exception('Connection error: %s', e)
            self.handle_close()

    def handle_connect(self):
        """Called when the active opener's socket actually makes a connection."""
        LOGGER.info('Connection accepted by the server...')
        self.timeout_scheduler.start()
        self.bot.on_connect()

    def handle_close(self):
        """Called when the socket is closed."""
        self.timeout_scheduler.stop()
        if current_thread() is not self.timeout_scheduler:
            self.timeout_scheduler.join(timeout=15)

        LOGGER.info('Connection closed...')
        try:
            self.bot.on_close()
        finally:
            if self.socket:
                LOGGER.debug('Closing socket')
                self.close()
                LOGGER.info('Closed!')

    def handle_error(self):
        """Called when an exception is raised and not otherwise handled."""
        LOGGER.info('Connection error...')
        self.bot.on_error()

    def collect_incoming_data(self, data):
        """Try to make sense of incoming data as Unicode.

        :param bytes data: the incoming raw bytes

        The incoming line is discarded (and thus ignored) if guessing the text
        encoding and decoding it fails.
        """
        # We can't trust clients to pass valid Unicode.
        try:
            data = unicode(data, encoding='utf-8')
        except UnicodeDecodeError:
            # not Unicode; let's try CP-1252
            try:
                data = unicode(data, encoding='cp1252')
            except UnicodeDecodeError:
                # Okay, let's try ISO 8859-1
                try:
                    data = unicode(data, encoding='iso8859-1')
                except UnicodeDecodeError:
                    # Discard line if encoding is unknown
                    return
        if data:
            self.bot.log_raw(data, '<<')
        self.buffer += data
        self.last_event_at = datetime.datetime.utcnow()

    def found_terminator(self):
        """Handle the end of an incoming message."""
        line = self.buffer
        if line.endswith('\r'):
            line = line[:-1]
        self.buffer = ''
        self.bot.on_message(line)

    def on_scheduler_error(self, scheduler, exc):
        """Called when the Job Scheduler fails."""
        LOGGER.exception('Error with the timeout scheduler: %s', exc)
        self.handle_close()

    def on_job_error(self, scheduler, job, exc):
        """Called when a job from the Job Scheduler fails."""
        LOGGER.exception('Error with the timeout scheduler: %s', exc)
        self.handle_close()


class SSLAsynchatBackend(AsynchatBackend):
    """SSL-aware extension of :class:`AsynchatBackend`.

    :param bot: a Sopel instance
    :type bot: :class:`sopel.bot.Sopel`
    :param bool verify_ssl: whether to validate the IRC server's certificate
                            (default ``True``, for good reason)
    :param str ca_certs: filesystem path to a CA Certs file containing trusted
                         root certificates
    """
    def __init__(self, bot, verify_ssl=True, ca_certs=None, **kwargs):
        AsynchatBackend.__init__(self, bot, **kwargs)
        self.verify_ssl = verify_ssl
        self.ssl = None
        self.ca_certs = ca_certs

    def handle_connect(self):
        """Handle potential TLS connection."""
        # TODO: Refactor to use SSLContext and an appropriate PROTOCOL_* constant
        # See https://lgtm.com/rules/1507225275976/
        # These warnings are ignored for now, because we can't easily fix them
        # while maintaining compatibility with py2.7 AND 3.3+, but in Sopel 8
        # the supported range should narrow sufficiently to fix these for real.
        # Each Python version still generally selects the most secure protocol
        # version(s) it supports.
        if not self.verify_ssl:
            self.ssl = ssl.wrap_socket(self.socket,  # lgtm [py/insecure-default-protocol]
                                       do_handshake_on_connect=True,
                                       suppress_ragged_eofs=True)
        else:
            self.ssl = ssl.wrap_socket(self.socket,  # lgtm [py/insecure-default-protocol]
                                       do_handshake_on_connect=True,
                                       suppress_ragged_eofs=True,
                                       cert_reqs=ssl.CERT_REQUIRED,
                                       ca_certs=self.ca_certs)
            # connect to host specified in config first
            try:
                ssl.match_hostname(self.ssl.getpeercert(), self.host)
            except ssl.CertificateError:
                # the host in config and certificate don't match
                LOGGER.error("hostname mismatch between configuration and certificate")
                # check (via exception) if a CNAME matches as a fallback
                has_matched = False
                for hostname in get_cnames(self.host):
                    try:
                        ssl.match_hostname(self.ssl.getpeercert(), hostname)
                        LOGGER.warning(
                            "using {0} instead of {1} for TLS connection"
                            .format(hostname, self.host))
                        has_matched = True
                        break
                    except ssl.CertificateError:
                        pass

                if not has_matched:
                    # everything is broken
                    LOGGER.error("Invalid certificate, no hostname matches.")
                    # TODO: refactor access to bot's settings
                    if hasattr(self.bot.settings.core, 'pid_file_path'):
                        # TODO: refactor to quit properly (no "os._exit")
                        os.unlink(self.bot.settings.core.pid_file_path)
                        os._exit(1)
        self.set_socket(self.ssl)
        LOGGER.info('Connection accepted by the server...')
        LOGGER.debug('Starting job scheduler for connection timeout...')
        self.timeout_scheduler.start()
        self.bot.on_connect()

    def send(self, data):
        """SSL-aware override for :meth:`~asyncore.dispatcher.send`."""
        try:
            result = self.socket.send(data)
            return result
        except ssl.SSLError as why:
            if why[0] in (asyncore.EWOULDBLOCK, errno.ESRCH):
                return 0
            raise why

    def recv(self, buffer_size):
        """SSL-aware override for :meth:`~asyncore.dispatcher.recv`.

        From a (now deleted) blog post by Evan "K7FOS" Fosmark:
        https://k7fos.com/2010/09/ssl-support-in-asynchatasync_chat
        """
        try:
            data = self.socket.read(buffer_size)
            if not data:
                self.handle_close()
                return b''
            return data
        except ssl.SSLError as why:
            if why[0] in (asyncore.ECONNRESET, asyncore.ENOTCONN,
                          asyncore.ESHUTDOWN):
                self.handle_close()
                return ''
            elif why[0] == errno.ENOENT:
                # Required in order to keep it non-blocking
                return b''
            else:
                raise
