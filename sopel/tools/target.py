# coding=utf-8
from __future__ import unicode_literals, absolute_import, print_function, division

import functools
from sopel.tools import Identifier


@functools.total_ordering
class User(object):
    """A representation of a user Sopel is aware of.

    :param nick: the user's nickname
    :type nick: :class:`~.tools.Identifier`
    :param str user: the user's local username ("user" in `user@host.name`)
    :param str host: the user's hostname ("host.name" in `user@host.name`)
    """
    def __init__(self, nick, user, host):
        assert isinstance(nick, Identifier)
        self.nick = nick
        """The user's nickname."""
        self.user = user
        """The user's local username."""
        self.host = host
        """The user's hostname."""
        self.channels = {}
        """The channels the user is in.

        This maps channel name :class:`~sopel.tools.Identifier`\\s to
        :class:`Channel` objects.
        """
        self.account = None
        """The IRC services account of the user.

        This relies on IRCv3 account tracking being enabled.
        """
        self.away = None
        """Whether the user is marked as away."""

    hostmask = property(lambda self: '{}!{}@{}'.format(self.nick, self.user,
                                                       self.host))
    """The user's full hostmask."""

    def __eq__(self, other):
        if not isinstance(other, User):
            return NotImplemented
        return self.nick == other.nick

    def __lt__(self, other):
        if not isinstance(other, User):
            return NotImplemented
        return self.nick < other.nick


@functools.total_ordering
class Channel(object):
    """A representation of a channel Sopel is in.

    :param name: the channel name
    :type name: :class:`~.tools.Identifier`
    """
    def __init__(self, name):
        assert isinstance(name, Identifier)
        self.name = name
        """The name of the channel."""
        self.users = {}
        """The users in the channel.

        This maps nickname :class:`~sopel.tools.Identifier`\\s to :class:`User`
        objects.
        """
        self.privileges = {}
        """The permissions of the users in the channel.

        This maps nickname :class:`~sopel.tools.Identifier`\\s to bitwise
        integer values. This can be compared to appropriate constants from
        :mod:`sopel.module`.
        """
        self.topic = ''
        """The topic of the channel."""

        self.last_who = None
        """The last time a WHO was requested for the channel."""

    def clear_user(self, nick):
        """Remove ``nick`` from this channel.

        :param nick: the nickname of the user to remove
        :type nick: :class:`~.tools.Identifier`

        Called after a user leaves the channel via PART, KICK, QUIT, etc.
        """
        user = self.users.pop(nick, None)
        self.privileges.pop(nick, None)
        if user is not None:
            user.channels.pop(self.name, None)

    def add_user(self, user, privs=0):
        """Add ``user`` to this channel.

        :param user: the new user to add
        :type user: :class:`User`
        :param int privs: privilege bitmask (see constants in
                          :mod:`sopel.module`)

        Called when a new user JOINs the channel.
        """
        assert isinstance(user, User)
        self.users[user.nick] = user
        self.privileges[user.nick] = privs
        user.channels[self.name] = self

    def rename_user(self, old, new):
        """Rename a user.

        :param old: the user's old nickname
        :type old: :class:`~.tools.Identifier`
        :param new: the user's new nickname
        :type new: :class:`~.tools.Identifier`

        Called on NICK events.
        """
        if old in self.users:
            self.users[new] = self.users.pop(old)
            self.users[new].nick = new
        if old in self.privileges:
            self.privileges[new] = self.privileges.pop(old)

    def __eq__(self, other):
        if not isinstance(other, Channel):
            return NotImplemented
        return self.name == other.name

    def __lt__(self, other):
        if not isinstance(other, Channel):
            return NotImplemented
        return self.name < other.name
