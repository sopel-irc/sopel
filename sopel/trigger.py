"""Triggers are how Sopel tells callables about their runtime context.

A :class:`~.trigger.Trigger` is the main type of user input plugins will see.

Sopel uses :class:`~.trigger.PreTrigger`\\s internally while processing
incoming IRC messages. Plugin authors can reasonably expect that their code
will never receive one. They are documented here for completeness, and for the
aid of Sopel's core development.
"""
from __future__ import annotations

from datetime import datetime, timezone
import re
from typing import (
    cast,
    Match,
    Sequence,
    TYPE_CHECKING,
)

from sopel import formatting, tools
from sopel.tools import web
from sopel.tools.identifiers import Identifier, IdentifierFactory


if TYPE_CHECKING:
    from sopel import config


__all__ = [
    'PreTrigger',
    'Trigger',
]

COMMANDS_WITH_CONTEXT = frozenset({
    'INVITE',
    'JOIN',
    'KICK',
    'MODE',
    'NOTICE',
    'PART',
    'PRIVMSG',
    'TOPIC',
})
"""Set of commands with a :attr:`trigger.sender<Trigger.sender>`.

Most IRC messages a plugin will want to handle (channel messages and PMs) are
associated with a context, exposed in the Trigger's ``sender`` property.
However, not *all* commands can be directly associated to a channel or nick.

For IRC message types other than those listed here, the ``trigger``\'s
``sender`` property will be ``None``.
"""


