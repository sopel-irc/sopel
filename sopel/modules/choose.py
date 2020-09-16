# coding=utf-8
"""
choose.py - Sopel Choice Plugin
Copyright 2010-2013, Dimitri "Tyrope" Molenaars, TyRope.nl
Copyright 2013, Ari Koivula, <ari@koivu.la>
Copyright 2018, Florian Strzelecki, <florian.strzelecki@gmail.com>
Copyright 2019, dgw, technobabbl.es
Licensed under the Eiffel Forum License 2.

https://sopel.chat
"""
from __future__ import absolute_import, division, print_function, unicode_literals

import random

from sopel import plugin


@plugin.command('choose', 'choice', 'ch')
@plugin.priority("medium")
@plugin.example(".choose a, b, c", r'Your options: a, b, c. My choice: (a|b|c)', re=True)
@plugin.example(".choose a | b | c", r'Your options: a, b, c. My choice: (a|b|c)', re=True)
@plugin.example(".choose a,b,c", r'Your options: a, b, c. My choice: (a|b|c)', re=True)
@plugin.example(".choose a|b|c", r'Your options: a, b, c. My choice: (a|b|c)', re=True)
@plugin.example(".choose a b c", r'Your options: a, b, c. My choice: (a|b|c)', re=True)
@plugin.example(".choose a, b | just a",
                r'Your options: "a, b", just a. My choice: ((a, b)|(just a))',
                re=True)
@plugin.example(".choose a", 'Your options: a. My choice: a')
@plugin.example(".choose a | b | c", user_help=True)
@plugin.example(".choose a, b, c", user_help=True)
def choose(bot, trigger):
    """Makes a difficult choice easy."""
    if not trigger.group(2):
        bot.reply("I'd choose an option, but you didn't give me any.")
        return

    choices = [trigger.group(2)]
    for delim in '|\\/, ':
        choices = trigger.group(2).split(delim)
        if len(choices) > 1:
            break
    choices = [choice.strip() for choice in choices]
    pick = random.choice(choices)

    # Always use a comma in the output
    display_options = ', '.join(
        choice if ',' not in choice else '"%s"' % choice
        for choice in choices
    )
    bot.reply('Your options: %s. My choice: %s' % (display_options, pick))
