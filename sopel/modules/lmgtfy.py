# coding=utf-8
"""
lmgtfy.py - Sopel Let Me Google That For You Plugin
Copyright 2013, Dimitri Molenaars http://tyrope.nl/
Licensed under the Eiffel Forum License 2.

https://sopel.chat/
"""
from __future__ import absolute_import, division, print_function, unicode_literals

from sopel import plugin

try:
    from urllib.parse import urlencode
except ImportError:
    from urllib import urlencode


@plugin.command('lmgtfy', 'lmgify', 'gify', 'gtfy')
@plugin.example('.lmgtfy sopel', 'https://lmgtfy.com/?q=sopel')
@plugin.example('.lmgtfy sopel bot', 'https://lmgtfy.com/?q=sopel+bot', user_help=True)
@plugin.example('.lmgtfy', 'https://www.google.com/', user_help=True)
def googleit(bot, trigger):
    """Let me just… Google that for you."""
    if not trigger.group(2):  # No input
        return bot.say('https://www.google.com/')
    qs = urlencode({
        'q': trigger.group(2),
    })
    bot.say('https://lmgtfy.com/?%s' % qs)