class PreTrigger:
    """A parsed raw message from the server.

    :param str own_nick: the bot's own IRC nickname
    :param str line: the full line from the server
    :param tuple url_schemes: allowed schemes for URL detection

    At the :class:`PreTrigger` stage, the line has not been matched against any
    rules yet. This is what Sopel uses to perform matching.

    ``own_nick`` is needed to correctly parse who sent the line (Sopel or
    someone else).

    ``line`` can also be a simulated echo-message, useful if the connected
    server does not support the capability.

    .. py:attribute:: args

        The IRC command's arguments.

        These are split on spaces, per the IRC protocol.

    .. py:attribute:: ctcp

        The CTCP command name, if present (``None`` otherwise)

    .. py:attribute:: event

        The IRC command name or numeric value.

        See :class:`sopel.tools.events` for a built-in mapping of names to
        numeric values.

    .. py:attribute:: host

        The sender's hostname.

    .. py:attribute:: hostmask

        The sender's hostmask, as sent by the IRC server.

    .. py:attribute:: line

        The raw line received from the server.

    .. py:attribute:: nick

        The nickname that sent this command.

    .. py:attribute:: sender

        Channel name or query where this message was received.

        .. warning::

            The ``sender`` Will be ``None`` for commands that have no implicit
            channel or private-message context, for example AWAY or QUIT.

            The :attr:`COMMANDS_WITH_CONTEXT` attribute lists IRC commands for
            which ``sender`` can be relied upon.

    .. py:attribute:: tags

        Any IRCv3 message tags attached to the line, as a :class:`dict`.

    .. py:attribute:: text

        The last argument of the IRC command.

        If the line contains ``:``, :attr:`text` will be the text following it.

        For lines that do *not* contain ``:``, :attr:`text` will be the last
        argument in :attr:`args` instead.

    .. py:attribute:: urls
        :type: tuple

        List of URLs found in the :attr:`text`.

        This is for ``PRIVMSG`` and ``NOTICE`` messages only. For other
        messages, this will be an empty ``tuple``.

    .. py:attribute:: plain

        The last argument of the IRC command with control codes stripped.

    .. py:attribute:: time

        The time when the message was received.

        If the IRC server sent a message tag indicating when *it* received the
        message, that is used instead of the time when Sopel received it.

        .. versionchanged:: 8.0
            Now a timezone-aware ``datetime`` object.

    .. py:attribute:: user

        The sender's local username.

    """
    component_regex = re.compile(r'([^!]*)!?([^@]*)@?(.*)')
    ctcp_regex = re.compile('\x01(\\S+) ?(.*)\x01')

    def __init__(
        self,
        own_nick: Identifier,
        line: str,
        url_schemes: Sequence | None = None,
        identifier_factory: IdentifierFactory = Identifier,
        statusmsg_prefixes: tuple[str, ...] = tuple(),
    ):
        self.make_identifier: IdentifierFactory = identifier_factory
        line = line.strip('\r\n')
        self.line: str = line
        self.urls: tuple[str, ...] = tuple()
        self.plain: str = ''
        self.ctcp: str | None = None

        # Break off IRCv3 message tags, if present
        self.tags: dict[str, str | None] = {}
        if line.startswith('@'):
            tagstring, line = line.split(' ', 1)
            for raw_tag in tagstring[1:].split(';'):
                tag = raw_tag.split('=', 1)
                if len(tag) > 1:
                    self.tags[tag[0]] = tag[1]
                else:
                    self.tags[tag[0]] = None

        # Client time or server time
        self.time = datetime.now(timezone.utc)
        if 'time' in self.tags:
            # ensure "time" is a string (typecheck)
            tag_time = self.tags['time'] or ''
            try:
                self.time = datetime.strptime(
                    tag_time,
                    "%Y-%m-%dT%H:%M:%S.%fZ",
                ).replace(tzinfo=timezone.utc)
            except ValueError:
                pass  # Server isn't conforming to spec, ignore the server-time

        # Grabs hostmask from line.
        # Example: line = ':Sopel!foo@bar PRIVMSG #sopel :foobar!'
        #          print(hostmask)  # Sopel!foo@bar
        # All lines start with ":" except PING.
        self.hostmask: str | None
        if line.startswith(':'):
            self.hostmask, line = line[1:].split(' ', 1)
        else:
            self.hostmask = None

        # Parses the line into a list of arguments.
        # Some events like MODE don't have a secondary string argument, i.e. no ' :' inside the line.
        # Example 1:  line = ':nick!ident@domain PRIVMSG #sopel :foo bar!'
        #             print(text)    # 'foo bar!'
        #             print(argstr)  # ':nick!ident@domain PRIVMSG #sopel'
        #             print(args)    # [':nick!ident@domain', 'PRIVMSG', '#sopel', 'foo bar!']
        # Example 2:  line = 'irc.libera.chat MODE Sopel +i'
        #             print(text)    # '+i'
        #             print(args)    # ['irc.libera.chat', 'MODE', 'Sopel', '+i']
        if ' :' in line:
            argstr, self.text = line.split(' :', 1)
            self.args = argstr.split(' ')
            self.args.append(self.text)
        else:
            self.args = line.split(' ')
            # see `text` attr documentation above, and #2360
            self.text = self.args[-1] if len(self.args) > 1 else ''

        self.event = self.args[0]
        self.args = self.args[1:]

        # The regex will always match any string, even an empty one
        components_match = cast(
            'Match', PreTrigger.component_regex.match(self.hostmask or ''))
        nick, self.user, self.host = components_match.groups()
        self.nick: Identifier = self.make_identifier(nick)

        # If we have arguments, the first one is *usually* the sender,
        # most numerics and certain general events (e.g. QUIT) excepted
        target: Identifier | None = None
        status_prefix: str | None = None

        if self.args and self.event in COMMANDS_WITH_CONTEXT:
            raw_target = self.args[0]
            if statusmsg_prefixes and raw_target[0] in statusmsg_prefixes:
                status_prefix, raw_target = raw_target[0], raw_target[1:]
            target = self.make_identifier(raw_target)

            # Unless we're messaging the bot directly, in which case that
            # second arg will be our bot's name.
            if target.lower() == own_nick.lower():
                target = self.nick

        self.sender = target
        self.status_prefix = status_prefix

        # Parse CTCP
        if self.event == 'PRIVMSG' or self.event == 'NOTICE':
            ctcp_match = PreTrigger.ctcp_regex.match(self.args[-1])
            if ctcp_match is not None:
                ctcp, message = ctcp_match.groups()
                self.ctcp = ctcp
                self.args[-1] = message or ''

            # Search URLs after CTCP parsing
            self.urls = tuple(
                web.search_urls(self.args[-1], schemes=url_schemes))

        # Populate account from extended-join messages
        if self.event == 'JOIN' and len(self.args) == 3:
            # Account is the second arg `...JOIN #Sopel account :realname`
            self.tags['account'] = self.args[1]

        # get plain text message
        if self.args:
            self.plain = formatting.plain(self.args[-1])


