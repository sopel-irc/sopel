#!/usr/bin/env python
"""
version.py - Jenni Version Module
Copyright 2009, Silas Baronda
Licensed under the Eiffel Forum License 2.

More info:
 * Jenni: https://github.com/myano/jenni/
 * Phenny: http://inamidst.com/phenny/
"""

from datetime import datetime
from subprocess import *


def git_info():
    p = Popen(["git", "log", "-n 1"], stdout=PIPE, close_fds=True)

    commit = p.stdout.readline()
    author = p.stdout.readline()
    date = p.stdout.readline()
    return commit, author, date


def version(jenni, input):
    commit, author, date = git_info()

    jenni.say(str(input.nick) + ": running version:")
    jenni.say("  " + commit)
    jenni.say("  " + author)
    jenni.say("  " + date)
version.commands = ['version']
version.priority = 'medium'
version.rate = 30


def ctcp_version(jenni, input):
    commit, author, date = git_info()
    date = date.replace("  ", "")

    jenni.write(('NOTICE', input.nick),
            '\x01VERSION {0} : {1}\x01'.format(commit, date))
ctcp_version.rule = '\x01VERSION\x01'
ctcp_version.rate = 20


def ctcp_source(jenni, input):
    jenni.write(('NOTICE', input.nick),
            '\x01SOURCE https://github.com/myano/jenni/\x01')
    jenni.write(('NOTICE', input.nick),
            '\x01SOURCE\x01')
ctcp_source.rule = '\x01SOURCE\x01'
ctcp_source.rate = 20


def ctcp_ping(jenni, input):
    text = input.group()
    text = text.replace("PING ", "")
    text = text.replace("\x01", "")
    jenni.write(('NOTICE', input.nick),
            '\x01PING {0}\x01'.format(text))
ctcp_ping.rule = '\x01PING\s(.*)\x01'
ctcp_ping.rate = 10


def ctcp_time(jenni, input):
    dt = datetime.now()
    current_time = dt.strftime("%A, %d. %B %Y %I:%M%p")
    jenni.write(('NOTICE', input.nick),
            '\x01TIME {0}\x01'.format(current_time))
ctcp_time.rule = '\x01TIME\x01'
ctcp_time.rate = 20

if __name__ == '__main__':
    print __doc__.strip()
