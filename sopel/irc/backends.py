""":mod:`sopel.irc.backends` defines Sopel's IRC connection handlers.

.. warning::

    This is all internal code, not intended for direct use by plugins. It is
    subject to change between versions, even patch releases, without any
    advance warning.

    Please use the public APIs on :class:`bot <sopel.bot.Sopel>`.

"""
# Copyright 2019, Florian Strzelecki <florian.strzelecki@gmail.com>
#
# Licensed under the Eiffel Forum License 2.
from __future__ import annotations

import asyncio
import logging
import signal
import socket
import ssl
import threading
from typing import Any, Optional, TYPE_CHECKING

from .abstract_backends import AbstractIRCBackend


if TYPE_CHECKING:
    from sopel.irc import AbstractBot
    from sopel.trigger import PreTrigger


LOGGER = logging.getLogger(__name__)
QUIT_SIGNALS = [
    getattr(signal, name)
    for name in ['SIGUSR1', 'SIGTERM', 'SIGINT']
    if hasattr(signal, name)
]
RESTART_SIGNALS = [
    getattr(signal, name)
    for name in ['SIGUSR2', 'SIGILL']
    if hasattr(signal, name)
]


class UninitializedBackend(AbstractIRCBackend):
    """IRC Backend shim to use before the bot has started connecting.

    :param bot: an instance of a bot that uses the backend

    This exists to intercept attempts to do "illegal" things before
    connection, like sending messages to IRC before we even have a socket.
    """
    def __init__(
        self,
        bot: AbstractBot,
    ):
        super().__init__(bot)

    def is_connected(self) -> bool:
        """Check if the backend is connected to an IRC server.

        **Always returns False:** This backend type is never connected.

        Jobs (:func:`~.plugin.interval`) or other time-based triggers can be
        invoked before the bot is finished initizalizing, even before it has
        begun the IRC connection process. We need to provide a reliable way for
        those triggers to abort early if they need a connection.

        .. note::

            Your plugin code doesn't need to call this directly; unless your
            plugin does something during connection setup, it should check the
            :attr:`bot.connection_registered <.AbstractBot.connection_registered>`
            flag, which also takes into account whether the IRC connection is
            ready to accept normal commands like PRIVMSG.

        """
        return False

    def on_irc_error(self, pretrigger: PreTrigger) -> None:
        """Dummy IRC error handler.

        Since it should be impossible to receive an error from IRC when there
        is no server connection, this implementation raises an error if it is
        ever called.
        """
        raise RuntimeError("Received error from unconnected backend.")

    def irc_send(self, data: bytes) -> None:
        """Dummy method to send IRC data.

        Since it is impossible to send data to IRC without an IRC connection,
        this implementation raises an error if it is ever called.

        .. note::

            Plugins will likely never need to call this method directly, but
            many public API methods of ``bot`` call it.

            Plugin code that can be triggered by anything that isn't an IRC
            event/message should check the
            :attr:`bot.connection_registered <.AbstractBot.connection_registered>`
            flag before calling any bot method that modifies IRC state.

        """
        raise RuntimeError("Attempt to send data to unconnected backend.")

    def run_forever(self) -> None:
        """Dummy connection setup method.

        Since this implementation is a placeholder and does not actually
        connect to IRC, it raises an error if it is ever called. The bot
        should switch to an appropriate backend type before trying to
        connect; not doing so is a bug.
        """
        raise RuntimeError("Attempt to run dummy backend that cannot connect.")


