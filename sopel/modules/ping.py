"""
ping.py - Sopel Ping Plugin
Copyright 2008 (?), Sean B. Palmer, inamidst.com

https://sopel.chat
"""
from __future__ import annotations

import random

from sopel import plugin


@plugin.rule(r'(?i)(hi|hello|hey),? $nickname[ \t]*$')
def hello(bot, trigger):
    greeting = random.choice(('Hi', 'Hey', 'Hello'))
    punctuation = random.choice(('', '.', '…', '!'))
    bot.say(greeting + ' ' + trigger.nick + punctuation)


@plugin.rule(r'(?i)(Fuck|Screw) you,? $nickname[ \t]*$')
def rude(bot, trigger):
    message = "Watch your mouth, {nick} or I'll tell your mother!".format(
        nick=trigger.nick,
    )
    bot.say(message)


@plugin.rule('$nickname!')
@plugin.priority('high')
@plugin.thread(False)
def interjection(bot, trigger):
    bot.say(trigger.nick + '!')


@plugin.command('ping')
def ping(bot, trigger):
    """Reply to ping command."""
    bot.reply('Pong!')
