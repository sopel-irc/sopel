# -*- coding: utf8 -*-
"""
seen.py - Willie Seen Module
Copyright 2008, Sean B. Palmer, inamidst.com
Copyright © 2012, Elad Alfassa <elad@fedoraproject.org>
Licensed under the Eiffel Forum License 2.

http://willie.dftba.net
"""

import time
from willie.tools import Ddict

seen_dict=Ddict(dict)

def seen(willie, trigger):
    """Reports when and where the user was last seen."""
    if not trigger.group(2):
        willie.say(".seen <nick> - Reports when <nick> was last seen.")
        return
    nick = trigger.group(2).lower()
    if seen_dict.has_key(nick):
        timestamp = seen_dict[nick]['timestamp']
        channel = seen_dict[nick]['channel']
        message = seen_dict[nick]['message']
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime(timestamp))

        msg = "I last saw %s at %s on %s, saying %s" % (nick, timestamp, channel, message)
        willie.say(str(trigger.nick) + ': ' + msg)
    else:
        willie.say("Sorry, I haven't seen %s around." % nick)
seen.commands = ['seen']

def note(willie, trigger):
    if trigger.sender.startswith('#'):
        nick = trigger.nick.lower()
        seen_dict[nick]['timestamp'] = time.time()
        seen_dict[nick]['channel'] = trigger.sender
        seen_dict[nick]['message'] = trigger

note.rule = r'(.*)'
note.priority = 'low'

if __name__ == '__main__':
    print __doc__.strip()
