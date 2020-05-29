# coding=utf-8
"""
ping.py - Sopel Ping Module
Copyright 2008 (?), Sean B. Palmer, inamidst.com

https://sopel.chat
"""
from __future__ import absolute_import, division, print_function, unicode_literals

import random

from sopel.module import commands, priority, rule, thread


@rule(r'(?i)(hi|hello|hey),? $nickname[ \t]*$')
def hello(bot, trigger):
    greeting = random.choice(('Hi', 'Hey', 'Hello'))
    punctuation = random.choice(('', '.', '…', '!'))
    bot.say(greeting + ' ' + trigger.nick + punctuation)


@rule(r'(?i)(Fuck|Screw) you,? $nickname[ \t]*$')
def rude(bot, trigger):
    bot.say('Watch your mouth, ' + trigger.nick + ', or I\'ll tell your mother!')


@rule('$nickname!')
@priority('high')
@thread(False)
def interjection(bot, trigger):
    bot.say(trigger.nick + '!')


@commands('ping')
def ping(bot, trigger):
    """Reply to ping command."""
    bot.reply('Pong!')
