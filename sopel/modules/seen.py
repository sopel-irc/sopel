# coding=utf-8
"""
seen.py - Sopel Seen Plugin
Copyright 2008, Sean B. Palmer, inamidst.com
Copyright © 2012, Elad Alfassa <elad@fedoraproject.org>
Copyright 2019, Sopel contributors
Licensed under the Eiffel Forum License 2.

https://sopel.chat
"""
from __future__ import absolute_import, division, print_function, unicode_literals

import datetime
import time

from sopel import plugin, tools
from sopel.tools.time import seconds_to_human


@plugin.command('seen')
@plugin.output_prefix('[seen] ')
def seen(bot, trigger):
    """Reports when and where the user was last seen."""
    if not trigger.group(2):
        bot.reply(
            "Use `%sseen <nick>` to know when <nick> was last seen."
            % bot.settings.core.help_prefix)
        return

    nick = trigger.group(2).strip()
    if nick == bot.nick:
        bot.reply("I'm right here!")
        return

    timestamp = bot.db.get_nick_value(nick, 'seen_timestamp')
    if not timestamp:
        bot.reply("Sorry, I haven't seen {nick} around.".format(nick=nick))
        return

    channel = bot.db.get_nick_value(nick, 'seen_channel')
    message = bot.db.get_nick_value(nick, 'seen_message')
    action = bot.db.get_nick_value(nick, 'seen_action')

    saw = datetime.datetime.utcfromtimestamp(timestamp)
    delta = seconds_to_human((trigger.time - saw).total_seconds())

    msg = "I last saw " + nick
    if tools.Identifier(channel) == trigger.sender:
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
    bot.say(msg)


@plugin.thread(False)
@plugin.rule('(.*)')
@plugin.priority('low')
@plugin.unblockable
@plugin.require_chanmsg
def note(bot, trigger):
    nick = trigger.nick
    bot.db.set_nick_value(nick, 'seen_timestamp', time.time())
    bot.db.set_nick_value(nick, 'seen_channel', trigger.sender)
    bot.db.set_nick_value(nick, 'seen_message', trigger)
    bot.db.set_nick_value(nick, 'seen_action', trigger.ctcp is not None)
