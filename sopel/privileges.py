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

    This class represents privileges as comparable, combinable flags. Lower
    privilege levels compare as *less than* (``<``) higher ones::

        >>> from sopel.privileges import AccessLevel
        >>> AccessLevel.VOICE < AccessLevel.HALFOP < AccessLevel.OP \\
        ... < AccessLevel.ADMIN < AccessLevel.OWNER
        True

    A user's privileges are represented as a combination of privilege levels::

        >>> priv = AccessLevel.VOICE | AccessLevel.OP

    This allows using comparators and bitwise operators to compare privileges.
    Here, ``priv`` contains both VOICE and OP privileges, but not HALFOP::

        >>> priv >= AccessLevel.OP
        True
        >>> bool(priv & AccessLevel.HALFOP)
        False

    .. important::

        Do not hard-code the value of a privilege level in your code; the values
        may change. Always reference or compare to the appropriate member of
        this class directly.

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

        Beware: This is one of the `nonstandard privilege levels`_.

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

        Beware: This is one of the `nonstandard privilege levels`_.

    """

    OWNER = enum.auto()
    """Privilege level for the +q channel permission

    .. versionadded:: 4.1
    .. versionchanged:: 8.0

        Constant moved from :mod:`sopel.plugin` to
        :class:`sopel.privileges.AccessLevel`.

    .. important::

        Beware: This is one of the `nonstandard privilege levels`_.

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

        Beware: This is one of the `nonstandard privilege levels`_.

    """
