# coding=utf8
"""
version.py - Willie Version Module
Copyright 2009, Silas Baronda
Copyright 2014, Dimitri Molenaars <tyrope@tyrope.nl>
Licensed under the Eiffel Forum License 2.

http://willie.dftba.net
"""
from __future__ import unicode_literals

from datetime import datetime
import willie
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


@willie.module.commands('version')
def version(bot, trigger):
    """Display the latest commit version, if Willie is running in a git repo."""
    release = willie.__version__
    sha = git_info()
    if not sha:
        msg = 'Willie v. ' + release
        if release[-4:] == '-git':
            msg += ' at unknown commit.'
        bot.reply(msg)
        return

    bot.reply("Willie v. {} at commit: {}".format(willie.__version__, sha))


@willie.module.rule('\x01VERSION\x01')
@willie.module.rate(20)
def ctcp_version(bot, trigger):
    bot.write(('NOTICE', trigger.nick),
              '\x01VERSION Willie IRC Bot version %s\x01' % willie.__version__)


@willie.module.rule('\x01SOURCE\x01')
@willie.module.rate(20)
def ctcp_source(bot, trigger):
    bot.write(('NOTICE', trigger.nick),
              '\x01SOURCE https://github.com/Embolalia/willie/\x01')


@willie.module.rule('\x01PING\s(.*)\x01')
@willie.module.rate(10)
def ctcp_ping(bot, trigger):
    text = trigger.group()
    text = text.replace("PING ", "")
    text = text.replace("\x01", "")
    bot.write(('NOTICE', trigger.nick),
              '\x01PING {0}\x01'.format(text))


@willie.module.rule('\x01TIME\x01')
@willie.module.rate(20)
def ctcp_time(bot, trigger):
    dt = datetime.now()
    current_time = dt.strftime("%A, %d. %B %Y %I:%M%p")
    bot.write(('NOTICE', trigger.nick),
              '\x01TIME {0}\x01'.format(current_time))

@willie.module.interval(86400)
def version_check(bot):
    """
    This functions checks every 24 hours if there's a new version available.
    """

    message_release = "My version doesn't match the latest release (%s(latest)s). I'm on %(local)s. Please update me."
    message_git = "My version doesn't match the master branch (%(latest)s). I'm on %(local)s). Please update me."

    API_url = 'https://api.github.com/repos/embolalia/willie/'

    git_HEAD = git_info()
    if not git_HEAD:
        # Running a release version.
        API_result = willie.web.get(API_url + 'releases')

        # Get the first(0) release name('name'), which should be the latest.
        latest_release = json.loads(API_result)[0]['name'].encode('utf-8')

        if willie.__version__ != latest_release:
            # We're not updated!
            # Message the owner.
            bot.msg(bot.config.core.owner, message_release %
                    {'latest': latest_release, 'local': willie.__version__ })
    else:
        # Running a -git version.
        API_result = willie.web.get(API_url + 'commits/master')

        # Get latest commit's hash('sha').
        remote_HEAD = json.loads(API_result)['sha'].encode('utf-8')

        if git_HEAD.strip() != remote_HEAD:
            # We're not updated! Note that this might mean you're AHEAD of master,
            # or on a different repo. At which case, you should know what you're doing.
            # Message the owner.
            bot.msg(bot.config.core.owner, message_git %
                    {'latest': remote_HEAD, 'local': git_HEAD })

