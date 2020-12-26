# coding=utf-8
"""
version.py - Sopel Version Plugin
Copyright 2009, Silas Baronda
Copyright 2014, Dimitri Molenaars <tyrope@tyrope.nl>
Licensed under the Eiffel Forum License 2.

https://sopel.chat
"""
from __future__ import absolute_import, division, print_function, unicode_literals

import datetime
import os
import platform

from sopel import __version__ as release, plugin


PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
GIT_DIR = os.path.join(PROJECT_DIR, '.git')


def git_info():
    head = os.path.join(GIT_DIR, 'HEAD')
    if os.path.isfile(head):
        with open(head) as h:
            head_loc = h.readline()[5:-1]  # strip ref: and \n
        head_file = os.path.join(GIT_DIR, head_loc)
        if os.path.isfile(head_file):
            with open(head_file) as h:
                sha = h.readline()
                if sha:
                    return sha


@plugin.command('version')
@plugin.output_prefix('[version] ')
def version(bot, trigger):
    """Display the installed version of Sopel.

    Includes the version of Python Sopel is installed on.
    Includes the commit hash if Sopel is installed from source.
    """
    parts = [
        'Sopel v%s' % release,
        'Python: %s' % platform.python_version()
    ]
    sha = git_info()
    if sha:
        parts.append('Commit: %s' % sha)

    bot.say(' | '.join(parts))


@plugin.ctcp('VERSION')
@plugin.rate(20)
def ctcp_version(bot, trigger):
    bot.write(('NOTICE', trigger.nick),
              '\x01VERSION Sopel IRC Bot version %s\x01' % release)


@plugin.ctcp('SOURCE')
@plugin.rate(20)
def ctcp_source(bot, trigger):
    bot.write(('NOTICE', trigger.nick),
              '\x01SOURCE https://github.com/sopel-irc/sopel\x01')


@plugin.ctcp('PING')
@plugin.rate(10)
def ctcp_ping(bot, trigger):
    text = trigger.group()
    text = text.replace("PING ", "")
    text = text.replace("\x01", "")
    bot.write(('NOTICE', trigger.nick),
              '\x01PING {0}\x01'.format(text))


@plugin.ctcp('TIME')
@plugin.rate(20)
def ctcp_time(bot, trigger):
    dt = datetime.datetime.now()
    current_time = dt.strftime("%A, %d. %B %Y %I:%M%p")
    bot.write(('NOTICE', trigger.nick),
              '\x01TIME {0}\x01'.format(current_time))
