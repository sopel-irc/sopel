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
<<<<<<< HEAD
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
        nick = input.nick.lower()
        seen_dict[nick]['timestamp'] = time.time()
        seen_dict[nick]['channel'] = input.sender
        seen_dict[nick]['message'] = input

note.rule = r'(.*)'
note.priority = 'low'
=======
from tools import deprecated

@deprecated
def f_seen(self, origin, match, args):
    """.seen <nick> - Reports when <nick> was last seen."""
    if origin.sender == '#talis': return
    nick = match.group(2).lower()
    if not hasattr(self, 'seen'):
        return self.msg(origin.sender, '?')
    if self.seen.has_key(nick):
        channel, t = self.seen[nick]
        t = time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime(t))

        msg = "I last saw %s at %s on %s" % (nick, t, channel)
        self.msg(origin.sender, str(origin.nick) + ': ' + msg)
    else: self.msg(origin.sender, "Sorry, I haven't seen %s around." % nick)
f_seen.rule = (['seen'], r'(\S+)')
f_seen.rate = 45

@deprecated
def f_note(self, origin, match, args):
    def note(self, origin, match, args):
        if not hasattr(self.bot, 'seen'):
            self.bot.seen = {}
        if origin.sender.startswith('#'):
            # if origin.sender == '#inamidst': return
            self.seen[origin.nick.lower()] = (origin.sender, time.time())

        # if not hasattr(self, 'chanspeak'):
        #     self.chanspeak = {}
        # if (len(args) > 2) and args[2].startswith('#'):
        #     self.chanspeak[args[2]] = args[0]

    try: note(self, origin, match, args)
    except Exception, e: print e
f_note.rule = r'(.*)'
f_note.priority = 'low'
>>>>>>> 21a89fde8d1fc578e0de0190e24b8079c6d82da9

if __name__ == '__main__':
    print __doc__.strip()
