# coding=utf-8
# Copyright 2019, Florian Strzelecki <florian.strzelecki@gmail.com>
#
# Licensed under the Eiffel Forum License 2.
from __future__ import unicode_literals, absolute_import, print_function, division

import collections
import sys
from dns import resolver, rdtypes

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
    """Remove newlines from a string."""
    if sys.version_info.major >= 3 and isinstance(string, bytes):
        string = string.decode("utf8")
    elif sys.version_info.major < 3:
        if not isinstance(string, unicode):
            string = unicode(string, encoding='utf8')
    string = string.replace('\n', '')
    string = string.replace('\r', '')
    return string


class CapReq(object):
    def __init__(self, prefix, module, failure=None, arg=None, success=None):
        def nop(bot, cap):
            pass
        # TODO at some point, reorder those args to be sane
        self.prefix = prefix
        self.module = module
        self.arg = arg
        self.failure = failure or nop
        self.success = success or nop


class MyInfo(collections.namedtuple('MyInfo', MYINFO_ARGS)):
    """Store client, servername, and version from ``RPL_MYINFO`` events.

    .. seealso::

        https://modern.ircdocs.horse/#rplmyinfo-004

    """
    # TODO: replace by a class using typing.NamedTuple (new in Python 3.5+)
    # probably in Sopel 8.0 (due to drop most old Python versions)
