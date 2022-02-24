from __future__ import annotations

from datetime import datetime
import functools
from typing import Any, Callable, Dict, Optional, Set, Union

from sopel import privileges
from sopel.tools import identifiers, memories


IdentifierFactory = Callable[[str], identifiers.Identifier]


@functools.total_ordering
class User:
    """A representation of a user Sopel is aware of.

    :param nick: the user's nickname
    :type nick: :class:`sopel.tools.identifiers.Identifier`
    :param str user: the user's local username ("user" in `user@host.name`)
    :param str host: the user's hostname ("host.name" in `user@host.name`)
    """
    __slots__ = (
        'nick', 'user', 'host', 'channels', 'account', 'away',
    )

    def __init__(
        self,
        nick: identifiers.Identifier,
        user: Optional[str],
        host: Optional[str],
    ) -> None:
        assert isinstance(nick, identifiers.Identifier)
        self.nick = nick
        """The user's nickname."""
        self.user = user
        """The user's local username."""
        self.host = host
        """The user's hostname."""
        self.channels: Dict[identifiers.Identifier, 'Channel'] = {}
        """The channels the user is in.

        This maps channel name :class:`~sopel.tools.identifiers.Identifier`\\s
        to :class:`Channel` objects.
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

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, User):
            return NotImplemented
        return self.nick == other.nick

    def __lt__(self, other: Any) -> bool:
        if not isinstance(other, User):
            return NotImplemented
        return self.nick < other.nick


@functools.total_ordering
class Channel:
    """A representation of a channel Sopel is in.

    :param name: the channel name
    :type name: :class:`~sopel.tools.identifiers.Identifier`
    :param identifier_factory: A factory to create
                               :class:`~sopel.tools.identifiers.Identifier`\\s
    """
    __slots__ = (
        'name',
        'users',
        'privileges',
        'topic',
        'modes',
        'last_who',
        'join_time',
        'make_identifier',
    )

    def __init__(
        self,
        name: identifiers.Identifier,
        identifier_factory: IdentifierFactory = identifiers.Identifier,
    ) -> None:
        assert isinstance(name, identifiers.Identifier)
        self.name = name
        """The name of the channel."""

        self.make_identifier: IdentifierFactory = identifier_factory
        """Factory to create :class:`~sopel.tools.identifiers.Identifier`.

        ``Identifier`` is used for :class:`User`'s nick, and the channel
        needs to translate nicks from string to ``Identifier`` when
        manipulating data associated to a user by its nickname.
        """

        self.users: Dict[
            identifiers.Identifier,
            User,
        ] = memories.SopelIdentifierMemory(
            identifier_factory=self.make_identifier,
        )
        """The users in the channel.

        This maps nickname :class:`~sopel.tools.identifiers.Identifier`\\s to
        :class:`User` objects.
        """
        self.privileges: Dict[
            identifiers.Identifier,
            int,
        ] = memories.SopelIdentifierMemory(
            identifier_factory=self.make_identifier,
        )
        """The permissions of the users in the channel.

        This maps nickname :class:`~sopel.tools.identifiers.Identifier`\\s to
        bitwise integer values. This can be compared to appropriate constants
        from :mod:`sopel.privileges`.
        """
        self.topic = ''
        """The topic of the channel."""

        self.modes: Dict[str, Union[Set, str, bool]] = {}
        """The channel's modes.

        For type A modes (nick/address list), the value is a set. For type B
        (parameter) or C (parameter when setting), the value is a string. For
        type D, the value is ``True``.

        .. note::

            Type A modes may only contain changes the bot has observed. Sopel
            does not automatically populate all modes and lists.
        """

        self.last_who: Optional[datetime] = None
        """The last time a WHO was requested for the channel."""

        self.join_time: Optional[datetime] = None
        """The time the server acknowledged our JOIN message.

        Based on server-reported time if the ``server-time`` IRCv3 capability
        is available, otherwise the time Sopel received it.
        """

    def clear_user(self, nick: identifiers.Identifier) -> None:
        """Remove ``nick`` from this channel.

        :param nick: the nickname of the user to remove

        Called after a user leaves the channel via PART, KICK, QUIT, etc.
        """
        user = self.users.pop(nick, None)
        self.privileges.pop(nick, None)
        if user is not None:
            user.channels.pop(self.name, None)

    def add_user(self, user: User, privs: int = 0) -> None:
        """Add ``user`` to this channel.

        :param user: the new user to add
        :param privs: privilege bitmask (see constants in
                      :mod:`sopel.privileges`)

        Called when a new user JOINs the channel.
        """
        assert isinstance(user, User)
        self.users[user.nick] = user
        self.privileges[user.nick] = privs or 0
        user.channels[self.name] = self

    def has_privilege(self, nick: str, privilege: int) -> bool:
        """Tell if a user has a ``privilege`` level or above in this channel.

        :param nick: a user's nick in this channel
        :param privilege: privilege level to check

        This method checks the user's privilege level in this channel, i.e. if
        it has this level or higher privileges::

            >>> channel.add_user(some_user, plugin.OP)
            >>> channel.has_privilege(some_user.nick, plugin.VOICE)
            True

        The ``nick`` argument can be either a :class:`str` or a
        :class:`sopel.tools.identifiers.Identifier`. If the user is not in this
        channel, it will be considered as not having any privilege.

        .. seealso::

            There are other methods to check the exact privilege level of a
            user, such as :meth:`is_oper`, :meth:`is_owner`, :meth:`is_admin`,
            :meth:`is_op`, :meth:`is_halfop`, and :meth:`is_voiced`.

        .. important::

            Not all IRC networks support all privilege levels. If you intend
            for your plugin to run on any network, it is safest to rely only
            on the presence of standard modes: ``+v`` (voice) and ``+o`` (op).

        """
        return self.privileges.get(self.make_identifier(nick), 0) >= privilege

    def is_oper(self, nick: str) -> bool:
        """Tell if a user has the OPER (operator) privilege level.

        :param nick: a user's nick in this channel

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
        identifier = self.make_identifier(nick)
        return bool(self.privileges.get(identifier, 0) & privileges.OPER)

    def is_owner(self, nick: str) -> bool:
        """Tell if a user has the OWNER privilege level.

        :param nick: a user's nick in this channel

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
        identifier = self.make_identifier(nick)
        return bool(self.privileges.get(identifier, 0) & privileges.OWNER)

    def is_admin(self, nick: str) -> bool:
        """Tell if a user has the ADMIN privilege level.

        :param nick: a user's nick in this channel

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
        identifier = self.make_identifier(nick)
        return bool(self.privileges.get(identifier, 0) & privileges.ADMIN)

    def is_op(self, nick: str) -> bool:
        """Tell if a user has the OP privilege level.

        :param nick: a user's nick in this channel

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
        identifier = self.make_identifier(nick)
        return bool(self.privileges.get(identifier, 0) & privileges.OP)

    def is_halfop(self, nick: str) -> bool:
        """Tell if a user has the HALFOP privilege level.

        :param nick: a user's nick in this channel

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
        identifier = self.make_identifier(nick)
        return bool(self.privileges.get(identifier, 0) & privileges.HALFOP)

    def is_voiced(self, nick: str) -> bool:
        """Tell if a user has the VOICE privilege level.

        :param nick: a user's nick in this channel

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
        identifier = self.make_identifier(nick)
        return bool(self.privileges.get(identifier, 0) & privileges.VOICE)

    def rename_user(
        self,
        old: identifiers.Identifier,
        new: identifiers.Identifier,
    ):
        """Rename a user.

        :param old: the user's old nickname
        :param new: the user's new nickname

        Called on ``NICK`` events.
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
