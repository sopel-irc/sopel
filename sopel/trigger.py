# coding=utf-8
from __future__ import unicode_literals, absolute_import, print_function, division

import re
import sys
import datetime

import sopel.tools

if sys.version_info.major >= 3:
    unicode = str
    basestring = str


class PreTrigger(object):
    """A parsed message from the server, which has not been matched against
    any rules."""
    component_regex = re.compile(r'([^!]*)!?([^@]*)@?(.*)')
    intent_regex = re.compile('\x01(\\S+) ?(.*)\x01')

    def __init__(self, own_nick, line):
        """own_nick is the bot's nick, needed to correctly parse sender.
        line is the full line from the server."""
        line = line.strip('\r')
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
            argstr, text = line.split(' :', 1)
            self.args = argstr.split(' ')
            self.args.append(text)
        else:
            self.args = line.split(' ')
            self.text = self.args[-1]

        self.event = self.args[0]
        self.args = self.args[1:]
        components = PreTrigger.component_regex.match(self.hostmask or '').groups()
        self.nick, self.user, self.host = components
        self.nick = sopel.tools.Identifier(self.nick)

        # If we have arguments, the first one is the sender
        # Unless it's a QUIT event
        if self.args and self.event != 'QUIT':
            target = sopel.tools.Identifier(self.args[0])
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

    Note that CTCP messages (`PRIVMSG`es and `NOTICE`es which start and end
    with `'\\x01'`) will have the `'\\x01'` bytes stripped, and the command
    (e.g. `ACTION`) placed mapped to the `'intent'` key in `Trigger.tags`.
    """
    sender = property(lambda self: self._pretrigger.sender)
    """The channel from which the message was sent.

    In a private message, this is the nick that sent the message."""
    time = property(lambda self: self._pretrigger.time)
    """A datetime object at which the message was received by the IRC server.

    If the server does not support server-time, then `time` will be the time
    that the message was received by Sopel"""
    raw = property(lambda self: self._pretrigger.line)
    """The entire message, as sent from the server. This includes the CTCP
    \\x01 bytes and command, if they were included."""
    is_privmsg = property(lambda self: self._is_privmsg)
    """True if the trigger is from a user, False if it's from a channel."""
    hostmask = property(lambda self: self._pretrigger.hostmask)
    """Hostmask of the person who sent the message as <nick>!<user>@<host>"""
    user = property(lambda self: self._pretrigger.user)
    """Local username of the person who sent the message"""
    nick = property(lambda self: self._pretrigger.nick)
    """The :class:`sopel.tools.Identifier` of the person who sent the message.
    """
    host = property(lambda self: self._pretrigger.host)
    """The hostname of the person who sent the message"""
    event = property(lambda self: self._pretrigger.event)
    """The IRC event (e.g. ``PRIVMSG`` or ``MODE``) which triggered the
    message."""
    match = property(lambda self: self._match)
    """The regular expression :class:`re.MatchObject` for the triggering line.
    """
    group = property(lambda self: self._match.group)
    """The ``group`` function of the ``match`` attribute.

    See Python :mod:`re` documentation for details."""
    groups = property(lambda self: self._match.groups)
    """The ``groups`` function of the ``match`` attribute.

    See Python :mod:`re` documentation for details."""
    groupdict = property(lambda self: self._match.groupdict)
    """The ``groupdict`` function of the ``match`` attribute.

    See Python :mod:`re` documentation for details."""
    args = property(lambda self: self._pretrigger.args)
    """
    A tuple containing each of the arguments to an event. These are the
    strings passed between the event name and the colon. For example,
    setting ``mode -m`` on the channel ``#example``, args would be
    ``('#example', '-m')``
    """
    tags = property(lambda self: self._pretrigger.tags)
    """A map of the IRCv3 message tags on the message."""
    admin = property(lambda self: self._admin)
    """True if the nick which triggered the command is one of the bot's admins.
    """
    owner = property(lambda self: self._owner)
    """True if the nick which triggered the command is the bot's owner."""
    account = property(lambda self: self.tags.get('account') or self._account)
    """The account name of the user sending the message.

    This is only available if either the account-tag or the account-notify and
    extended-join capabilites are available. If this isn't the case, or the user
    sending the message isn't logged in, this will be None.
    """

    def __new__(cls, config, message, match, account=None):
        self = unicode.__new__(cls, message.args[-1] if message.args else '')
        self._account = account
        self._pretrigger = message
        self._match = match
        self._is_privmsg = message.sender and message.sender.is_nick()

        def match_host_or_nick(pattern):
            pattern = sopel.tools.get_hostmask_regex(pattern)
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