class AsyncioBackend(AbstractIRCBackend):
    """IRC Backend implementation using :mod:`asyncio`.

    :param bot: an instance of a bot that uses the backend
    :param host: hostname/IP to connect to
    :param port: port to connect to
    :param source_address: optional source address as a tuple of
                           ``(host, port)``
    :param server_timeout: optional time (in seconds) before the backend reach
                           a timeout (defaults to 120s)
    :param ping_interval: optional ping interval (in seconds) between
                          last message received and sending a PING to the
                          server (defaults to ``server_timeout * 0.45``)
    :param use_ssl: if the connection must use SSL/TLS or not
    :param certfile: optional location of the certificates; used when
                     ``use_ssl`` is ``True``
    :param keyfile: optional location to the key file for certificates; used
                    when ``use_ssl`` is ``True`` and ``certfile`` is not
                    ``None``
    :param verify_ssl: if the certificates must be verified; ignored if
                       ``use_ssl`` is not ``True``
    :param ca_certs: optional location to the CA certificates; ignored if
                    ``verify_ssl`` is ``False``
    :param ssl_ciphers: the OpenSSL cipher suites to use
    :param ssl_minimum_version: the lowest SSL/TLS version to accept
    """
    def __init__(
        self,
        bot: AbstractBot,
        host: str,
        port: int,
        source_address: Optional[tuple[str, int]],
        server_timeout: Optional[int] = None,
        ping_interval: Optional[int] = None,
        use_ssl: bool = False,
        certfile: Optional[str] = None,
        keyfile: Optional[str] = None,
        verify_ssl: bool = True,
        ca_certs: Optional[str] = None,
        ssl_ciphers: Optional[list[str]] = None,
        ssl_minimum_version: ssl.TLSVersion = ssl.TLSVersion.TLSv1_2,
        **kwargs: Any,
    ):
        super().__init__(bot)
        # connection parameters
        self._host: str = host
        self._port: int = port
        self._source_address: Optional[tuple[str, int]] = source_address
        self._use_ssl: bool = use_ssl
        self._certfile: Optional[str] = certfile
        self._keyfile: Optional[str] = keyfile
        self._verify_ssl: bool = verify_ssl
        self._ca_certs: Optional[str] = ca_certs
        self._ssl_ciphers: str = ":".join(ssl_ciphers or [])
        self._ssl_minimum_version: ssl.TLSVersion = ssl_minimum_version

        # timeout configuration
        self._server_timeout: float = float(server_timeout or 120)
        self._ping_interval: float = float(
            ping_interval or (self._server_timeout * 0.45)
        )

        # connection flags
        self._connected: bool = False
        self._loop: Optional[asyncio.AbstractEventLoop] = None

        # connection writer & reader
        self._writer: Optional[asyncio.StreamWriter] = None
        self._reader: Optional[asyncio.StreamReader] = None

        # connection tasks
        self._read_task: Optional[asyncio.Task] = None
        self._ping_task: Optional[asyncio.TimerHandle] = None
        self._timeout_task: Optional[asyncio.TimerHandle] = None

    # signal handlers

    def _signal_quit(self) -> None:
        LOGGER.info('Receiving QUIT signal.')
        self.bot.quit('Quit')

    def _signal_restart(self) -> None:
        LOGGER.info('Receiving RESTART signal.')
        self.bot.restart('Restarting')

    # timeout management

    def _ping_callback(self) -> None:
        # simply send a PING
        LOGGER.debug(
            'Sending PING after %0.1fs of inactivity.', self._ping_interval)
        self.send_ping(self._host)

    def _timeout_callback(self) -> None:
        # cancel other tasks
        for task in [self._ping_task, self._read_task]:
            if task is not None:
                task.cancel()
        self._ping_task = None
        self._read_task = None
        # log a warning
        LOGGER.warning(
            'Reached timeout (%0.1fs); closing connection.',
            self._server_timeout,
        )

    def _cancel_timeout_tasks(self) -> None:
        # cancel every timeout tasks (PING & Server Timeout)
        for task in [self._ping_task, self._timeout_task]:
            if task is not None:
                task.cancel()
        self._ping_task = None
        self._timeout_task = None

    def _reset_timeout_tasks(self) -> None:
        # cancel first
        self._cancel_timeout_tasks()
        # then schedule again
        loop = asyncio.get_running_loop()
        self._ping_task = loop.call_later(
            self._ping_interval, self._ping_callback,
        )
        self._timeout_task = loop.call_later(
            self._server_timeout, self._timeout_callback,
        )

    # backend interface

    def is_connected(self) -> bool:
        return self._connected

    def on_irc_error(self, pretrigger: PreTrigger) -> None:
        LOGGER.warning('Error received from server: %s', pretrigger.text)

    def irc_send(self, data: bytes) -> None:
        if self._loop is None:
            raise RuntimeError('EventLoop not initialized.')

        if threading.current_thread() is threading.main_thread():
            self._loop.create_task(self.send(data))
        else:
            asyncio.run_coroutine_threadsafe(self.send(data), self._loop)

    # read/write

    async def send(self, data: bytes) -> None:
        """Send ``data`` through the writer."""
        if self._writer is None:
            raise RuntimeError(
                'Writer not initialized. '
                'Are you sure the backend is running?')

        try:
            self._writer.write(data)
            await self._writer.drain()
        except asyncio.CancelledError:
            LOGGER.debug('Writer was cancelled')

    async def read_forever(self) -> None:
        """Main reading loop of the backend.

        This listens to the reader for an incoming IRC line, decodes the data,
        and passes it to
        :meth:`bot.on_message(data) <sopel.irc.AbstractBot.on_message>`, until
        the reader reaches the EOF (i.e. connection closed).

        It manages connection timeouts by scheduling two tasks:

        * a PING task, that will send a PING to the server as defined by
          the ping interval (from the configuration)
        * a Timeout task, that will stop the bot if it reaches the timeout

        Whenever a message is received, both tasks are cancelled and
        rescheduled.

        When the connection is closed, the reader will reach EOF, and return
        an empty string, which in turn will end the coroutine.

        .. seealso::

            The :meth:`~.decode_line` method is used to decode the IRC line
            from :class:`bytes` to :class:`str`.

        """
        if self._reader is None:
            raise RuntimeError(
                'Reader not initialized. '
                'Are you sure the backend is running?')

        # cancel timeout tasks
        self._cancel_timeout_tasks()

        # loop forever until EOF
        while not self._reader.at_eof():
            try:
                line: bytes = await self._reader.readuntil(separator=b'\r\n')
            except asyncio.IncompleteReadError as err:
                LOGGER.warning('Receiving partial message from IRC.')
                line = err.partial
            except asyncio.LimitOverrunError:
                LOGGER.exception('Unable to read from IRC server.')
                break

            # connection is active: reset timeout tasks
            self._reset_timeout_tasks()

            # check content
            if not line:
                LOGGER.debug('No data received.')
                continue

            # decode content to unicode
            try:
                data: str = self.decode_line(line)
            except ValueError:
                LOGGER.error('Unable to decode line from IRC server: %r', line)
                continue

            # use bot's callbacks
            try:
                self.bot.log_raw(data, '<<')
                self.bot.on_message(data)
            except Exception:
                LOGGER.exception('Unexpected exception on message handling.')
                LOGGER.warning('Stopping the backend after error.')
                break

        # cancel timeout tasks when reading loop ends
        self._cancel_timeout_tasks()

    # run & connection

    def get_connection_kwargs(self) -> dict:
        """Return the keyword arguments required to initiate connection."""
        ssl_context: Optional[ssl.SSLContext] = None

        if self._use_ssl:
            ssl_context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
            ssl_context.minimum_version = self._ssl_minimum_version
            ssl_context.set_ciphers(self._ssl_ciphers)
            if self._certfile is not None:
                # load_cert_chain requires a certfile (cannot be None)
                ssl_context.load_cert_chain(
                    certfile=self._certfile,
                    keyfile=self._keyfile,
                )

            if self._verify_ssl and self._ca_certs is not None:
                ssl_context.load_verify_locations(self._ca_certs)
            elif not self._verify_ssl:
                # deactivate SSL verification for hostname & certificate
                ssl_context.check_hostname = False
                ssl_context.verify_mode = ssl.CERT_NONE

        return {
            'host': self._host,
            'port': self._port,
            'ssl': ssl_context,
            'local_addr': self._source_address,
        }

    async def _connect_to_server(
        self, **connection_kwargs: Any,
    ) -> tuple[
        Optional[asyncio.StreamReader],
        Optional[asyncio.StreamWriter],
    ]:
        reader: Optional[asyncio.StreamReader] = None
        writer: Optional[asyncio.StreamWriter] = None

        # open connection
        try:
            reader, writer = await asyncio.open_connection(
                **connection_kwargs,
            )

        # SSL Errors (certificate verification and generic SSL errors)
        except ssl.SSLCertVerificationError as err:
            LOGGER.error(
                'Unable to connect due to '
                'SSL certificate verification failure: %s',
                err,
            )
            self.log_exception()
            # tell the bot to quit without restart
            self.bot.hasquit = True
            self.bot.wantsrestart = False
        except ssl.SSLError as err:
            LOGGER.error('Unable to connect due to an SSL error: %s', err)
            self.log_exception()
            # tell the bot to quit without restart
            self.bot.hasquit = True
            self.bot.wantsrestart = False

        # Specific connection error (invalid address and timeout)
        except socket.gaierror as err:
            LOGGER.error(
                'Unable to connect due to invalid IRC server address: %s',
                err,
            )
            LOGGER.error(
                'You should verify that "%s:%s" is the correct address '
                'to connect to the IRC server.',
                connection_kwargs.get('host'),
                connection_kwargs.get('port'),
            )
            self.log_exception()
            # tell the bot to quit without restart
            self.bot.hasquit = True
            self.bot.wantsrestart = False
        except TimeoutError as err:
            LOGGER.error('Unable to connect due to a timeout: %s', err)
            self.log_exception()
            # tell the bot to quit without restart
            self.bot.hasquit = True
            self.bot.wantsrestart = False

        # Generic connection error
        except ConnectionError as err:
            LOGGER.error('Unable to connect: %s', err)
            self.log_exception()
            # tell the bot to quit without restart
            self.bot.hasquit = True
            self.bot.wantsrestart = False

        # Generic OSError (used for any unspecific connection error)
        except OSError as err:
            LOGGER.error('Unable to connect: %s', err)
            LOGGER.error(
                'You should verify that "%s:%s" is the correct address '
                'to connect to the IRC server.',
                connection_kwargs.get('host'),
                connection_kwargs.get('port'),
            )
            self.log_exception()
            # tell the bot to quit without restart
            self.bot.hasquit = True
            self.bot.wantsrestart = False

        # Unexpected error
        except Exception as err:
            LOGGER.error(
                'Unable to connect due to an unexpected error: %s',
                err,
            )
            self.log_exception()
            # until there is a way to prevent an infinite loop of connection
            # error and reconnect, we have to tell the bot to quit here
            # TODO: prevent infinite connection failure loop
            self.bot.hasquit = True
            self.bot.wantsrestart = False

        return reader, writer

    async def _run_forever(self) -> None:
        self._loop = asyncio.get_running_loop()
        connection_kwargs = self.get_connection_kwargs()

        # register signal handlers
        for quit_signal in QUIT_SIGNALS:
            self._loop.add_signal_handler(quit_signal, self._signal_quit)
        for restart_signal in RESTART_SIGNALS:
            self._loop.add_signal_handler(restart_signal, self._signal_restart)

        # connect to socket
        LOGGER.debug('Attempt connection.')
        self._reader, self._writer = await self._connect_to_server(
            **connection_kwargs
        )
        if not self._reader or not self._writer:
            LOGGER.debug('Connection attempt failed.')
            return

        # on socket connection
        LOGGER.debug('Connection registered.')
        self._connected = True
        self.bot.on_connect()

        # read forever
        LOGGER.debug('Waiting for messages...')
        self._read_task = asyncio.create_task(self.read_forever())
        try:
            await self._read_task

        # task was cancelled, i.e. another exception is responsible for that
        except asyncio.CancelledError:
            LOGGER.debug('Read task was cancelled.')

        # connection reset requires a log, but no exception log
        except ConnectionResetError as err:
            LOGGER.error('Connection reset on read: %s', err)

        # generic (connection) error requires a specific exception log
        except ConnectionError as err:
            LOGGER.error('Connection error on read: %s', err)
            self.log_exception()

        except Exception as err:
            LOGGER.error('Unexpected error on read: %s', err)
            self.log_exception()

        # task done (connection closed without error)
        else:
            LOGGER.debug('Reader received EOF.')

        # on socket disconnection
        self._connected = False

        # cancel timeout tasks
        self._cancel_timeout_tasks()

        # nothing to read anymore
        LOGGER.debug('Shutting down writer.')
        self._writer.close()
        try:
            await self._writer.wait_closed()

        # task was cancelled, i.e. another exception is responsible for that
        except asyncio.CancelledError:
            LOGGER.debug('Writer task was cancelled.')

        # connection reset happened before on the read task
        except ConnectionResetError as err:
            LOGGER.debug('Connection reset while closing: %s', err)

        # generic (connection) error requires a specific exception log
        except ConnectionError as err:
            LOGGER.error('Connection error while closing: %s', err)
            self.log_exception()

        except Exception:
            LOGGER.error('Unexpected error while shutting down socket.')
            self.log_exception()

        LOGGER.debug('All clear, exiting now.')

    def run_forever(self) -> None:
        """Run forever."""
        LOGGER.debug('Running forever.')
        asyncio.run(self._run_forever())
        LOGGER.info('Connection backend stopped.')
        self.bot.on_close()
