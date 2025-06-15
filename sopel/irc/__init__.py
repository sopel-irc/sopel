""":mod:`sopel.irc` is the core IRC module for Sopel.

This sub-package contains everything that is related to the IRC protocol
(connection, commands, abstract client, etc.) and that can be used to implement
the Sopel bot.

In particular, it defines the interface for the IRC backend
(:class:`~sopel.irc.abstract_backends.AbstractIRCBackend`), and the
interface for the bot itself (:class:`~sopel.irc.AbstractBot`).

.. warning::

    This is all internal code, not intended for direct use by plugins. It is
    subject to change between versions, even patch releases, without any
    advance warning.

    Please use the public APIs on :class:`bot <sopel.bot.Sopel>`.

.. important::

    When working on core IRC protocol related features, consult protocol
    documentation at https://modern.ircdocs.horse/

"""
# Copyright 2008, Sean B. Palmer, inamidst.com
# Copyright 2012, Elsie Powell, http://embolalia.com
# Copyright © 2012, Elad Alfassa <elad@fedoraproject.org>
# Copyright 2019, Florian Strzelecki <florian.strzelecki@gmail.com>
#
# Licensed under the Eiffel Forum License 2.
from __future__ import annotations

import abc
from collections import deque
from datetime import datetime, timezone
import logging
import os
import threading
import time
from typing import (
    Any,
    TYPE_CHECKING,
)

from sopel import tools, trigger
from sopel.lifecycle import deprecated
from sopel.tools import identifiers, memories
from .backends import AsyncioBackend, UninitializedBackend
from .capabilities import Capabilities
from .isupport import ISupport


if TYPE_CHECKING:
    from collections.abc import Iterable

    from sopel.config import Config
    from .abstract_backends import AbstractIRCBackend
    from .utils import MyInfo


__all__ = ['abstract_backends', 'backends', 'utils']

LOGGER = logging.getLogger(__name__)
ERR_BACKEND_NOT_INITIALIZED = 'Backend not initialized; is the bot running?'


