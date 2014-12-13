# coding=utf8
"""
seen.py - Willie Seen Module
Copyright 2008, Sean B. Palmer, inamidst.com
Copyright © 2012, Elad Alfassa <elad@fedoraproject.org>
Licensed under the Eiffel Forum License 2.

http://willie.dftba.net
"""
from __future__ import unicode_literals

import time
import datetime
from willie.tools import Ddict, Identifier, get_timezone, format_time
from willie.module import commands, rule, priority

seen_dict = Ddict(dict)


@commands('seen')
def seen(bot, trigger):
    """Reports when and where the user was last seen."""
    if not trigger.group(2):
        bot.say(".seen <nick> - Reports when <nick> was last seen.")
        return
    nick = Identifier(trigger.group(2).strip())
    if nick in seen_dict:
        timestamp = seen_dict[nick]['timestamp']
        channel = seen_dict[nick]['channel']
        message = seen_dict[nick]['message']

        tz = get_timezone(bot.db, bot.config, None, trigger.nick,
                          trigger.sender)
        saw = datetime.datetime.utcfromtimestamp(timestamp)
        timestamp = format_time(bot.db, bot.config, tz, trigger.nick,
                                trigger.sender, saw)

        msg = "I last saw %s at %s on %s, saying %s" % (nick, timestamp, channel, message)
        bot.say(str(trigger.nick) + ': ' + msg)
    else:
        bot.say("Sorry, I haven't seen %s around." % nick)


@rule('(.*)')
@priority('low')
def note(bot, trigger):
    if not trigger.is_privmsg:
        nick = Identifier(trigger.nick)
        seen_dict[nick]['timestamp'] = time.time()
        seen_dict[nick]['channel'] = trigger.sender
        seen_dict[nick]['message'] = trigger
