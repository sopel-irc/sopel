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
        asyncore.loop()

    def initiate_connect(self, host, port, source_address):
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
        """Called when the socket is closed"""
        self.timeout_scheduler.stop()
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
                except UnicodeDecodeError:
                    # Discard line if encoding is unknown
                    return
        if data:
            self.bot.log_raw(data, '<<')
        self.buffer += data
        self.last_event_at = datetime.datetime.utcnow()

    def found_terminator(self):
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
    def __init__(self, bot, verify_ssl=True, ca_certs=None, **kwargs):
        AsynchatBackend.__init__(self, bot, **kwargs)
        self.verify_ssl = verify_ssl
        self.ssl = None
        self.ca_certs = ca_certs

    def handle_connect(self):
        # handle potential TLS connection
        if not self.verify_ssl:
            self.ssl = ssl.wrap_socket(self.socket,
                                       do_handshake_on_connect=True,
                                       suppress_ragged_eofs=True)
        else:
            self.ssl = ssl.wrap_socket(self.socket,
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
        """Replacement for self.send() during SSL connections."""
        try:
            result = self.socket.send(data)
            return result
        except ssl.SSLError as why:
            if why[0] in (asyncore.EWOULDBLOCK, errno.ESRCH):
                return 0
            raise why

    def recv(self, buffer_size):
        """Replacement for self.recv() during SSL connections.

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
