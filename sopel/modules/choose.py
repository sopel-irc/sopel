# coding=utf-8
"""
choose.py - Sopel Choice Module
Copyright 2010-2013, Dimitri "Tyrope" Molenaars, TyRope.nl
Copyright 2013, Ari Koivula, <ari@koivu.la>
Copyright 2018, Florian Strzelecki, <florian.strzelecki@gmail.com>
Copyright 2019, dgw, technobabbl.es
Licensed under the Eiffel Forum License 2.

https://sopel.chat
"""
from __future__ import unicode_literals, absolute_import, print_function, division

import random

from sopel import module


@module.commands("choice")
@module.commands("ch")
@module.commands("choose")
@module.priority("medium")
@module.example(".choose a, b, c", r'Your options: a, b, c. My choice: (a|b|c)', re=True)
@module.example(".choose a | b | c", r'Your options: a, b, c. My choice: (a|b|c)', re=True)
@module.example(".choose a,b,c", r'Your options: a, b, c. My choice: (a|b|c)', re=True)
@module.example(".choose a|b|c", r'Your options: a, b, c. My choice: (a|b|c)', re=True)
@module.example(".choose a b c", r'Your options: a, b, c. My choice: (a|b|c)', re=True)
@module.example(".choose a, b | just a",
                r'Your options: "a, b", just a. My choice: ((a, b)|(just a))',
                re=True)
@module.example(".choose a", 'Your options: a. My choice: a')
def choose(bot, trigger):
    """.choice option1|option2|option3 - Makes a difficult choice easy."""
    if not trigger.group(2):
        return bot.reply('I\'d choose an option, but you didn\'t give me any.')
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
    return bot.reply('Your options: %s. My choice: %s' % (display_options, pick))


if __name__ == "__main__":
    from sopel.test_tools import run_example_tests
    run_example_tests(__file__)
