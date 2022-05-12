# Copyright 2019, Florian Strzelecki <florian.strzelecki@gmail.com>
#
# Licensed under the Eiffel Forum License 2.
# When working on core IRC protocol related features, consult protocol
# documentation at http://www.irchelp.org/irchelp/rfc/
from __future__ import annotations

import asyncio
import logging
import signal
import ssl
import threading
from typing import Dict, Optional, Tuple, TYPE_CHECKING

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
    """
    def __init__(
        self,
        bot: AbstractBot,
        host: str,
        port: int,
        source_address: Optional[Tuple[str, int]],
        server_timeout: Optional[int] = None,
        ping_interval: Optional[int] = None,
        use_ssl: bool = False,
        certfile: Optional[str] = None,
        keyfile: Optional[str] = None,
        verify_ssl: bool = True,
        ca_certs: Optional[str] = None,
        **kwargs,
    ):
        super().__init__(bot)
        # connection parameters
        self._host: str = host
        self._port: int = port
        self._source_address: Optional[Tuple[str, int]] = source_address
        self._use_ssl: bool = use_ssl
        self._certfile: Optional[str] = certfile
        self._keyfile: Optional[str] = keyfile
        self._verify_ssl: bool = verify_ssl
        self._ca_certs: Optional[str] = ca_certs

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
            except asyncio.exceptions.IncompleteReadError as e:
                LOGGER.warning('Receiving partial message from IRC.')
                line = e.partial
            except asyncio.exceptions.LimitOverrunError:
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

    def get_connection_kwargs(self) -> Dict:
        """Return the keyword arguments required to initiate connection."""
        ssl_context: Optional[ssl.SSLContext] = None

        if self._use_ssl:
            ssl_context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
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

    async def _run_forever(self) -> None:
        self._loop = asyncio.get_running_loop()

        # register signal handlers
        for quit_signal in QUIT_SIGNALS:
            self._loop.add_signal_handler(quit_signal, self._signal_quit)
        for restart_signal in RESTART_SIGNALS:
            self._loop.add_signal_handler(restart_signal, self._signal_restart)

        # open connection
        try:
            self._reader, self._writer = await asyncio.open_connection(
                **self.get_connection_kwargs(),
            )
        except ssl.SSLError:
            LOGGER.exception('Unable to connect due to SSL error.')
            return

        self._connected = True

        LOGGER.debug('Connection registered.')
        self.bot.on_connect()

        LOGGER.debug('Waiting for messages...')
        self._read_task = asyncio.create_task(self.read_forever())
        try:
            await self._read_task
        except asyncio.CancelledError:
            LOGGER.debug('Read task was cancelled.')
        else:
            LOGGER.debug('Reader received EOF.')

        self._connected = False

        # cancel timeout tasks
        self._cancel_timeout_tasks()

        # nothing to read anymore
        LOGGER.debug('Shutting down writer.')
        self._writer.close()
        await self._writer.wait_closed()
        LOGGER.debug('All clear, exiting now.')

    def run_forever(self) -> None:
        """Run forever."""
        LOGGER.debug('Running forever.')
        asyncio.run(self._run_forever())
        LOGGER.info('Connection backend stopped.')
        self.bot.on_close()
