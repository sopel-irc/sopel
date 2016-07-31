# coding=utf-8
"""
karma.py - Sopel karma module
Copyright © 2015-2016, Alex Newman <anewman@redhat.com>
Copyright © 2016, Sachin Patil <psachin@redhat.com>
Licensed under the Eiffel Forum License 2.

This module is based on https://github.com/anewmanRH/sopel-karma
"""
from __future__ import (unicode_literals, absolute_import,
                        print_function, division)
import re

from sopel.module import (rule, commands, example,
                          require_privilege, OP)
from sopel.tools import Identifier
from sopel.formatting import bold as bold_text


@rule(r'([\S]+?)\+\+')
def promote_karma(bot, trigger):
    """
    Update karma status for specify IRC user if get '++' message.
    """
    if trigger.is_privmsg:
        return bot.say('People like it when you tell them good things.')
    for nick in re.finditer(r'([\S]+?)\+\+', trigger):
        if (bot.db.get_nick_id(Identifier(nick.group(1))) ==
            bot.db.get_nick_id(Identifier(trigger.nick))):
            return bot.say('You may not give yourself karma!')
        current_karma = bot.db.get_nick_value(nick.group(1), 'karma')
        if not current_karma:
            current_karma = 0
        else:
            current_karma = int(current_karma)
        current_karma += 1

        bot.db.set_nick_value(nick.group(1), 'karma', current_karma)
        bot.say("{} has {} points of karma".format(
            nick.group(1), bold_text(str(current_karma))))


@rule(r'([\S]+?)\-\-')
def demote_karma(bot, trigger):
    """
    Update karma status for specify IRC user if get '--' message.
    """
    # TODO: Implement re.finditer()
    if trigger.is_privmsg:
        return bot.say('Say it to their face!')
    if (bot.db.get_nick_id(Identifier(trigger.group(1))) ==
            bot.db.get_nick_id(Identifier(trigger.nick))):
        return bot.say('You may not reduce your own karma!')
    current_karma = bot.db.get_nick_value(trigger.group(1), 'karma')
    if not current_karma:
        current_karma = 0
    else:
        current_karma = int(current_karma)
    current_karma -= 1

    bot.db.set_nick_value(trigger.group(1), 'karma', current_karma)
    bot.say("{} has {} points of karma".format(
        trigger.group(1), bold_text(str(current_karma))))


@rule(r'([\S]+?)\=\=')
def show_karma(bot, trigger):
    """
    Update karma status for specify IRC user if get '--' message.
    """
    current_karma = bot.db.get_nick_value(trigger.group(1), 'karma')
    if not current_karma:
        current_karma = 0
    else:
        current_karma = int(current_karma)
    bot.say("{} has {} points of karma".format(
        trigger.group(1), bold_text(str(current_karma))))


@commands('karma')
@example('.karma nick')
def karma(bot, trigger):
    """
    Command to show the karma status for specify IRC user.
    """
    nick = trigger.nick
    if trigger.group(2):
        nick = trigger.group(2).strip().split()[0]

    _karma = bot.db.get_nick_value(nick, 'karma')
    if not _karma:
        _karma = '0'
    bot.say("{} has {} points of karma".format(nick, _karma))


@require_privilege(OP)
@commands('setkarma')
# @example('.setkarma nick 99')
def set_karma(bot, trigger):
    """
    Set karma status for specific IRC user.
    """

    if trigger.group(2):
        nick = trigger.group(2).strip().split()[0]
        value = int(trigger.group(2).strip().split()[1])

    bot.db.set_nick_value(nick, 'karma', value)
    bot.say("%s == %s" % (nick, value))


@commands('topkarma')
@example('.topkarma 3')
def top_karma(bot, trigger):
    """
    Show karma status for the top n number of IRC users.
    """
    try:
        top_limit = int(trigger.group(2).strip())
    except (ValueError, AttributeError):
        top_limit = 5

    query = "SELECT DISTINCT slug, value FROM nick_values NATURAL JOIN nicknames \
        WHERE key = 'karma' ORDER BY value DESC LIMIT ?"
    karmalist = bot.db.execute(query, str(top_limit)).fetchall()
    bot.say("And the award goes to..")
    if karmalist:
        for user in karmalist:
            bot.say("{}({} points of karma)".format(
                user[0], bold_text(str(user[1]))))
            return
    bot.say("No one is eligible :(")
