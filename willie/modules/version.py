"""
version.py - Willie Version Module
Copyright 2009, Silas Baronda
Licensed under the Eiffel Forum License 2.

http://willie.dftba.net
"""

from datetime import datetime
from subprocess import Popen, PIPE
import willie


def git_info():
    p = Popen(["git", "log", "-n 1"], stdout=PIPE, close_fds=True)

    commit = p.stdout.readline()
    author = p.stdout.readline()
    date = p.stdout.readline()
    return commit, author, date


@willie.module.commands('version')
def version(bot, trigger):
    """Display the latest commit version, if Willie is running in a git repo."""
    commit, author, date = git_info()

    if not commit.strip():
        bot.reply("Willie v. " + willie.__version__)
        return

    bot.say(str(trigger.nick) + ": Willie v. %s at commit:" % willie.__version__)
    bot.say("  " + commit)
    bot.say("  " + author)
    bot.say("  " + date)


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
