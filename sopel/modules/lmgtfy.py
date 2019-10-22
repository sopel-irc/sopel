# coding=utf-8
"""
lmgtfy.py - Sopel Let Me Google That For You Module
Copyright 2013, Dimitri Molenaars http://tyrope.nl/
Licensed under the Eiffel Forum License 2.

https://sopel.chat/
"""
from __future__ import unicode_literals, absolute_import, print_function, division

from sopel.module import commands, example
from sopel.tools.web import quote


@commands('lmgtfy', 'lmgify', 'gify', 'gtfy')
@example('.lmgtfy sopel', 'https://lmgtfy.com/?q=sopel')
@example('.lmgtfy sopel bot', 'https://lmgtfy.com/?q=sopel+bot', user_help=True)
@example('.lmgtfy', 'https://www.google.com/', user_help=True)
def googleit(bot, trigger):
    """Let me just… Google that for you."""
    if not trigger.group(2):  # No input
        return bot.say('https://www.google.com/')
    bot.say('https://lmgtfy.com/?q=' + quote(trigger.group(2).replace(' ', '+'), '+'))
