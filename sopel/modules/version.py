# coding=utf-8
"""
version.py - Sopel Version Module
Copyright 2009, Silas Baronda
Copyright 2014, Dimitri Molenaars <tyrope@tyrope.nl>
Licensed under the Eiffel Forum License 2.

http://sopel.chat
"""
from __future__ import unicode_literals, absolute_import, print_function, division

from datetime import datetime
import sopel
import re
from os import path
import json

log_line = re.compile('\S+ (\S+) (.*? <.*?>) (\d+) (\S+)\tcommit[^:]*: (.+)')


def git_info():
    repo = path.join(path.dirname(path.dirname(path.dirname(__file__))), '.git')
    head = path.join(repo, 'HEAD')
    if path.isfile(head):
        with open(head) as h:
            head_loc = h.readline()[5:-1]  # strip ref: and \n
        head_file = path.join(repo, head_loc)
        if path.isfile(head_file):
            with open(head_file) as h:
                sha = h.readline()
                if sha:
                    return sha


@sopel.module.commands('version')
def version(bot, trigger):
    """Display the latest commit version, if Sopel is running in a git repo."""
    release = sopel.__version__
    sha = git_info()
    if not sha:
        msg = 'Sopel v. ' + release
        if release[-4:] == '-git':
            msg += ' at unknown commit.'
        bot.reply(msg)
        return

    bot.reply("Sopel v. {} at commit: {}".format(sopel.__version__, sha))


@sopel.module.intent('VERSION')
@sopel.module.rate(20)
@sopel.module.rule('.*')
def ctcp_version(bot, trigger):
    print('wat')
    bot.write(('NOTICE', trigger.nick),
              '\x01VERSION Sopel IRC Bot version %s\x01' % sopel.__version__)


@sopel.module.rule('\x01SOURCE\x01')
@sopel.module.rate(20)
def ctcp_source(bot, trigger):
    bot.write(('NOTICE', trigger.nick),
              '\x01SOURCE https://github.com/sopel-irc/sopel/\x01')


@sopel.module.rule('\x01PING\s(.*)\x01')
@sopel.module.rate(10)
def ctcp_ping(bot, trigger):
    text = trigger.group()
    text = text.replace("PING ", "")
    text = text.replace("\x01", "")
    bot.write(('NOTICE', trigger.nick),
              '\x01PING {0}\x01'.format(text))


@sopel.module.rule('\x01TIME\x01')
@sopel.module.rate(20)
def ctcp_time(bot, trigger):
    dt = datetime.now()
    current_time = dt.strftime("%A, %d. %B %Y %I:%M%p")
    bot.write(('NOTICE', trigger.nick),
              '\x01TIME {0}\x01'.format(current_time))
