#!/usr/bin/env python
"""
version.py - Jenni Version Module
Copyright 2009, Silas Baronda
Licensed under the Eiffel Forum License 2.

More info:
 * Jenni: https://github.com/myano/jenni/
 * Phenny: http://inamidst.com/phenny/
"""

from subprocess import *

def version(jenni, input):
    p = Popen(["git", "log", "-n 1"], stdout=PIPE, close_fds=True)

    commit = p.stdout.readline()
    author = p.stdout.readline()
    date = p.stdout.readline()

    jenni.say(str(input.nick) + ": running version:")
    jenni.say("  " + commit)
    jenni.say("  " + author)
    jenni.say("  " + date)

version.commands = ['version']
version.priority = 'medium'

if __name__ == '__main__':
    print __doc__.strip()
