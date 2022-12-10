""":mod:`sopel.irc.utils` contains low-level tools for IRC protocol handling.

.. warning::

    This is all internal code, not intended for direct use by plugins. It is
    subject to change between versions, even patch releases, without any
    advance notice.

"""
# Copyright 2019, Florian Strzelecki <florian.strzelecki@gmail.com>
#
# Licensed under the Eiffel Forum License 2.
from __future__ import annotations

from typing import NamedTuple


def safe(string):
    """Remove newlines from a string.

    :param str string: input text to process
    :return: the string without newlines
    :rtype: str
    :raises TypeError: when ``string`` is ``None``

    This function removes newlines from a string and always returns a unicode
    string (``str``), but doesn't strip or alter it in any other way::

        >>> safe('some text\\r\\n')
        'some text'

    This is useful to ensure a string can be used in a IRC message.

    .. versionchanged:: 7.1

        This function now raises a :exc:`TypeError` instead of an unpredictable
        behaviour when given ``None``.

    """
    if string is None:
        raise TypeError('safe function requires a string, not NoneType')
    if isinstance(string, bytes):
        string = string.decode("utf8")
    string = string.replace('\n', '')
    string = string.replace('\r', '')
    return string


class CapReq:
    """Represents a pending CAP REQ request.

    :param str prefix: either ``=`` (must be enabled),
                       ``-`` (must **not** be enabled),
                       or empty string (desired but optional)
    :param str plugin: the requesting plugin's name
    :param failure: function to call if this capability request fails
    :type failure: :term:`function`
    :param str arg: optional capability value; the request will fail if
                    the server's value is different
    :param success: function to call if this capability request succeeds
    :type success: :term:`function`

    The ``success`` and ``failure`` callbacks must accept two arguments:
    ``bot`` (a :class:`~sopel.bot.Sopel` instance) and ``cap`` (the name of
    the requested capability, as a string).

    .. seealso::
        For more information on how capability requests work, see the
        documentation for :meth:`sopel.irc.AbstractBot.cap_req`.
    """
    def __init__(self, prefix, plugin, failure=None, arg=None, success=None):
        def nop(bot, cap):
            pass
        # TODO at some point, reorder those args to be sane
        self.prefix = prefix
        self.plugin = plugin
        self.arg = arg
        self.failure = failure or nop
        self.success = success or nop


class MyInfo(NamedTuple):
    """Store client, servername, and version from ``RPL_MYINFO`` events.

    .. seealso::

        https://modern.ircdocs.horse/#rplmyinfo-004

    """
    client: str
    servername: str
    version: str
