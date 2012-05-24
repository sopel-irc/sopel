#!/usr/bin/env python
# -*- coding: utf8 -*-
"""
seen.py - Jenni Seen Module
Copyright 2008, Sean B. Palmer, inamidst.com
Copyright © 2012, Elad Alfassa <elad@fedoraproject.org>
Licensed under the Eiffel Forum License 2.

http://inamidst.com/phenny/
"""

import time
seen_dict=dict()

def seen(jenni, input):
    if not input.group(2):
        jenni.say(".seen <nick> - Reports when <nick> was last seen.")
        return
    nick = input.group(2)
    if seen_dict.has_key(nick):
        channel, timestamp = seen_dict[nick]
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime(timestamp))

        msg = "I last saw %s at %s on %s" % (nick, timestamp, channel)
        jenni.say(str(input.nick) + ': ' + msg)
    else:
        jenni.say("Sorry, I haven't seen %s around." % nick)
seen.rule = (['seen'], r'(\S+)')

def note(jenni, input):
    if input.sender.startswith('#'):
        seen_dict[input.nick] = (input.sender, time.time())
note.rule = r'(.*)'
note.priority = 'low'

if __name__ == '__main__':
    print __doc__.strip()
