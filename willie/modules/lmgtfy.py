# coding=utf8
"""
lmgtfy.py - Willie Let me Google that for you module
Copyright 2013, Dimitri Molenaars http://tyrope.nl/
Licensed under the Eiffel Forum License 2.

http://willie.dftba.net/
"""
from __future__ import unicode_literals
from willie.module import commands


@commands('lmgtfy', 'lmgify', 'gify', 'gtfy')
def googleit(bot, trigger):
    """Let me just... google that for you."""
    #No input
    if not trigger.group(2):
        return bot.say('http://google.com/')
    bot.say('http://lmgtfy.com/?q=' + trigger.group(2).replace(' ', '+'))
