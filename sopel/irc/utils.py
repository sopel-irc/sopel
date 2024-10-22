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

from sopel.lifecycle import deprecated


def safe(string: str) -> str:
    """Remove disallowed bytes from a string, and ensure Unicode.

    :param string: input text to process
    :return: the string as Unicode without characters prohibited in IRC messages
    :raises TypeError: when ``string`` is ``None``

    This function removes newlines and null bytes from a string. It will always
    return a Unicode ``str``, even if given non-Unicode input, but doesn't strip
    or alter the string in any other way::

        >>> safe('some \\x00text\\r\\n')
        'some text'

    This is useful to ensure a string can be used in a IRC message. Parameters
    can **never** contain NUL, CR, or LF octets, per :rfc:`2812#section-2.3.1`.

    .. versionchanged:: 7.1

        This function now raises a :exc:`TypeError` instead of an unpredictable
        behaviour when given ``None``.

    .. versionchanged:: 8.0.1

        Also remove NUL (``\\x00``) in addition to CR/LF.

    """
    if string is None:
        raise TypeError('safe function requires a string, not NoneType')
    if isinstance(string, bytes):
        string = string.decode("utf8")
    string = string.replace('\n', '')
    string = string.replace('\r', '')
    string = string.replace('\x00', '')
    return string


@deprecated('CapReq is obsolete.', version='8.0', removed_in='9.0')
class CapReq:
    """Obsolete representation of a CAP REQ.

    .. deprecated:: 8.0

        This class is deprecated. See :class:`sopel.plugin.capability` instead.

        This will be removed in Sopel 9.

    """
    def __init__(self, prefix, plugin, failure=None, arg=None, success=None):
        def nop(bot, cap):
            pass
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
