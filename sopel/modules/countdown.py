# coding=utf-8
"""
countdown.py - Sopel Countdown Module
Copyright 2011, Michael Yanovich, yanovich.net
Licensed under the Eiffel Forum License 2.

https://sopel.chat
"""
from __future__ import unicode_literals, absolute_import, print_function, division

import datetime

from sopel.module import commands, NOLIMIT


@commands('countdown')
def generic_countdown(bot, trigger):
    """.countdown <year> <month> <day> - displays a countdown to a given date."""
    text = trigger.group(2)
    if not text:
        bot.say("Please use correct format: {}countdown 2012 12 21"
                .format(bot.config.core.help_prefix))
        return NOLIMIT
    text = trigger.group(2).split()
    if text and (len(text) == 3 and text[0].isdigit() and
                 text[1].isdigit() and text[2].isdigit()):
        try:
            diff = (datetime.datetime(int(text[0]), int(text[1]),
                    int(text[2])) - datetime.datetime.today())
        except Exception:  # TODO: Be specific
            bot.say("Please use correct format: {}countdown 2012 12 21"
                    .format(bot.config.core.help_prefix))
            return NOLIMIT
        bot.say(str(diff.days) + " days, " + str(diff.seconds // 3600) +
                " hours and " + str(diff.seconds % 3600 // 60) +
                " minutes until " + text[0] + " " + text[1] + " " + text[2])
    else:
        bot.say("Please use correct format: {}countdown 2012 12 21"
                .format(bot.config.core.help_prefix))
        return NOLIMIT
