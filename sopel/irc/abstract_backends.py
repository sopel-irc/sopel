# coding=utf-8
# Copyright 2019, Florian Strzelecki <florian.strzelecki@gmail.com>
#
# Licensed under the Eiffel Forum License 2.
from __future__ import unicode_literals, absolute_import, print_function, division

import threading

from .utils import safe


class AbstractIRCBackend(object):
    """Abstract class defining the interface and basic logic of an IRC backend.

    :param bot: a Sopel instance
    :type bot: :class:`sopel.bot.Sopel`

    Some methods of this class **MUST** be overridden by a subclass, or the
    backend implementation will not function correctly.
    """
    def __init__(self, bot):
        self.bot = bot
        self.writing_lock = threading.RLock()

    def send_command(self, *args, **kwargs):
        """Send a command through the IRC connection.

        :param args: IRC command to send with its argument(s)
        :param str text: the text to send (optional keyword argument)

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
        raw_command = self.prepare_command(*args, text=kwargs.get('text'))
        with self.writing_lock:
            self.send(raw_command.encode('utf-8'))
        self.bot.on_message_sent(raw_command)

    def prepare_command(self, *args, **kwargs):
        """Prepare an IRC command from ``args`` and optional ``text``.

        :param list args: list of text, arguments of the IRC command to send
        :param str text: optional text to send with the IRC command
        :return: the raw message to send through the connection
        :rtype: str

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
        text = kwargs.get('text')
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

    def send_ping(self, host):
        """Send a ``PING`` command to the server.

        :param str host: IRC server host

        A ``PING`` command should be sent at a regular interval to make sure
        the server knows the IRC connection is still active.
        """
        self.send_command('PING', safe(host))

    def send_pong(self, host):
        """Send a ``PONG`` command to the server.

        :param str host: IRC server host

        A ``PONG`` command must be sent each time the server sends a ``PING``
        command to the client.
        """
        self.send_command('PONG', safe(host))

    def send_nick(self, nick):
        """Send a ``NICK`` command with a ``nick``.

        :param str nick: nickname to take
        """
        self.send_command('NICK', safe(nick))

    def send_user(self, user, mode, nick, name):
        """Send a ``USER`` command with a ``user``.

        :param str user: IRC username
        :param str mode: mode(s) to send for the user
        :param str nick: nickname associated with this user
        :param str name: "real name" for the user
        """
        self.send_command('USER', safe(user), mode, safe(nick), text=name)

    def send_pass(self, password):
        """Send a ``PASS`` command with a ``password``.

        :param str password: password for authentication
        """
        self.send_command('PASS', safe(password))

    def send_join(self, channel, password=None):
        """Send a ``JOIN`` command to ``channel`` with optional ``password``.

        :param str channel: channel to join
        :param str password: optional password for protected channels
        """
        if password is None:
            self.send_command('JOIN', safe(channel))
        else:
            self.send_command('JOIN', safe(channel), safe(password))

    def send_part(self, channel, reason=None):
        """Send a ``PART`` command to ``channel``.

        :param str channel: the channel to part
        :param str text: optional text for leaving the channel
        """
        self.send_command('PART', safe(channel), text=reason)

    def send_quit(self, reason=None):
        """Send a ``QUIT`` command.

        :param str reason: optional text for leaving the server

        This won't send anything if the backend isn't connected.
        """
        if self.connected:  # TODO: refactor for a method instead of attribute
            self.send_command('QUIT', text=reason)

    def send_kick(self, channel, nick, reason=None):
        """Send a ``KICK`` command for ``nick`` in ``channel`` .

        :param str channel: the channel from which to kick ``nick``
        :param str nick: nickname to kick from the ``channel``
        :param str reason: optional reason for the kick
        """
        self.send_command('KICK', safe(channel), safe(nick), text=reason)

    def send_privmsg(self, dest, text):
        """Send a ``PRIVMSG`` command to ``dest`` with ``text``.

        :param str dest: nickname or channel name
        :param str text: the text to send
        """
        self.send_command('PRIVMSG', safe(dest), text=text)

    def send_notice(self, dest, text):
        """Send a ``NOTICE`` command to ``dest`` with ``text``.

        :param str dest: nickname or channel name
        :param str text: the text to send
        """
        self.send_command('NOTICE', dest, text=text)
