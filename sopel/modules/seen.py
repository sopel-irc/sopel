# coding=utf-8
"""
seen.py - Sopel Seen Module
Copyright 2008, Sean B. Palmer, inamidst.com
Copyright © 2012, Elad Alfassa <elad@fedoraproject.org>
Copyright 2019, Sopel contributors
Licensed under the Eiffel Forum License 2.

https://sopel.chat
"""
from __future__ import unicode_literals, absolute_import, print_function, division

import datetime
import time

from sopel.module import commands, rule, priority, thread, unblockable
from sopel.tools import Identifier
from sopel.tools.time import seconds_to_human


@commands('seen')
def seen(bot, trigger):
    """Reports when and where the user was last seen."""
    if not trigger.group(2):
        bot.say(".seen <nick> - Reports when <nick> was last seen.")
        return
    nick = trigger.group(2).strip()
    if nick == bot.nick:
        bot.reply("I'm right here!")
        return
    timestamp = bot.db.get_nick_value(nick, 'seen_timestamp')
    if timestamp:
        channel = bot.db.get_nick_value(nick, 'seen_channel')
        message = bot.db.get_nick_value(nick, 'seen_message')
        action = bot.db.get_nick_value(nick, 'seen_action')

        saw = datetime.datetime.utcfromtimestamp(timestamp)
        delta = seconds_to_human((trigger.time - saw).total_seconds())

        msg = "I last saw " + nick
        if Identifier(channel) == trigger.sender:
            if action:
                msg += " in here {since}, doing: {nick} {action}".format(
                    since=delta,
                    nick=nick,
                    action=message)
            else:
                msg += " in here {since}, saying: {message}".format(
                    since=delta,
                    message=message)
        else:
            msg += " in another channel {since}.".format(since=delta)
        bot.reply(msg)
    else:
        bot.say("Sorry, I haven't seen {nick} around.".format(nick=nick))


@thread(False)
@rule('(.*)')
@priority('low')
@unblockable
def note(bot, trigger):
    if not trigger.is_privmsg:
        bot.db.set_nick_value(trigger.nick, 'seen_timestamp', time.time())
        bot.db.set_nick_value(trigger.nick, 'seen_channel', trigger.sender)
        bot.db.set_nick_value(trigger.nick, 'seen_message', trigger)
        bot.db.set_nick_value(trigger.nick, 'seen_action', 'intent' in trigger.tags)
