# coding=utf-8
# ASCII ONLY IN THIS FILE THOUGH!!!!!!!
# Python does some stupid bullshit of respecting LC_ALL over the encoding on the
# file, so in order to undo Python's ridiculous fucking idiocy, we have to have
# our own check.

# Copyright 2008, Sean B. Palmer, inamidst.com
# Copyright 2012, Elsie Powell, http://embolalia.com
# Copyright 2012, Elad Alfassa <elad@fedoraproject.org>
#
# Licensed under the Eiffel Forum License 2.

from __future__ import absolute_import, division, print_function, unicode_literals

from collections import namedtuple
import locale
import re
import sys

import pkg_resources

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
if sys.version_info.major > 2:
    if not loc[1] or 'UTF-8' not in loc[1]:
        print('WARNING!!! You are running with a non-UTF8 locale environment '
              'variables (e.g. LC_ALL is set to "C"), which makes Python 3 do '
              'stupid things. If you get strange errors, please set it to '
              'something like "en_US.UTF-8".', file=sys.stderr)


__version__ = pkg_resources.get_distribution('sopel').version


def _version_info(version=__version__):
    regex = re.compile(r'(\d+)\.(\d+)\.(\d+)(?:[\-\.]?(a|b|rc)(\d+))?.*')
    version_groups = regex.match(version).groups()
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
    version_type = namedtuple('version_info',
                              'major, minor, micro, releaselevel, serial')
    return version_type(major, minor, micro, level, serial)


version_info = _version_info()
