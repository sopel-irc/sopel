# coding=utf8
"""
ping.py - Willie Ping Module
Author: Sean B. Palmer, inamidst.com
About: http://willie.dftba.net
"""
from __future__ import unicode_literals

import random
from willie.module import rule, priority, thread


@rule(r'(?i)(hi|hello|hey) $nickname[ \t]*$')
def hello(bot, trigger):
    if trigger.owner:
        greeting = random.choice(('Fuck off,', 'Screw you,', 'Go away'))
    else:
        greeting = random.choice(('Hi', 'Hey', 'Hello'))
    punctuation = random.choice(('', '!'))
    bot.say(greeting + ' ' + trigger.nick + punctuation)


@rule(r'(?i)(Fuck|Screw) you, $nickname[ \t]*$')
def rude(bot, trigger):
    bot.say('Watch your mouth, ' + trigger.nick + ', or I\'ll tell your mother!')


@rule('$nickname!')
@priority('high')
@thread(False)
def interjection(bot, trigger):
    bot.say(trigger.nick + '!')
