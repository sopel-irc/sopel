# coding=utf-8
"""
rand.py - Rand Plugin
Copyright 2013, Ari Koivula, <ari@koivu.la>
Licensed under the Eiffel Forum License 2.

https://sopel.chat
"""
from __future__ import absolute_import, division, print_function, unicode_literals

import random
import sys

from sopel import plugin


@plugin.command('rand')
@plugin.example('.rand 2', r'random\(0, 2\): (0|1|2)', re=True, repeat=10)
@plugin.example('.rand -1 -1', 'random(-1, -1): -1')
@plugin.example('.rand', r'random\(0, \d+\): \d+', re=True)
@plugin.example('.rand 99 10', r'random\(10, 99\): \d\d', re=True, repeat=10)
@plugin.example('.rand 10 99', r'random\(10, 99\): \d\d', re=True, repeat=10)
@plugin.output_prefix('[rand] ')
def rand(bot, trigger):
    """Replies with a random number between first and second argument."""
    arg1 = trigger.group(3)
    arg2 = trigger.group(4)

    try:
        if arg2 is not None:
            low = int(arg1)
            high = int(arg2)
        elif arg1 is not None:
            low = 0
            high = int(arg1)
        else:
            low = 0
            high = sys.maxsize
    except (ValueError, TypeError):
        return bot.reply("Arguments must be integers.")

    if low > high:
        low, high = high, low

    number = random.randint(low, high)
    bot.say("random(%d, %d): %d" % (low, high, number))
