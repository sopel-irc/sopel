# coding=utf-8
"""
lmgtfy.py - Sopel Let me Google that for you module
Copyright 2013, Dimitri Molenaars http://tyrope.nl/
Licensed under the Eiffel Forum License 2.

https://sopel.chat/
"""
from __future__ import unicode_literals, absolute_import, print_function, division

from sopel.module import commands, example
from sopel.web import quote


@commands('lmgtfy', 'lmgify', 'gify', 'gtfy')
@example('.lmgtfy sopel', 'https://lmgtfy.com/?q=sopel')
@example('.lmgtfy sopel bot', 'https://lmgtfy.com/?q=sopel+bot')
@example('.lmgtfy', 'https://www.google.com/')
def googleit(bot, trigger):
    """Let me just... google that for you."""
    # No input
    if not trigger.group(2):
        return bot.say('https://www.google.com/')
    bot.say('https://lmgtfy.com/?q=' + quote(trigger.group(2).replace(' ', '+'), '+'))
