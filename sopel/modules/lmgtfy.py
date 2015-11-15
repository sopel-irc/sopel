# coding=utf-8
"""
lmgtfy.py - Sopel Let me Google that for you module
Copyright 2013, Dimitri Molenaars http://tyrope.nl/
Licensed under the Eiffel Forum License 2.

http://sopel.chat/
"""
from __future__ import unicode_literals, absolute_import, print_function, division
from sopel.module import commands


@commands('lmgtfy', 'lmgify', 'gify', 'gtfy')
def googleit(bot, trigger):
    """Let me just... google that for you."""
    #No input
    if not trigger.group(2):
        return bot.say('http://google.com/')
    bot.say('http://lmgtfy.com/?q=' + trigger.group(2).replace(' ', '+'))