class AbstractBot(abc.ABC):
    """Abstract definition of Sopel's interface."""
    def __init__(self, settings: Config):
        # private properties: access as read-only properties
        self._user: str = settings.core.user
        self._name: str = settings.core.name
        self._isupport = ISupport()
        self._capabilities = Capabilities()
        self._myinfo: MyInfo | None = None
        self._nick: identifiers.Identifier = self.make_identifier(
            settings.core.nick)

        self.backend: AbstractIRCBackend = UninitializedBackend(self)
        """IRC Connection Backend."""
        self._connection_registered = threading.Event()
        """Flag stating whether the IRC connection is registered yet."""
        self.settings = settings
        """The bot's settings.

        .. versionadded:: 7.0
        """

        # internal machinery
        self.sending = threading.RLock()
        self.last_error_timestamp: datetime | None = None
        self.error_count = 0
        self.stack: dict[identifiers.Identifier, dict[str, Any]] = {}
        self.hasquit = False
        self.wantsrestart = False
        self.last_raw_line = ''  # last raw line received

    @property
    def connection_registered(self) -> bool:
        """Whether the IRC connection is registered.

        This is a property so it can accurately reflect not only the socket
        state (connection to IRC server), but also whether the connection is
        ready to accept "normal" IRC commands.

        Before registration is completed, only a very limited set of commands
        are allowed to be used. Sopel itself takes care of these, so plugins
        will be more concerned with whether they are allowed to use methods
        like :meth:`say` yet.
        """
        return (
            self.backend is not None
            and self.backend.is_connected()
            and self._connection_registered.is_set())

    @property
    def nick(self) -> identifiers.Identifier:
        """Sopel's current nick.

        Changing this while Sopel is running is unsupported and can result in
        undefined behavior.
        """
        return self._nick

    @property
    def user(self) -> str:
        """Sopel's user/ident."""
        return self._user

    @property
    def name(self) -> str:
        """Sopel's "real name", as used for WHOIS responses."""
        return self._name

    @property
    def config(self) -> Config:
        """The :class:`sopel.config.Config` for the current Sopel instance."""
        # TODO: Deprecate config, replaced by settings
        return self.settings

    @property
    def capabilities(self) -> Capabilities:
        """Capabilities negotiated with the server.

        .. versionadded:: 8.0
        """
        return self._capabilities

    @property
    @deprecated(
        reason='Capability handling has been rewritten. '
        'Use `bot.capabilities.is_enabled()` or `bot.capabilities.enabled` instead.',
        version='8.0',
        warning_in='8.1',
        removed_in='9.0',
    )
    def enabled_capabilities(self) -> set[str]:
        """A set containing the IRCv3 capabilities that the bot has enabled.

        .. deprecated:: 8.0

            Enabled server capabilities are now managed by
            :attr:`bot.capabilities <capabilities>` and its various methods and
            attributes:

            * use :meth:`bot.capabilities.is_enabled() <sopel.irc.capabilities.Capabilities.is_enabled>`
              to check if a capability is enabled
            * use :attr:`bot.capabilities.enabled <sopel.irc.capabilities.Capabilities.enabled>`
              for a list of enabled capabilities

            Will be removed in Sopel 9.

        """
        return set(self._capabilities.enabled)

    @property
    @deprecated(
        reason='Capability handling has been rewritten. '
        'Use `bot.capabilities.is_available()` or `bot.capabilities.available` instead.',
        version='8.0',
        warning_in='8.1',
        removed_in='9.0',
    )
    def server_capabilities(self) -> dict[str, str | None]:
        """A dict mapping supported IRCv3 capabilities to their options.

        For example, if the server specifies the capability ``sasl=EXTERNAL``,
        it will be here as ``{"sasl": "EXTERNAL"}``. Capabilities specified
        without any options will have ``None`` as the value.

        For servers that do not support IRCv3, this will be an empty set.

        .. deprecated:: 8.0

            Enabled server capabilities are now managed by
            :attr:`bot.capabilities <capabilities>` and its various methods and
            attributes:

            * use :meth:`bot.capabilities.is_available() <sopel.irc.capabilities.Capabilities.is_available>`
              to check if a capability is available
            * use :attr:`bot.capabilities.available <sopel.irc.capabilities.Capabilities.available>`
              for a list of available capabilities and their parameters

            Will be removed in Sopel 9.

        """
        return self._capabilities.available

    @property
    def isupport(self) -> ISupport:
        """Features advertised by the server.

        .. versionadded:: 7.0
        """
        return self._isupport

    @property
    def myinfo(self) -> MyInfo:
        """Server/network information.

        .. versionadded:: 7.0
        """
        if self._myinfo is None:
            raise AttributeError('myinfo')
        return self._myinfo

    @property
    @abc.abstractmethod
    def hostmask(self) -> str | None:
        """The bot's hostmask."""

    # Utility

    def make_identifier(self, name: str) -> identifiers.Identifier:
        """Instantiate an Identifier using the bot's context.

        .. versionadded:: 8.0
        """
        casemapping = {
            'ascii': identifiers.ascii_lower,
            'rfc1459': identifiers.rfc1459_lower,
            'rfc1459-strict': identifiers.rfc1459_strict_lower,
        }.get(self.isupport.get('CASEMAPPING'), identifiers.rfc1459_lower)
        chantypes = (
            self.isupport.get('CHANTYPES', identifiers.DEFAULT_CHANTYPES))

        return identifiers.Identifier(
            name,
            casemapping=casemapping,
            chantypes=chantypes,
        )

    def make_identifier_memory(self) -> memories.SopelIdentifierMemory:
        """Instantiate a SopelIdentifierMemory using the bot's context.

        This is a shortcut for :class:`~.memories.SopelIdentifierMemory`\'s most
        common use case, which requires remembering to pass the ``bot``\'s own
        :meth:`make_identifier` method so the ``SopelIdentifierMemory`` will
        cast its keys to :class:`~.tools.identifiers.Identifier`\\s that are
        compatible with what the bot tracks internally and sends with
        :class:`~.trigger.Trigger`\\s when a plugin callable runs.

        Calling this method is equivalent to the following::

            from sopel.tools import memories

            memories.SopelIdentifierMemory(
                identifier_factory=bot.make_identifier,
            )

        .. versionadded:: 8.0

        .. seealso::

            The :mod:`.tools.memories` module describes how to use
            :class:`~.tools.memories.SopelIdentifierMemory` and its siblings.

        """
        return memories.SopelIdentifierMemory(
            identifier_factory=self.make_identifier,
        )

    def safe_text_length(self, recipient: str) -> int:
        """Estimate a safe text length for an IRC message.

        :return: the maximum possible length of a message to ``recipient``

        When the bot sends a message to a recipient (channel or nick), it has
        512 bytes minus the command, arguments, various separators and trailing
        CRLF for its text. However, this is not what other users will see from
        the server; the message forwarded to other clients will be sent using
        this format::

            :nick!~user@hostname PRIVMSG #channel :text

        Which takes more bytes, reducing the maximum length available for a
        single line of text. This method computes a safe length of text that
        can be sent using ``PRIVMSG`` or ``NOTICE`` by subtracting the size
        required by the server to convey the bot's message.

        .. versionadded:: 8.0

        .. seealso::

            This method is useful when sending a message using :meth:`say`,
            and can be used with :func:`sopel.tools.get_sendable_message`.

        """
        # Clients "SHOULD" assume messages will be truncated at 512 bytes if
        # the LINELEN ISUPPORT token is not present.
        # See https://modern.ircdocs.horse/#linelen-parameter
        max_line_length = self.isupport.get('LINELEN', 512)

        if self.hostmask is not None:
            hostmask_length = len(self.hostmask)
        else:
            # calculate maximum possible length, given current nick/username
            hostmask_length = (
                len(self.nick)  # own nick length
                + 1  # (! separator)
                + 1  # (for the optional ~ in user)
                + min(  # own ident length, capped to ISUPPORT or RFC maximum
                    len(self.user),
                    getattr(self.isupport, 'USERLEN', 9))
                + 1  # (@ separator)
                + 63  # <hostname> has a maximum length of 63 characters.
            )

        return (
            max_line_length
            - 1  # leading colon
            - hostmask_length  # calculated/maximum length of own hostmask prefix
            - 1  # space between prefix & command
            - 7  # PRIVMSG command
            - 1  # space before recipient
            - len(recipient.encode('utf-8'))  # target channel/nick (can contain Unicode)
            - 2  # space after recipient, colon before text
            - 2  # trailing CRLF
        )

    # Connection

    def get_irc_backend(
        self,
        host: str,
        port: int,
        source_address: tuple[str, int] | None,
    ) -> AbstractIRCBackend:
        """Set up the IRC backend based on the bot's settings.

        :return: the initialized IRC backend object
        """
        timeout = int(self.settings.core.timeout)
        ping_interval = int(self.settings.core.timeout_ping_interval)
        return AsyncioBackend(
            self,
            # connection
            host=host,
            port=port,
            source_address=source_address,
            # timeout
            server_timeout=timeout,
            ping_interval=ping_interval,
            # ssl
            use_ssl=self.settings.core.use_ssl,
            certfile=self.settings.core.client_cert_file,
            keyfile=self.settings.core.client_cert_file,
            verify_ssl=self.settings.core.verify_ssl,
            ca_certs=self.settings.core.ca_certs,
            ssl_ciphers=self.settings.core.ssl_ciphers,
            ssl_minimum_version=self.settings.core.ssl_minimum_version,
        )

    def run(self, host: str, port: int = 6667) -> None:
        """Connect to IRC server and run the bot forever.

        :param host: the IRC server hostname
        :param port: the IRC server port
        """
        source_address = ((self.settings.core.bind_host, 0)
                          if self.settings.core.bind_host else None)

        self.backend = self.get_irc_backend(host, port, source_address)
        try:
            self.backend.run_forever()
        except KeyboardInterrupt:
            # raised only when the bot is not connected
            LOGGER.warning('Keyboard Interrupt')
            raise

    def on_connect(self) -> None:
        """Handle successful establishment of IRC connection."""
        if self.backend is None:
            raise RuntimeError(ERR_BACKEND_NOT_INITIALIZED)

        LOGGER.info('Connected, initiating setup sequence')

        # Request list of server capabilities. IRCv3 servers will respond with
        # CAP * LS (which we handle in coretasks). v2 servers will respond with
        # 421 Unknown command, which we'll ignore
        LOGGER.debug('Sending CAP request')
        self.backend.send_command('CAP', 'LS', '302')

        # authenticate account if needed
        if self.settings.core.auth_method == 'server':
            LOGGER.debug('Sending server auth')
            self.backend.send_pass(self.settings.core.auth_password)
        elif self.settings.core.server_auth_method == 'server':
            LOGGER.debug('Sending server auth')
            self.backend.send_pass(self.settings.core.server_auth_password)

        LOGGER.debug('Sending nick "%s"', self.nick)
        self.backend.send_nick(self.nick)
        LOGGER.debug('Sending user "%s" (name: "%s")', self.user, self.name)
        self.backend.send_user(self.user, '0', '*', self.name)

    def on_message(self, message: str) -> None:
        """Handle an incoming IRC message.

        :param message: the received raw IRC message
        """
        if self.backend is None:
            raise RuntimeError(ERR_BACKEND_NOT_INITIALIZED)

        self.last_raw_line = message

        pretrigger = trigger.PreTrigger(
            self.nick,
            message,
            url_schemes=self.settings.core.auto_url_schemes,
            identifier_factory=self.make_identifier,
            statusmsg_prefixes=self.isupport.get('STATUSMSG'),
        )
        if all(
            not self.capabilities.is_enabled(cap)
            for cap in ['account-tag', 'extended-join']
        ):
            pretrigger.tags.pop('account', None)

        if pretrigger.event == 'PING':
            self.backend.send_pong(pretrigger.args[-1])
        elif pretrigger.event == 'ERROR':
            LOGGER.error("ERROR received from server: %s", pretrigger.args[-1])
            self.backend.on_irc_error(pretrigger)

        self.dispatch(pretrigger)

    def on_message_sent(self, raw: str) -> None:
        """Handle any message sent through the connection.

        :param raw: raw text message sent through the connection

        When a message is sent through the IRC connection, the bot will log
        the raw message. If necessary, it will also simulate the
        `echo-message`_ feature of IRCv3.

        .. _echo-message: https://ircv3.net/irc/#echo-message
        """
        # Log raw message
        self.log_raw(raw, '>>')

        # Simulate echo-message
        no_echo = not self.capabilities.is_enabled('echo-message')
        echoed = ['PRIVMSG', 'NOTICE']
        if no_echo and any(raw.upper().startswith(cmd) for cmd in echoed):
            # Use the hostmask we think the IRC server is using for us,
            # or something reasonable if that's not available
            host = 'localhost'
            if self.settings.core.bind_host:
                host = self.settings.core.bind_host
            else:
                try:
                    host = self.hostmask or host
                except KeyError:
                    pass  # we tried, and that's good enough

            pretrigger = trigger.PreTrigger(
                self.nick,
                ":{0}!{1}@{2} {3}".format(self.nick, self.user, host, raw),
                url_schemes=self.settings.core.auto_url_schemes,
                identifier_factory=self.make_identifier,
                statusmsg_prefixes=self.isupport.get('STATUSMSG'),
            )
            self.dispatch(pretrigger)

    @deprecated(
        'This method was used to log errors with asynchat; '
        'use logging.getLogger("sopel.exception") instead.',
        version='8.0',
        removed_in='9.0',
    )
    def on_error(self) -> None:
        """Handle any uncaptured error in the bot itself."""
        LOGGER.error('Fatal error in core, please review exceptions log.')

        err_log = logging.getLogger('sopel.exceptions')
        err_log.error(
            'Fatal error in core, bot.on_error() was called.\n'
            'Last Line:\n%s',
            self.last_raw_line,
        )
        err_log.exception('Fatal error traceback')
        err_log.error('----------------------------------------')

        if self.error_count > 10:
            # quit if too many errors
            dt_seconds: float = 0.0
            if self.last_error_timestamp is not None:
                dt = datetime.now(timezone.utc) - self.last_error_timestamp
                dt_seconds = dt.total_seconds()

            if dt_seconds < 5:
                LOGGER.error('Too many errors, can\'t continue')
                os._exit(1)
            # remove 1 error per full 5s that passed since last error
            self.error_count = int(max(0, self.error_count - dt_seconds // 5))

        self.last_error_timestamp = datetime.now(timezone.utc)
        self.error_count = self.error_count + 1

    def rebuild_nick(self) -> None:
        """Rebuild nick as a new identifier.

        This method exists to update the casemapping rules for the
        :class:`~sopel.tools.identifiers.Identifier` that represents the bot's
        nick, e.g. after ISUPPORT info is received.

        .. versionadded:: 8.0
        """
        self._nick = self.make_identifier(str(self._nick))

    def change_current_nick(self, new_nick: str) -> None:
        """Change the current nick without configuration modification.

        :param new_nick: new nick to be used by the bot

        .. versionadded:: 7.1
        """
        if self.backend is None:
            raise RuntimeError(ERR_BACKEND_NOT_INITIALIZED)

        self._nick = self.make_identifier(new_nick)
        LOGGER.debug('Sending nick "%s"', self.nick)
        self.backend.send_nick(self.nick)

    def on_close(self) -> None:
        """Call shutdown methods."""
        self._connection_registered.clear()
        self._shutdown()

    def _shutdown(self) -> None:
        """Handle shutdown tasks.

        Must be overridden by subclasses to do anything useful.
        """

    # Features

    @abc.abstractmethod
    def dispatch(self, pretrigger: trigger.PreTrigger) -> None:
        """Handle running the appropriate callables for an incoming message.

        :param pretrigger: Sopel PreTrigger object

        .. important::
            This method **MUST** be implemented by concrete subclasses.
        """

    def log_raw(self, line: str, prefix: str) -> None:
        """Log raw line to the raw log.

        :param line: the raw line
        :param prefix: additional information to prepend to the log line

        The ``prefix`` is usually either ``>>`` for an outgoing ``line`` or
        ``<<`` for a received one.
        """
        if not self.settings.core.log_raw:
            return
        logger = logging.getLogger('sopel.raw')
        logger.info("%s\t%r", prefix, line)

    def write(self, args: Iterable[str], text: str | None = None) -> None:
        """Send a command to the server.

        :param args: an iterable of strings, which will be joined by spaces
        :param text: a string that will be prepended with a ``:`` and added to
                     the end of the command

        ``args`` is an iterable of strings, which are joined by spaces.
        ``text`` is treated as though it were the final item in ``args``, but
        is preceded by a ``:``. This is a special case which means that
        ``text``, unlike the items in ``args``, may contain spaces (though this
        constraint is not checked by ``write``).

        In other words, both ``sopel.write(('PRIVMSG',), 'Hello, world!')``
        and ``sopel.write(('PRIVMSG', ':Hello, world!'))`` will send
        ``PRIVMSG :Hello, world!`` to the server.

        Newlines and carriage returns (``'\\n'`` and ``'\\r'``) are removed
        before sending. Additionally, if the message (after joining) is longer
        than than 510 characters, any remaining characters will not be sent.

        .. seealso::

            The connection backend is responsible for formatting and sending
            the message through the IRC connection. See the
            :meth:`sopel.irc.abstract_backends.AbstractIRCBackend.send_command`
            method for more information.

        """
        if self.backend is None:
            raise RuntimeError(ERR_BACKEND_NOT_INITIALIZED)

        self.backend.send_command(*args, text=text)

    # IRC Commands

    def action(self, text: str, dest: str) -> None:
        """Send a CTCP ACTION PRIVMSG to a user or channel.

        :param text: the text to send in the CTCP ACTION
        :param dest: the destination of the CTCP ACTION

        The same loop detection and length restrictions apply as with
        :func:`say`, though automatic message splitting is not available.
        """
        self.say('\001ACTION {}\001'.format(text), dest)

    def join(self, channel: str, password: str | None = None) -> None:
        """Join a ``channel``.

        :param channel: the channel to join
        :param password: an optional channel password

        If ``channel`` contains a space, and no ``password`` is given, the
        space is assumed to split the argument into the channel to join and its
        password. ``channel`` should not contain a space if ``password``
        is given.
        """
        if self.backend is None:
            raise RuntimeError(ERR_BACKEND_NOT_INITIALIZED)

        self.backend.send_join(channel, password=password)

    def kick(
        self,
        nick: str,
        channel: str,
        text: str | None = None,
    ) -> None:
        """Kick a ``nick`` from a ``channel``.

        :param nick: nick to kick out of the ``channel``
        :param channel: channel to kick ``nick`` from
        :param text: optional text for the kick

        The bot must be an operator in the specified channel for this to work.

        .. versionadded:: 7.0
        """
        if self.backend is None:
            raise RuntimeError(ERR_BACKEND_NOT_INITIALIZED)

        self.backend.send_kick(channel, nick, reason=text)

    def notice(self, text: str, dest: str) -> None:
        """Send an IRC NOTICE to a user or channel (``dest``).

        :param text: the text to send in the NOTICE
        :param dest: the destination of the NOTICE
        """
        if self.backend is None:
            raise RuntimeError(ERR_BACKEND_NOT_INITIALIZED)

        self.backend.send_notice(dest, text)

    def part(self, channel: str, msg: str | None = None) -> None:
        """Leave a channel.

        :param channel: the channel to leave
        :param msg: the message to display when leaving a channel
        """
        if self.backend is None:
            raise RuntimeError(ERR_BACKEND_NOT_INITIALIZED)

        self.backend.send_part(channel, reason=msg)

    def quit(self, message: str | None = None) -> None:
        """Disconnect from IRC and close the bot.

        :param message: optional QUIT message to send (e.g. "Bye!")
        """
        if self.backend is None:
            raise RuntimeError(ERR_BACKEND_NOT_INITIALIZED)

        self._connection_registered.clear()
        self.backend.send_quit(reason=message)
        self.hasquit = True
        # Wait for acknowledgment from the server. Per RFC 2812 it should be
        # an ERROR message, but many servers just close the connection.
        # Either way is fine by us. Closing the connection now would mean that
        # stuff in the buffers that has not yet been processed would never be
        # processed. It would also release the main thread, which is
        # problematic because whomever called quit might still want to do
        # something before the main thread quits.

    def restart(self, message: str | None = None) -> None:
        """Disconnect from IRC and restart the bot.

        :param message: optional QUIT message to send (e.g. "Be right back!")
        """
        self.wantsrestart = True
        self.quit(message)

    def reply(
        self,
        text: str,
        dest: str,
        reply_to: str,
        notice: bool = False,
    ) -> None:
        """Send a PRIVMSG to a user or channel, prepended with ``reply_to``.

        :param text: the text of the reply
        :param dest: the destination of the reply
        :param reply_to: the nickname that the reply will be prepended with
        :param notice: whether to send the reply as a ``NOTICE`` or not,
                       defaults to ``False``

        If ``notice`` is ``True``, send a ``NOTICE`` rather than a ``PRIVMSG``.

        The same loop detection and length restrictions apply as with
        :meth:`say`, though automatic message splitting is not available.
        """
        text = '%s: %s' % (reply_to, text)
        if notice:
            self.notice(text, dest)
        else:
            self.say(text, dest)

    def say(
        self,
        text: str,
        recipient: str,
        max_messages: int = 1,
        truncation: str = '',
        trailing: str = '',
    ) -> None:
        """Send a ``PRIVMSG`` to a user or channel.

        :param text: the text to send
        :param recipient: the message recipient
        :param max_messages: split ``text`` into at most this many messages
                             if it is too long to fit in one (optional)
        :param truncation: string to append if ``text`` is too long to fit in
                           a single message, or into the last message if
                           ``max_messages`` is greater than 1 (optional)
        :param trailing: string to append after ``text`` and (if used)
                         ``truncation`` (optional)

        By default, this will attempt to send the entire ``text`` in one
        message. If the text is too long for the server, it may be truncated.

        If ``max_messages`` is given, the ``text`` will be split into at most
        that many messages. The split is made at the last space character
        before the "safe length" (which is calculated based on the bot's
        nickname and hostmask), or exactly at the "safe length" if no such
        space character exists.

        If the ``text`` is too long to fit into the specified number of messages
        using the above splitting, the final message will contain the entire
        remainder, which may be truncated by the server. You can specify
        ``truncation`` to tell Sopel how it should indicate that the remaining
        ``text`` was cut off. Note that the ``truncation`` parameter must
        include leading whitespace if you desire any between it and the
        truncated text.

        The ``trailing`` parameter is *always* appended to ``text``, after the
        point where ``truncation`` would be inserted if necessary. It's useful
        for making sure e.g. a link is always included, even if the summary your
        plugin fetches is too long to fit.

        Here are some examples of how the ``truncation`` and ``trailing``
        parameters work, using an artificially low maximum line length::

            # bot.say() outputs <text> + <truncation?> + <trailing>
            #                   always     if needed       always

            bot.say(
                '"This is a short quote.',
                truncation=' […]',
                trailing='"')
            # Sopel says: "This is a short quote."

            bot.say(
                '"This quote is very long and will not fit on a line.',
                truncation=' […]',
                trailing='"')
            # Sopel says: "This quote is very long […]"

            bot.say(
                # note the " included at the end this time
                '"This quote is very long and will not fit on a line."',
                truncation=' […]')
            # Sopel says: "This quote is very long […]
            # The ending " goes missing

        .. versionadded:: 7.1

            The ``truncation`` and ``trailing`` parameters.

        """
        if self.backend is None:
            raise RuntimeError(ERR_BACKEND_NOT_INITIALIZED)

        excess = ''

        if not isinstance(text, str):
            # Make sure we are dealing with a Unicode string
            text = text.decode('utf-8')

        safe_length = self.safe_text_length(recipient)
        if trailing and max_messages == 1:
            # last message needs to leave room for `trailing`
            safe_length -= len(trailing.encode('utf-8'))

        # only think about `truncation` if we need to
        if safe_length < len(text.encode('utf-8')):
            if max_messages == 1:
                # last message needs to leave room for `truncation`
                # if it's still too long to fit in the line
                safe_length -= len(truncation.encode('utf-8'))
            text, excess = tools.get_sendable_message(text, safe_length)
            if max_messages == 1:
                text += truncation

        if max_messages == 1:
            # ALWAYS append `trailing` to the last message;
            # its size is included in the initial `safe_length` check
            text += trailing

        flood_max_wait = self.settings.core.flood_max_wait
        flood_burst_lines = self.settings.core.flood_burst_lines
        flood_refill_rate = self.settings.core.flood_refill_rate
        flood_empty_wait = self.settings.core.flood_empty_wait

        flood_text_length = self.settings.core.flood_text_length
        flood_penalty_ratio = self.settings.core.flood_penalty_ratio

        antiloop_threshold = min(10, self.settings.core.antiloop_threshold)
        antiloop_window = self.settings.core.antiloop_window
        antiloop_repeat_text = self.settings.core.antiloop_repeat_text
        antiloop_silent_after = self.settings.core.antiloop_silent_after

        with self.sending:
            recipient_id = self.make_identifier(recipient)
            recipient_stack = self.stack.setdefault(recipient_id, {
                'messages': deque(maxlen=10),
                'flood_left': flood_burst_lines,
            })

            if recipient_stack['messages']:
                elapsed = time.time() - recipient_stack['messages'][-1][0]
            else:
                # Default to a high enough value that we won't care.
                # Five minutes should be enough not to matter anywhere below.
                elapsed = 300

            # If flood bucket is empty, refill the appropriate number of lines
            # based on how long it's been since our last message to recipient
            if not recipient_stack['flood_left']:
                recipient_stack['flood_left'] = min(
                    flood_burst_lines,
                    int(elapsed) * flood_refill_rate)

            # If it's too soon to send another message, wait
            if not recipient_stack['flood_left']:
                penalty = 0

                if flood_penalty_ratio > 0:
                    penalty_ratio = flood_text_length * flood_penalty_ratio
                    text_length_overflow = float(
                        max(0, len(text) - flood_text_length))
                    penalty = text_length_overflow / penalty_ratio

                # Maximum wait time is 2 sec by default
                initial_wait_time = flood_empty_wait + penalty
                wait = min(initial_wait_time, flood_max_wait)
                if elapsed < wait:
                    sleep_time = wait - elapsed
                    LOGGER.debug(
                        'Flood protection wait time: %.3fs; '
                        'elapsed time: %.3fs; '
                        'initial wait time (limited to %.3fs): %.3fs '
                        '(including %.3fs of penalty).',
                        sleep_time,
                        elapsed,
                        flood_max_wait,
                        initial_wait_time,
                        penalty,
                    )
                    time.sleep(sleep_time)

            # Loop detection
            if antiloop_threshold > 0 and elapsed < antiloop_window:
                messages = [m[1] for m in recipient_stack['messages']]

                # If what we're about to send repeated at least N times
                # in the anti-looping window, replace it
                if messages.count(text) >= antiloop_threshold:
                    text = antiloop_repeat_text
                    if messages.count(text) >= antiloop_silent_after:
                        # If we've already said that N times, discard message
                        return

            self.backend.send_privmsg(recipient, text)

            # update recipient metadata
            flood_left = recipient_stack['flood_left'] - 1
            recipient_stack['flood_left'] = max(0, flood_left)
            recipient_stack['messages'].append((time.time(), text))

        # Now that we've sent the first part, we need to send the rest if
        # requested. Doing so recursively seems simpler than iteratively.
        if max_messages > 1 and excess:
            self.say(excess, recipient, max_messages - 1, truncation, trailing)
