# coding=utf-8
from __future__ import unicode_literals, absolute_import, print_function, division

import re
import sys

import sopel.tools

if sys.version_info.major >= 3:
    unicode = str
    basestring = str


class PreTrigger(object):
    """A parsed message from the server, which has not been matched against
    any rules."""
    component_regex = re.compile(r'([^!]*)!?([^@]*)@?(.*)')
    intent_regex = re.compile('\x01(\\S+) (.*)\x01')

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

        # TODO note what this is doing and why
        if line.startswith(':'):
            self.hostmask, line = line[1:].split(' ', 1)
        else:
            self.hostmask = None

        # TODO note what this is doing and why
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
        if self.args:
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


class Trigger(unicode):
    """A line from the server, which has matched a callable's rules.

    Note that CTCP messages (`PRIVMSG`es and `NOTICE`es which start and end
    with `'\\x01'`) will have the `'\\x01'` bytes stripped, and the command
    (e.g. `ACTION`) placed mapped to the `'intent'` key in `Trigger.tags`.
    """
    sender = property(lambda self: self._pretrigger.sender)
    """The channel from which the message was sent.

    In a private message, this is the nick that sent the message."""
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
    """The ``Identifier`` of the person who sent the message."""
    host = property(lambda self: self._pretrigger.host)
    """The hostname of the person who sent the message"""
    event = property(lambda self: self._pretrigger.event)
    """The IRC event (e.g. ``PRIVMSG`` or ``MODE``) which triggered the
    message."""
    match = property(lambda self: self._match)
    """The regular expression `MatchObject`_ for the triggering line.

    .. _MatchObject: http://docs.python.org/library/re.html#match-objects"""
    group = property(lambda self: self._match.group)
    """The ``group`` function of the ``match`` attribute.

    See Python `re`_ documentation for details."""
    groups = property(lambda self: self._match.groups)
    """The ``groups`` function of the ``match`` attribute.

    See Python `re`_ documentation for details."""
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

    def __new__(cls, config, message, match):
        self = unicode.__new__(cls, message.args[-1])
        self._pretrigger = message
        self._match = match
        self._is_privmsg = message.sender.is_nick()

        def match_host_or_nick(pattern):
            pattern = sopel.tools.get_hostmask_regex(pattern)
            return bool(
                pattern.match(self.nick) or
                pattern.match('@'.join((self.nick, self.host)))
            )

        self._admin = any(match_host_or_nick(item)
                         for item in config.core.admins)
        self._owner = match_host_or_nick(config.core.owner)
        self._admin = self.admin or self.owner

        return self