class Trigger(str):
    """A line from the server, which has matched a callable's rules.

    :param config: Sopel's current configuration settings object
    :type config: :class:`~sopel.config.Config`
    :param message: the message that matched the callable
    :type message: :class:`PreTrigger`
    :param match: what *in* the message matched
    :type match: :ref:`Match object <match-objects>`
    :param str account: services account name of the ``message``'s sender
                        (optional; only applies on networks with the
                        ``account-tag`` capability enabled)

    A :class:`Trigger` object itself can be used as a string; when used in
    this way, it represents the matching line's full text.

    The ``match`` is based on the matching regular expression rule; Sopel's
    command decorators auto-generate rules containing specific numbered groups
    that are documented separately. (See :attr:`group` below.)

    Note that CTCP messages (``PRIVMSG``\\es and ``NOTICE``\\es which start
    and end with ``'\\x01'``) will have the ``'\\x01'`` bytes stripped, and
    :attr:`trigger.ctcp <ctcp>` will contain the command (e.g. ``ACTION``).

    .. note::

        CTCP used to be stored as the ``intent`` tag. Since message intents
        never made it past the IRCv3 draft stage, Sopel dropped support for
        them in Sopel 8.

    """
    sender = property(lambda self: self._pretrigger.sender)
    """Where the message arrived from.

    :type: :class:`~sopel.tools.identifiers.Identifier`

    This will be a channel name for "regular" (channel) messages, or the nick
    that sent a private message.

    You can check if the trigger comes from a channel or a nick with its
    :meth:`~sopel.tools.identifiers.Identifier.is_nick` method::

        if trigger.sender.is_nick():
            # message sent from a private message
        else:
            # message sent from a channel

    .. important::

        If the message was sent to a `specific status prefix`__, the ``sender``
        does not include the status prefix. Be sure to use the
        :attr:`status_prefix` when replying.

        Note that the ``bot`` argument passed to plugin callables is a
        :class:`~sopel.bot.SopelWrapper` that handles this for the default
        ``destination`` of the methods it overrides (most importantly,
        :meth:`~sopel.bot.SopelWrapper.say` &
        :meth:`~sopel.bot.SopelWrapper.reply`).

    .. warning::

        The ``sender`` Will be ``None`` for commands that have no implicit
        channel or private-message context, for example AWAY or QUIT.

        The :attr:`COMMANDS_WITH_CONTEXT` attribute lists IRC commands for
        which ``sender`` can be relied upon.

    .. __: https://modern.ircdocs.horse/#statusmsg-parameter
    """
    status_prefix = property(lambda self: self._pretrigger.status_prefix)
    """The prefix used for the :attr:`sender` for status-specific messages.

    :type: str | None

    This will be ``None`` by default. If a message is sent to a channel, it may
    have a status prefix for status-specific messages. In that case, the prefix
    is removed from the channel's identifier (see :attr:`sender`) and saved to
    this attribute.
    """
    time = property(lambda self: self._pretrigger.time)
    """When the message was received.

    :type: naïve :class:`~datetime.datetime` object (no timezone)

    If the IRC server supports ``server-time``, :attr:`time` will give that
    value. Otherwise, :attr:`time` will use the time when the message was
    received by Sopel. In both cases, this time is in UTC.
    """
    raw = property(lambda self: self._pretrigger.line)
    """The entire raw IRC message, as sent from the server.

    :type: str

    This includes the CTCP ``\\x01`` bytes and command, if they were included.
    """
    is_privmsg = property(lambda self: self._is_privmsg)
    """Whether the message was triggered in a private message.

    :type: bool

    ``True`` if the trigger was received in a private message; ``False`` if it
    came from a channel.
    """
    hostmask = property(lambda self: self._pretrigger.hostmask)
    """Hostmask of the person who sent the message as ``<nick>!<user>@<host>``.

    :type: str
    """
    user = property(lambda self: self._pretrigger.user)
    """Local username of the person who sent the message.

    :type: str
    """
    nick = property(lambda self: self._pretrigger.nick)
    """The nickname who sent the message.

    :type: :class:`~sopel.tools.identifiers.Identifier`
    """
    host = property(lambda self: self._pretrigger.host)
    """The hostname of the person who sent the message.

    :type: str
    """
    event = property(lambda self: self._pretrigger.event)
    """The IRC event which triggered the message.

    :type: str

    Most plugin :func:`callables <callable>` primarily need to deal with
    ``PRIVMSG``. Other event types like ``NOTICE``, ``NICK``, ``TOPIC``,
    ``KICK``, etc. must be requested using :func:`.plugin.event`.
    """
    ctcp = property(lambda self: self._pretrigger.ctcp)
    """The CTCP command (if any).

    :type: str

    Common CTCP commands are ``ACTION``, ``VERSION``, and ``TIME``. Other
    commands include ``USERINFO``, ``PING``, and various ``DCC`` operations.

    .. versionadded:: 7.1

    .. important::

        Use this attribute instead of the ``intent`` tag in :attr:`tags`.
        Message intents never made it past the IRCv3 draft stage, and Sopel
        dropped support for them in Sopel 8.

    """
    match = property(lambda self: self._match)
    """The :ref:`Match object <match-objects>` for the triggering line.

    :type: :ref:`Match object <match-objects>`
    """
    group = property(lambda self: self._match.group)
    """The ``group()`` function of the :attr:`match` attribute.

    :type: :term:`method`
    :rtype: str

    Any regular-expression :func:`rules <.plugin.rule>` attached to the
    triggered :func:`callable` may define numbered or named groups that can be
    retrieved through this property.

    Sopel's command decorators each define a predetermined set of numbered
    groups containing fragments of the line that plugins commonly use.

    .. seealso::

       For more information on predefined numbered match groups in commands,
       see :func:`.plugin.command`, :func:`.plugin.action_command`, and
       :func:`.plugin.nickname_command`.

       Also see Python's :meth:`re.Match.group` documentation for details
       about this method's behavior.

    """
    groups = property(lambda self: self._match.groups)
    """The ``groups()`` function of the :attr:`match` attribute.

    :type: :term:`method`
    :rtype: tuple

    See Python's :meth:`re.Match.groups` documentation for details.
    """
    groupdict = property(lambda self: self._match.groupdict)
    """The ``groupdict()`` function of the :attr:`match` attribute.

    :type: :term:`method`
    :rtype: dict

    See Python's :meth:`re.Match.groupdict` documentation for details.
    """
    args = property(lambda self: self._pretrigger.args)
    """A list containing each of the arguments to an event.

    :type: list[str]

    These are the strings passed between the event name and the colon. For
    example, when setting ``mode -m`` on the channel ``#example``, args would
    be ``['#example', '-m']``
    """
    urls = property(lambda self: self._pretrigger.urls)
    """A tuple containing all URLs found in the text.

    :type: tuple

    URLs are listed only for ``PRIVMSG`` or a ``NOTICE``, otherwise this is
    an empty tuple.
    """
    plain = property(lambda self: self._pretrigger.plain)
    """The text without formatting control codes.

    :type: str

    This is the text of the trigger object without formatting control codes.
    """
    tags = property(lambda self: self._pretrigger.tags)
    """A map of the IRCv3 message tags on the message.

    :type: dict
    """
    admin = property(lambda self: self._admin)
    """Whether the triggering :attr:`nick` is one of the bot's admins.

    :type: bool

    ``True`` if the triggering :attr:`nick` is a Sopel admin; ``False`` if not.

    Note that Sopel's :attr:`~.config.core_section.CoreSection.owner` is also
    considered to be an admin.
    """
    owner = property(lambda self: self._owner)
    """Whether the :attr:`nick` which triggered the command is the bot's owner.

    :type: bool

    ``True`` if the triggering :attr:`nick` is Sopel's owner; ``False`` if not.
    """
    account = property(lambda self: self.tags.get('account') or self._account)
    """The services account name of the user sending the message.

    :type: str or None

    Note: This is only available if the ``account-tag`` capability or *both*
    the ``account-notify`` and ``extended-join`` capabilities are available on
    the connected IRC network. If this is not the case, or if the user sending
    the message isn't logged in to services, this property will be ``None``.
    """

    def __new__(
        cls,
        settings: config.Config,
        message: PreTrigger,
        match: Match,
        account: str | None = None,
    ) -> 'Trigger':
        return str.__new__(cls, message.args[-1] if message.args else '')

    def __init__(
        self,
        settings: config.Config,
        message: PreTrigger,
        match: Match,
        account: str | None = None,
    ) -> None:
        self._account = account
        self._pretrigger = message
        self._match = match
        self._is_privmsg = message.sender and message.sender.is_nick()

        def match_host_or_nick(pattern):
            pattern = tools.get_hostmask_regex(pattern)
            return bool(
                pattern.match(self.nick) or
                pattern.match('@'.join((self.nick, self.host)))
            )

        if settings.core.owner_account:
            self._owner = settings.core.owner_account == self.account
        else:
            self._owner = match_host_or_nick(settings.core.owner)
        self._admin = (
            self._owner or
            self.account in settings.core.admin_accounts or
            any(match_host_or_nick(item) for item in settings.core.admins)
        )
