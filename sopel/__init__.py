"""
Sopel is a simple, easy-to-use, open-source IRC utility bot, written in Python.

It’s designed to be easy to use, easy to run, and easy to extend.
"""
#
# Copyright 2008, Sean B. Palmer, inamidst.com
# Copyright 2012, Elsie Powell, http://embolalia.com
# Copyright 2012, Elad Alfassa <elad@fedoraproject.org>
#
# Licensed under the Eiffel Forum License 2.

from __future__ import annotations

from collections import namedtuple
import importlib.metadata
import locale
import re
import sys


__all__ = [
    'bot',
    'config',
    'db',
    'formatting',
    'irc',
    'loader',
    'logger',
    'module',  # deprecated in 7.1, removed in 9.0
    'plugin',
    'tools',
    'trigger',
    'version_info',
]

loc = locale.getlocale()
if not loc[1] or ('UTF-8' not in loc[1] and 'utf8' not in loc[1]):
    print('Warning: Running with a non-UTF8 locale. If you see strange '
          'encoding errors, try setting the LC_ALL environment variable to '
          'something like "en_US.UTF-8".', file=sys.stderr)


__version__ = importlib.metadata.version('sopel')


def _version_info(version=__version__):
    regex = re.compile(r'(\d+)\.(\d+)\.(\d+)(?:[\-\.]?(a|b|rc)(\d+))?.*')
    version_match = regex.match(version)

    if version_match is None:
        raise RuntimeError("Can't parse version number!")

    version_groups = version_match.groups()
    major, minor, micro = (int(piece) for piece in version_groups[0:3])
    level = version_groups[3]
    serial = int(version_groups[4] or 0)
    if level == 'a':
        level = 'alpha'
    elif level == 'b':
        level = 'beta'
    elif level == 'rc':
        level = 'candidate'
    elif not level and version_groups[4] is None:
        level = 'final'
    else:
        level = 'alpha'

    VersionInfo = namedtuple('VersionInfo',
                             'major, minor, micro, releaselevel, serial')
    return VersionInfo(major, minor, micro, level, serial)


version_info = _version_info()
