"""
version.py - Willie Version Module
Copyright 2009, Silas Baronda
Licensed under the Eiffel Forum License 2.

http://willie.dftba.net
"""

from datetime import datetime
from subprocess import *
from willie import __version__


def git_info():
    p = Popen(["git", "log", "-n 1"], stdout=PIPE, close_fds=True)

    commit = p.stdout.readline()
    author = p.stdout.readline()
    date = p.stdout.readline()
    return commit, author, date


def version(willie, trigger):
    """Display the latest commit version, if Willie is running in a git repo."""
    commit, author, date = git_info()
    
    if not commit.strip():
        willie.reply("Willie v. " + __version__)
        return

    willie.say(str(trigger.nick) + ": Willie v. %s at commit:" % __version__)
    willie.say("  " + commit)
    willie.say("  " + author)
    willie.say("  " + date)
version.commands = ['version']


def ctcp_version(willie, trigger):
    willie.write(('NOTICE', trigger.nick),
            '\x01VERSION Willie IRC Bot version %s\x01' % __version__)
ctcp_version.rule = '\x01VERSION\x01'
ctcp_version.rate = 20


def ctcp_source(willie, trigger):
    willie.write(('NOTICE', trigger.nick),
            '\x01SOURCE https://github.com/Embolalia/willie/\x01')
ctcp_source.rule = '\x01SOURCE\x01'
ctcp_source.rate = 20


def ctcp_ping(willie, trigger):
    text = trigger.group()
    text = text.replace("PING ", "")
    text = text.replace("\x01", "")
    willie.write(('NOTICE', trigger.nick),
            '\x01PING {0}\x01'.format(text))
ctcp_ping.rule = '\x01PING\s(.*)\x01'
ctcp_ping.rate = 10


def ctcp_time(willie, trigger):
    dt = datetime.now()
    current_time = dt.strftime("%A, %d. %B %Y %I:%M%p")
    willie.write(('NOTICE', trigger.nick),
            '\x01TIME {0}\x01'.format(current_time))
ctcp_time.rule = '\x01TIME\x01'
ctcp_time.rate = 20
