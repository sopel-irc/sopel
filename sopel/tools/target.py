# coding=utf-8
from __future__ import absolute_import, division, print_function, unicode_literals

import functools

from sopel import plugin
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
        :mod:`sopel.plugin`.
        """
        self.topic = ''
        """The topic of the channel."""

        self.modes = {}
        """The channel's modes.

        For type A modes (nick/address list), the value is a set. For type B
        (parameter) or C (parameter when setting), the value is a string. For
        type D, the value is ``True``.

        .. note::

            Type A modes may only contain changes the bot has observed. Sopel
            does not automatically populate all modes and lists.
        """

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
                          :mod:`sopel.plugin`)

        Called when a new user JOINs the channel.
        """
        assert isinstance(user, User)
        self.users[user.nick] = user
        self.privileges[user.nick] = privs or 0
        user.channels[self.name] = self

    def has_privilege(self, nick, privilege):
        """Tell if a user has a ``privilege`` level or above in this channel.

        :param str nick: a user's nick in this channel
        :param int privilege: privilege level to check
        :rtype: bool

        This method checks the user's privilege level in this channel, i.e. if
        it has this level or higher privileges::

            >>> channel.add_user(some_user, plugin.OP)
            >>> channel.has_privilege(some_user.nick, plugin.VOICE)
            True

        The ``nick`` argument can be either a :class:`str` or a
        :class:`sopel.tools.Identifier`. If the user is not in this channel,
        it will be considered as not having any privilege.

        .. seealso::

            There are other methods to check the exact privilege level of a
            user, such as :meth:`is_oper`, :meth:`is_owner`, :meth:`is_admin`,
            :meth:`is_op`, :meth:`is_halfop`, and :meth:`is_voiced`.

        .. important::

            Not all IRC networks support all privilege levels. If you intend
            for your plugin to run on any network, it is safest to rely only
            on the presence of standard modes: ``+v`` (voice) and ``+o`` (op).

        """
        return self.privileges.get(Identifier(nick), 0) >= privilege

    def is_oper(self, nick):
        """Tell if a user has the OPER (operator) privilege level.

        :param str nick: a user's nick in this channel
        :rtype: bool

        Unlike :meth:`has_privilege`, this method checks if the user has been
        explicitly granted the OPER privilege level::

            >>> channel.add_user(some_user, plugin.OPER)
            >>> channel.is_oper(some_user.nick)
            True
            >>> channel.is_voiced(some_user.nick)
            False

        Note that you can always have more than one privilege level::

            >>> channel.add_user(some_user, plugin.OPER | plugin.VOICE)
            >>> channel.is_oper(some_user.nick)
            True
            >>> channel.is_voiced(some_user.nick)
            True

        .. important::

            Not all IRC networks support this privilege mode. If you are
            writing a plugin for public distribution, ensure your code behaves
            sensibly if only ``+v`` (voice) and ``+o`` (op) modes exist.

        """
        return self.privileges.get(Identifier(nick), 0) & plugin.OPER

    def is_owner(self, nick):
        """Tell if a user has the OWNER privilege level.

        :param str nick: a user's nick in this channel
        :rtype: bool

        Unlike :meth:`has_privilege`, this method checks if the user has been
        explicitly granted the OWNER privilege level::

            >>> channel.add_user(some_user, plugin.OWNER)
            >>> channel.is_owner(some_user.nick)
            True
            >>> channel.is_voiced(some_user.nick)
            False

        Note that you can always have more than one privilege level::

            >>> channel.add_user(some_user, plugin.OWNER | plugin.VOICE)
            >>> channel.is_owner(some_user.nick)
            True
            >>> channel.is_voiced(some_user.nick)
            True

        .. important::

            Not all IRC networks support this privilege mode. If you are
            writing a plugin for public distribution, ensure your code behaves
            sensibly if only ``+v`` (voice) and ``+o`` (op) modes exist.

        """
        return self.privileges.get(Identifier(nick), 0) & plugin.OWNER

    def is_admin(self, nick):
        """Tell if a user has the ADMIN privilege level.

        :param str nick: a user's nick in this channel
        :rtype: bool

        Unlike :meth:`has_privilege`, this method checks if the user has been
        explicitly granted the ADMIN privilege level::

            >>> channel.add_user(some_user, plugin.ADMIN)
            >>> channel.is_admin(some_user.nick)
            True
            >>> channel.is_voiced(some_user.nick)
            False

        Note that you can always have more than one privilege level::

            >>> channel.add_user(some_user, plugin.ADMIN | plugin.VOICE)
            >>> channel.is_admin(some_user.nick)
            True
            >>> channel.is_voiced(some_user.nick)
            True

        .. important::

            Not all IRC networks support this privilege mode. If you are
            writing a plugin for public distribution, ensure your code behaves
            sensibly if only ``+v`` (voice) and ``+o`` (op) modes exist.

        """
        return self.privileges.get(Identifier(nick), 0) & plugin.ADMIN

    def is_op(self, nick):
        """Tell if a user has the OP privilege level.

        :param str nick: a user's nick in this channel
        :rtype: bool

        Unlike :meth:`has_privilege`, this method checks if the user has been
        explicitly granted the OP privilege level::

            >>> channel.add_user(some_user, plugin.OP)
            >>> channel.is_op(some_user.nick)
            True
            >>> channel.is_voiced(some_user.nick)
            False

        Note that you can always have more than one privilege level::

            >>> channel.add_user(some_user, plugin.OP | plugin.VOICE)
            >>> channel.is_op(some_user.nick)
            True
            >>> channel.is_voiced(some_user.nick)
            True

        """
        return self.privileges.get(Identifier(nick), 0) & plugin.OP

    def is_halfop(self, nick):
        """Tell if a user has the HALFOP privilege level.

        :param str nick: a user's nick in this channel
        :rtype: bool

        Unlike :meth:`has_privilege`, this method checks if the user has been
        explicitly granted the HALFOP privilege level::

            >>> channel.add_user(some_user, plugin.HALFOP)
            >>> channel.is_halfop(some_user.nick)
            True
            >>> channel.is_voiced(some_user.nick)
            False

        Note that you can always have more than one privilege level::

            >>> channel.add_user(some_user, plugin.HALFOP | plugin.VOICE)
            >>> channel.is_halfop(some_user.nick)
            True
            >>> channel.is_voiced(some_user.nick)
            True

        .. important::

            Not all IRC networks support this privilege mode. If you are
            writing a plugin for public distribution, ensure your code behaves
            sensibly if only ``+v`` (voice) and ``+o`` (op) modes exist.

        """
        return self.privileges.get(Identifier(nick), 0) & plugin.HALFOP

    def is_voiced(self, nick):
        """Tell if a user has the VOICE privilege level.

        :param str nick: a user's nick in this channel
        :rtype: bool

        Unlike :meth:`has_privilege`, this method checks if the user has been
        explicitly granted the VOICE privilege level::

            >>> channel.add_user(some_user, plugin.VOICE)
            >>> channel.is_voiced(some_user.nick)
            True
            >>> channel.add_user(some_user, plugin.OP)
            >>> channel.is_voiced(some_user.nick)
            False

        Note that you can always have more than one privilege level::

            >>> channel.add_user(some_user, plugin.VOICE | plugin.OP)
            >>> channel.is_voiced(some_user.nick)
            True
            >>> channel.is_op(some_user.nick)
            True

        """
        return self.privileges.get(Identifier(nick), 0) & plugin.VOICE

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
