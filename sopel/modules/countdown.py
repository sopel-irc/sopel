# coding=utf-8
"""
countdown.py - Sopel Countdown Plugin
Copyright 2011, Michael Yanovich, yanovich.net
Licensed under the Eiffel Forum License 2.

https://sopel.chat
"""
from __future__ import absolute_import, division, print_function, unicode_literals

import datetime

from sopel import plugin


@plugin.command('countdown')
@plugin.example('.countdown 2078 09 14')
@plugin.output_prefix('[countdown] ')
def generic_countdown(bot, trigger):
    """Displays a countdown to a given date."""
    text = trigger.group(2)
    if not text:
        bot.reply("Please use correct format: {}countdown 2012 12 21"
                  .format(bot.config.core.help_prefix))
        return plugin.NOLIMIT

    text = trigger.group(2).split()
    if text and (len(text) == 3 and text[0].isdigit() and
                 text[1].isdigit() and text[2].isdigit()):
        try:
            diff = (datetime.datetime(int(text[0]), int(text[1]),
                    int(text[2])) - datetime.datetime.today())
        except Exception:  # TODO: Be specific
            bot.reply("Please use correct format: {}countdown 2012 12 21"
                      .format(bot.config.core.help_prefix))
            return plugin.NOLIMIT
        bot.say(str(diff.days) + " days, " + str(diff.seconds // 3600) +
                " hours and " + str(diff.seconds % 3600 // 60) +
                " minutes until " + text[0] + " " + text[1] + " " + text[2])
    else:
        bot.reply("Please use correct format: {}countdown 2012 12 21"
                  .format(bot.config.core.help_prefix))
        return plugin.NOLIMIT
