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
# from http://parand.com/say/index.php/2007/07/13/simple-multi-dimensional-dictionaries-in-python/
# A simple class to make mutli dimensional dict easy to use
class Ddict(dict):
    def __init__(self, default=None):
        self.default = default

    def __getitem__(self, key):
        if not self.has_key(key):
            self[key] = self.default()
        return dict.__getitem__(self, key)

seen_dict=Ddict(dict)

def seen(jenni, input):
    if not input.group(2):
        jenni.say(".seen <nick> - Reports when <nick> was last seen.")
        return
    nick = input.group(2).lower()
    if seen_dict.has_key(nick):
        timestamp = seen_dict[nick]['timestamp']
        channel = seen_dict[nick]['channel']
        message = seen_dict[nick]['message']
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime(timestamp))

        msg = "I last saw %s at %s on %s, saying %s" % (nick, timestamp, channel, message)
        jenni.say(str(input.nick) + ': ' + msg)
    else:
        jenni.say("Sorry, I haven't seen %s around." % nick)
seen.rule = (['seen'], r'(\S+)')

def note(jenni, input):
    if input.sender.startswith('#'):
        seen_dict[input.nick]['timestamp'] = time.time()
        seen_dict[input.nick]['channel'] = input.sender.lower()
        seen_dict[input.nick]['message'] = input

note.rule = r'(.*)'
note.priority = 'low'

if __name__ == '__main__':
    print __doc__.strip()
