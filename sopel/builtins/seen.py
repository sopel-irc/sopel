"""
seen.py - Sopel Seen Plugin
Copyright 2008, Sean B. Palmer, inamidst.com
Copyright © 2012, Elad Alfassa <elad@fedoraproject.org>
Copyright 2019, Sopel contributors
Licensed under the Eiffel Forum License 2.

https://sopel.chat
"""
from __future__ import annotations

import logging

from sqlalchemy.exc import SQLAlchemyError

from sopel import plugin
from sopel.tools.time import seconds_to_human


logger = logging.getLogger(__name__)


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

    saw = bot.db.get_nick_value(nick, 'seen_timestamp')
    if not saw:
        bot.reply("Sorry, I haven't seen {nick} around.".format(nick=nick))
        return

    channel = bot.db.get_nick_value(nick, 'seen_channel')
    message = bot.db.get_nick_value(nick, 'seen_message')
    action = bot.db.get_nick_value(nick, 'seen_action')

    # as of Sopel 8, trigger.time is an aware datetime
    delta = seconds_to_human(trigger.time.timestamp() - saw)

    msg = "I last saw " + nick
    if bot.make_identifier(channel) == trigger.sender:
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
@plugin.priority(plugin.Priority.LOW)
@plugin.unblockable
@plugin.require_chanmsg
def note(bot, trigger):
    nick = trigger.nick
    try:
        # as of Sopel 8, `trigger.time` is Aware, meaning we should store its value
        # for timezone safety when comparing it later
        bot.db.set_nick_value(nick, 'seen_timestamp', trigger.time.timestamp())
        bot.db.set_nick_value(nick, 'seen_channel', trigger.sender)
        bot.db.set_nick_value(nick, 'seen_message', trigger)
        bot.db.set_nick_value(nick, 'seen_action', trigger.ctcp is not None)
    except SQLAlchemyError as error:
        logger.error("Unable to save seen, database error: %s" % error)
