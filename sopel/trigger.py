# coding=utf-8
"""Triggers are how Sopel tells callables about their runtime context."""
from __future__ import unicode_literals, absolute_import, print_function, division

import re
import sys
import datetime

from sopel import tools


__all__ = [
    'PreTrigger',
    'Trigger',
]

if sys.version_info.major >= 3:
    unicode = str
    basestring = str


class PreTrigger(object):
    """A parsed raw message from the server.

    :param str own_nick: the bot's own IRC nickname
    :param str line: the full line from the server

    At the :class:`PreTrigger` stage, the line has not been matched against any
    rules yet. This is what Sopel uses to perform matching.

    ``own_nick`` is needed to correctly parse who sent the line (Sopel or
    someone else).

    ``line`` can also be a simulated echo-message, useful if the connected
    server does not support the capability.

    .. py:attribute:: args

        The IRC command's arguments.

        These are split on spaces, per the IRC protocol.

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

    .. py:attribute:: tags

        Any IRCv3 message tags attached to the line, as a :class:`dict`.

    .. py:attribute:: text

        The last argument of the IRC command.

        If the line contains ``:``, :attr:`text` will be the text following it.

        For lines that do *not* contain ``:``, :attr:`text` will be the last
        argument in :attr:`args` instead.

    .. py:attribute:: time

        The time when the message was received.

        If the IRC server sent a message tag indicating when *it* received the
        message, that is used instead of the time when Sopel received it.

    .. py:attribute:: user

        The sender's local username.

    """
    component_regex = re.compile(r'([^!]*)!?([^@]*)@?(.*)')
    intent_regex = re.compile('\x01(\\S+) ?(.*)\x01')

    def __init__(self, own_nick, line):
        line = line.strip('\r\n')
        self.line = line

        # Break off IRCv3 message tags, if present
        self.tags = {}
        if line.startswith('@'):
            tagstring, line = line.split(' ', 1)
            for tag in tagstring[1:].split(';'):
                tag = tag.split('=', 1)
                if len(tag) > 1:
                    self.tags[tag[0]] = tag[1]
                else:
                    self.tags[tag[0]] = None

        self.time = datetime.datetime.utcnow()
        if 'time' in self.tags:
            try:
                self.time = datetime.datetime.strptime(self.tags['time'], '%Y-%m-%dT%H:%M:%S.%fZ')
            except ValueError:
                pass  # Server isn't conforming to spec, ignore the server-time

        # Grabs hostmask from line.
        # Example: line = ':Sopel!foo@bar PRIVMSG #sopel :foobar!'
        #          print(hostmask)  # Sopel!foo@bar
        # All lines start with ":" except PING.
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
        # Example 2:  line = 'irc.freenode.net MODE Sopel +i'
        #             print(text)    # '+i'
        #             print(args)    # ['irc.freenode.net', 'MODE', 'Sopel', '+i']
        if ' :' in line:
            argstr, self.text = line.split(' :', 1)
            self.args = argstr.split(' ')
            self.args.append(self.text)
        else:
            self.args = line.split(' ')
            self.text = self.args[-1]

        self.event = self.args[0]
        self.args = self.args[1:]
        components = PreTrigger.component_regex.match(self.hostmask or '').groups()
        self.nick, self.user, self.host = components
        self.nick = tools.Identifier(self.nick)

        # If we have arguments, the first one is the sender
        # Unless it's a QUIT event
        if self.args and self.event != 'QUIT':
            target = tools.Identifier(self.args[0])
        else:
            target = None

        # Unless we're messaging the bot directly, in which case that second
        # arg will be our bot's name.
        if target and target.lower() == own_nick.lower():
            target = self.nick
        self.sender = target

        # Parse CTCP into a form consistent with IRCv3 intents
        if self.event == 'PRIVMSG' or self.event == 'NOTICE':
            intent_match = PreTrigger.intent_regex.match(self.args[-1])
            if intent_match:
                intent, message = intent_match.groups()
                self.tags['intent'] = intent
                self.args[-1] = message or ''

        # Populate account from extended-join messages
        if self.event == 'JOIN' and len(self.args) == 3:
            # Account is the second arg `...JOIN #Sopel account :realname`
            self.tags['account'] = self.args[1]


class Trigger(unicode):
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
    the command (e.g. ``ACTION``) placed mapped to the ``'intent'`` key in
    :attr:`Trigger.tags`.
    """
    sender = property(lambda self: self._pretrigger.sender)
    """Where the message arrived from.

    :type: :class:`~.tools.Identifier`

    This will be a channel name for "regular" (channel) messages, or the nick
    that sent a private message.
    """
    time = property(lambda self: self._pretrigger.time)
    """When the message was received.

    :type: :class:`~datetime.datetime` object

    If the IRC server supports ``server-time``, :attr:`time` will give that
    value. Otherwise, :attr:`time` will use the time when the message was
    received by Sopel.
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

    :type: :class:`~.tools.Identifier`
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
    ``KICK``, etc. must be requested using :func:`.module.event`.
    """
    match = property(lambda self: self._match)
    """The :ref:`Match object <match-objects>` for the triggering line.

    :type: :ref:`Match object <match-objects>`
    """
    group = property(lambda self: self._match.group)
    """The ``group()`` function of the :attr:`match` attribute.

    :type: :term:`method`
    :rtype: str

    Any regular-expression :func:`rules <.module.rule>` attached to the
    triggered :func:`callable` may define numbered or named groups that can be
    retrieved through this property.

    Sopel's command decorators each define a predetermined set of numbered
    groups containing fragments of the line that plugins commonly use.

    .. seealso::

       For more information on predefined numbered match groups in commands,
       see :func:`.module.commands`, :func:`.module.action_commands`, and
       :func:`.module.nickname_commands`.

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
    """A tuple containing each of the arguments to an event.

    :type: tuple

    These are the strings passed between the event name and the colon. For
    example, when setting ``mode -m`` on the channel ``#example``, args would
    be ``('#example', '-m')``
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

    def __new__(cls, config, message, match, account=None):
        self = unicode.__new__(cls, message.args[-1] if message.args else '')
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

        if config.core.owner_account:
            self._owner = config.core.owner_account == self.account
        else:
            self._owner = match_host_or_nick(config.core.owner)
        self._admin = (
            self._owner or
            self.account in config.core.admin_accounts or
            any(match_host_or_nick(item) for item in config.core.admins)
        )

        return self
