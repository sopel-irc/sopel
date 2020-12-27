# coding=utf-8
# Copyright 2019, Florian Strzelecki <florian.strzelecki@gmail.com>
#
# Licensed under the Eiffel Forum License 2.
from __future__ import absolute_import, division, print_function, unicode_literals

import collections
import sys

from dns import rdtypes, resolver

from sopel.tools import deprecated

if sys.version_info.major >= 3:
    unicode = str


MYINFO_ARGS = ['client', 'servername', 'version']


def get_cnames(domain):
    """Determine the CNAMEs for a given domain.

    :param str domain: domain to check
    :return: list (of str)
    """
    try:
        answer = resolver.query(domain, "CNAME")
    except resolver.NoAnswer:
        return []

    return [
        data.to_text()[:-1]
        for data in answer
        if isinstance(data, rdtypes.ANY.CNAME.CNAME)
    ]


def safe(string):
    """Remove newlines from a string.

    :param str string: input text to process
    :return: the string without newlines
    :rtype: str
    :raises TypeError: when ``string`` is ``None``

    This function removes newlines from a string and always returns a unicode
    string (as in ``str`` on Python 3 and ``unicode`` on Python 2), but doesn't
    strip or alter it in any other way::

        >>> safe('some text\\r\\n')
        'some text'

    This is useful to ensure a string can be used in a IRC message.

    .. versionchanged:: 7.1

        This function now raises a :exc:`TypeError` instead of an unpredictable
        behaviour when given ``None``.

    """
    if string is None:
        raise TypeError('safe function requires a string, not NoneType')
    if sys.version_info.major >= 3 and isinstance(string, bytes):
        string = string.decode("utf8")
    elif sys.version_info.major < 3:
        if not isinstance(string, unicode):
            string = unicode(string, encoding='utf8')
    string = string.replace('\n', '')
    string = string.replace('\r', '')
    return string


class CapReq(object):
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

    @property
    @deprecated(
        reason='use the `plugin` property instead',
        version='7.1',
        removed_in='8.0',
    )
    def module(self):
        return self.plugin


class MyInfo(collections.namedtuple('MyInfo', MYINFO_ARGS)):
    """Store client, servername, and version from ``RPL_MYINFO`` events.

    .. seealso::

        https://modern.ircdocs.horse/#rplmyinfo-004

    """
    # TODO: replace by a class using typing.NamedTuple (new in Python 3.5+)
    # probably in Sopel 8.0 (due to drop most old Python versions)
