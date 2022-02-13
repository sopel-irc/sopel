# Copyright 2019, Florian Strzelecki <florian.strzelecki@gmail.com>
#
# Licensed under the Eiffel Forum License 2.
from __future__ import annotations

import abc
from typing import Optional, TYPE_CHECKING

from .utils import safe


if TYPE_CHECKING:
    from sopel.irc import AbstractBot
    from sopel.trigger import PreTrigger


class AbstractIRCBackend(abc.ABC):
    """Abstract class defining the interface and basic logic of an IRC backend.

    :param bot: a Sopel instance
    :type bot: :class:`sopel.bot.Sopel`

    Some methods of this class **MUST** be overridden by a subclass, or the
    backend implementation will not function correctly.
    """
    def __init__(self, bot: AbstractBot):
        self.bot: AbstractBot = bot

    @abc.abstractmethod
    def is_connected(self) -> bool:
        """Tell if the backend is connected or not."""

    @abc.abstractmethod
    def on_irc_error(self, pretrigger: PreTrigger) -> None:
        """Action to perform when the server sends an error event.

        :param pretrigger: PreTrigger object with the error event

        On IRC error, if ``bot.hasquit`` is set, the backend should close the
        connection so the bot can quit or reconnect as required.
        """

    @abc.abstractmethod
    def irc_send(self, data: bytes) -> None:
        """Send an IRC line as raw ``data``.

        :param bytes data: raw line to send

        This method must be thread-safe.
        """

    @abc.abstractmethod
    def run_forever(self) -> None:
        """Run the backend forever (blocking call).

        This method is responsible for initiating the connection to the server,
        and it must call ``bot.on_connect`` once connected, or ``bot.on_close``
        if it fails to connect.

        Upon successful connection, it must run forever, listening to the
        server and allowing the bot to use :meth:`~.send_command` in a
        thread-safe way.
        """

    def decode_line(self, line: bytes) -> str:
        """Decode a raw IRC line from ``bytes`` to ``str``."""
        # We can't trust clients to pass valid Unicode.
        try:
            data = str(line, encoding='utf-8')
        except UnicodeDecodeError:
            # not Unicode; let's try CP-1252
            try:
                data = str(line, encoding='cp1252')
            except UnicodeDecodeError:
                # Okay, let's try ISO 8859-1
                try:
                    data = str(line, encoding='iso8859-1')
                except UnicodeDecodeError:
                    raise RuntimeError('Unable to decode data from server.')

        return data

    def send_command(self, *args: str, text: Optional[str] = None) -> None:
        """Send a command through the IRC connection.

        :param args: IRC command to send with its argument(s)
        :param text: the text to send (optional keyword argument)

        Example::

            # send the INFO command
            backend.send_command('INFO')
            # send the NICK command with the argument 'Sopel'
            backend.send_command('NICK', 'Sopel')
            # send the PRIVMSG command to channel #sopel with some text
            backend.send_command('PRIVMSG', '#sopel', text='Hello world!')

        .. note::

            This will call the :meth:`sopel.bot.Sopel.on_message_sent`
            callback on the bot instance with the raw message sent.
        """
        raw_command = self.prepare_command(*args, text=text)
        self.irc_send(raw_command.encode('utf-8'))
        self.bot.on_message_sent(raw_command)

    def prepare_command(self, *args: str, text: Optional[str] = None) -> str:
        """Prepare an IRC command from ``args`` and optional ``text``.

        :param args: arguments of the IRC command to send
        :param text: text to send with the IRC command (optional keyword
                     argument)
        :return: the raw message to send through the connection

        From :rfc:`2812` Internet Relay Chat: Client Protocol, Section 2.3:

            IRC messages are always lines of characters terminated with a
            CR-LF (Carriage Return - Line Feed) pair, and these messages SHALL
            NOT exceed 512 characters in length, counting all characters
            including the trailing CR-LF. Thus, there are 510 characters
            maximum allowed for the command and its parameters. There is no
            provision for continuation of message lines.

        The length in the RFC refers to the length in *bytes*, which can be
        bigger than the length of the Unicode string. This method cuts the
        message until its length fits within this limit of 510 bytes.

        The returned message contains the CR-LF pair required at the end,
        and can be sent as-is.
        """
        max_length = unicode_max_length = 510
        raw_command = ' '.join(args)
        if text is not None:
            raw_command = '{args} :{text}'.format(args=raw_command,
                                                  text=safe(text))

        # The max length of 512 is in bytes, not Unicode characters:
        # we can't split the message on bytes, or we may cut in the middle of a
        # multi-byte character.
        while len(raw_command.encode('utf-8')) > max_length:
            raw_command = raw_command[:unicode_max_length]
            unicode_max_length = unicode_max_length - 1

        # Ends the message with CR-LF
        return raw_command + '\r\n'

    def send_ping(self, host: str) -> None:
        """Send a ``PING`` command to the server.

        :param host: IRC server host

        A ``PING`` command should be sent at a regular interval to make sure
        the server knows the IRC connection is still active.
        """
        self.send_command('PING', safe(host))

    def send_pong(self, host: str) -> None:
        """Send a ``PONG`` command to the server.

        :param host: IRC server host

        A ``PONG`` command must be sent each time the server sends a ``PING``
        command to the client.
        """
        self.send_command('PONG', safe(host))

    def send_nick(self, nick: str) -> None:
        """Send a ``NICK`` command with a ``nick``.

        :param nick: nickname to take
        """
        self.send_command('NICK', safe(nick))

    def send_user(self, user: str, mode: str, nick: str, name: str) -> None:
        """Send a ``USER`` command with a ``user``.

        :param user: IRC username
        :param mode: mode(s) to send for the user
        :param nick: nickname associated with this user
        :param name: "real name" for the user
        """
        self.send_command('USER', safe(user), mode, safe(nick), text=name)

    def send_pass(self, password: str) -> None:
        """Send a ``PASS`` command with a ``password``.

        :param password: password for authentication
        """
        self.send_command('PASS', safe(password))

    def send_join(self, channel: str, password: Optional[str] = None) -> None:
        """Send a ``JOIN`` command to ``channel`` with optional ``password``.

        :param channel: channel to join
        :param password: optional password for protected channels
        """
        if password is None:
            self.send_command('JOIN', safe(channel))
        else:
            self.send_command('JOIN', safe(channel), safe(password))

    def send_part(self, channel: str, reason: Optional[str] = None) -> None:
        """Send a ``PART`` command to ``channel``.

        :param channel: the channel to part
        :param text: optional text for leaving the channel
        """
        self.send_command('PART', safe(channel), text=reason)

    def send_quit(self, reason: Optional[str] = None) -> None:
        """Send a ``QUIT`` command.

        :param reason: optional text for leaving the server

        This won't send anything if the backend isn't connected.
        """
        if self.is_connected():
            self.send_command('QUIT', text=reason)

    def send_kick(
        self,
        channel: str,
        nick: str,
        reason: Optional[str] = None,
    ) -> None:
        """Send a ``KICK`` command for ``nick`` in ``channel`` .

        :param channel: the channel from which to kick ``nick``
        :param nick: nickname to kick from the ``channel``
        :param reason: optional reason for the kick
        """
        self.send_command('KICK', safe(channel), safe(nick), text=reason)

    def send_privmsg(self, dest: str, text: str) -> None:
        """Send a ``PRIVMSG`` command to ``dest`` with ``text``.

        :param dest: nickname or channel name
        :param text: the text to send
        """
        self.send_command('PRIVMSG', safe(dest), text=text)

    def send_notice(self, dest: str, text: str) -> None:
        """Send a ``NOTICE`` command to ``dest`` with ``text``.

        :param str dest: nickname or channel name
        :param str text: the text to send
        """
        self.send_command('NOTICE', dest, text=text)
