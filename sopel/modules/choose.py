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
import unicodedata

from sopel import formatting, plugin

# Remove when dropping py2 support
try:
    str = unicode
except NameError:
    pass


def _format_safe(text):
    """Remove excess whitespace and terminate IRC formatting.

    :param str text: text to clean of whitespace
    :rtype: str
    :raises TypeError: if the passed ``text`` is not a string

    Our own take on ``str.strip()`` that skips stripping off IRC formatting
    and makes sure any formatting codes are closed if necessary.
    """
    if not isinstance(text, str):
        raise TypeError("A string is required.")
    elif not text:
        # unnecessary optimization
        return ''

    start = end = 0

    # strip left
    pos = 0
    while pos < len(text):
        is_whitespace = unicodedata.category(text[pos]) == 'Zs'
        is_non_printing = (
            text[pos] in formatting.CONTROL_NON_PRINTING and
            text[pos] not in formatting.CONTROL_FORMATTING
        )
        if not is_whitespace and not is_non_printing:
            start = pos
            break
        pos += 1

    # strip right
    pos = len(text) - 1
    while pos >= 0:
        is_whitespace = unicodedata.category(text[pos]) == 'Zs'
        is_non_printing = (
            text[pos] in formatting.CONTROL_NON_PRINTING and
            text[pos] not in formatting.CONTROL_FORMATTING
        )
        if not is_whitespace and not is_non_printing:
            end = pos + 1
            break
        pos -= 1

    # build the final string
    safe = text[start:end]
    if any(c in safe for c in formatting.CONTROL_FORMATTING):
        # if it includes IRC formatting, append reset character just in case
        safe += formatting.CONTROL_NORMAL

    return safe


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
    choices = [_format_safe(choice) for choice in choices]
    pick = random.choice(choices)

    # Always use a comma in the output
    display_options = ', '.join(
        choice if ',' not in choice else '"%s"' % choice
        for choice in choices
    )
    bot.reply('Your options: %s. My choice: %s' % (display_options, pick))
