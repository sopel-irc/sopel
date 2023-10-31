"""Constants for user privileges in channels."""
# Copyright 2023 dgw, technobabbl.es
#
# Licensed under the Eiffel Forum License 2.
from __future__ import annotations

import enum


__all__ = [
    'AccessLevel',
]


class AccessLevel(enum.IntFlag):
    """Enumeration of available user privilege levels.

    Privilege levels
    ================

    Historically, there were two user privilege levels in a channel:

    * :data:`~AccessLevel.OP`: channel operator, set and unset by modes ``+o``
      and ``-o``
    * :data:`~AccessLevel.VOICE`: the privilege to send messages to a channel
      with the ``+m`` mode, set and unset by modes ``+v`` and ``-v``

    Since then, other privileges have been adopted by IRC servers and clients:

    * :data:`~AccessLevel.HALFOP`: intermediate level between VOICE and OP, set
      and unset by modes ``+h`` and ``-h``
    * :data:`~AccessLevel.ADMIN`: channel admin, above OP and below OWNER, set
      and unset by modes ``+a`` and ``-a``
    * :data:`~AccessLevel.OWNER`: channel owner, above ADMIN and OP, set and
      unset by modes ``+q`` and ``-q``

    .. important::

        Not all IRC networks support these added privilege modes. If you are
        writing a plugin for public distribution, ensure your code behaves
        sensibly if only +v (voice) and +o (op) modes exist.

    Comparing privileges
    ====================

    This class represents privileges as powers of two, with higher values
    assigned to higher-level privileges::

        >>> from sopel.privileges import AccessLevel
        >>> AccessLevel.VOICE < AccessLevel.HALFOP < AccessLevel.OP \\
        ... < AccessLevel.ADMIN < AccessLevel.OWNER
        True

    Then a user's privileges are represented as a sum of privilege levels::

        >>> AccessLevel.VOICE
        1
        >>> AccessLevel.OP
        4
        >>> priv = AccessLevel.VOICE | AccessLevel.OP
        >>> priv
        5

    This allows using comparators and bitwise operators to compare privileges.
    Here, ``priv`` contains both VOICE and OP privileges, but not HALFOP::

        >>> priv >= AccessLevel.OP
        True
        >>> bool(priv & AccessLevel.HALFOP)
        False

    .. important::

        Do not refer directly to the integer value of a privilege level in your
        code; the values may change. Use the appropriate member of this class as
        a reference point instead.

    """
    # values should behave as ints, but their string representations should
    # still look like Enum
    __str__ = enum.Enum.__str__

    VOICE = enum.auto()
    """Privilege level for the +v channel permission

    .. versionadded:: 4.1
    .. versionchanged:: 8.0

        Constant moved from :mod:`sopel.plugin` to
        :class:`sopel.privileges.AccessLevel`.

    """

    HALFOP = enum.auto()
    """Privilege level for the +h channel permission

    .. versionadded:: 4.1
    .. versionchanged:: 8.0

        Constant moved from :mod:`sopel.plugin` to
        :class:`sopel.privileges.AccessLevel`.

    .. important::

        Not all IRC networks support this privilege mode. If you are writing a
        plugin for public distribution, ensure your code behaves sensibly if
        only ``+v`` (voice) and ``+o`` (op) modes exist.

    """

    OP = enum.auto()
    """Privilege level for the +o channel permission

    .. versionadded:: 4.1
    .. versionchanged:: 8.0

        Constant moved from :mod:`sopel.plugin` to
        :class:`sopel.privileges.AccessLevel`.

    """

    ADMIN = enum.auto()
    """Privilege level for the +a channel permission

    .. versionadded:: 4.1
    .. versionchanged:: 8.0

        Constant moved from :mod:`sopel.plugin` to
        :class:`sopel.privileges.AccessLevel`.

    .. important::

        Not all IRC networks support this privilege mode. If you are writing a
        plugin for public distribution, ensure your code behaves sensibly if
        only ``+v`` (voice) and ``+o`` (op) modes exist.

    """

    OWNER = enum.auto()
    """Privilege level for the +q channel permission

    .. versionadded:: 4.1
    .. versionchanged:: 8.0

        Constant moved from :mod:`sopel.plugin` to
        :class:`sopel.privileges.AccessLevel`.

    .. important::

        Not all IRC networks support this privilege mode. If you are writing a
        plugin for public distribution, ensure your code behaves sensibly if
        only ``+v`` (voice) and ``+o`` (op) modes exist.

    """

    OPER = enum.auto()
    """Privilege level for the +y/+Y channel permission

    Note: Except for these (non-standard) channel modes, Sopel does not monitor
    or store any user's OPER status.

    .. versionadded:: 7.0
    .. versionchanged:: 8.0

        Constant moved from :mod:`sopel.plugin` to
        :class:`sopel.privileges.AccessLevel`.

    .. important::

        Not all IRC networks support this privilege mode. If you are writing a
        plugin for public distribution, ensure your code behaves sensibly if
        only ``+v`` (voice) and ``+o`` (op) modes exist.

    """
