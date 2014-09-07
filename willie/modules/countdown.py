# coding=utf8
"""
countdown.py - Willie Countdown Module
Copyright 2011, Michael Yanovich, yanovich.net
Licensed under the Eiffel Forum License 2.

http://willie.dfbta.net
"""
from __future__ import unicode_literals
from willie.module import commands, NOLIMIT
import datetime


@commands('countdown')
def generic_countdown(bot, trigger):
    """
    .countdown <year> <month> <day> - displays a countdown to a given date.
    """
    text = trigger.group(2)
    if not text:
        bot.say("Please use correct format: .countdown 2012 12 21")
        return NOLIMIT
    text = trigger.group(2).split()
    if text and (text[0].isdigit() and text[1].isdigit() and text[2].isdigit()
            and len(text) == 3):
        diff = (datetime.datetime(int(text[0]), int(text[1]), int(text[2]))
                - datetime.datetime.today())
        bot.say(str(diff.days) + " days, " + str(diff.seconds / 60 / 60)
                   + " hours and "
                   + str(diff.seconds / 60 - diff.seconds / 60 / 60 * 60)
                   + " minutes until "
                   + text[0] + " " + text[1] + " " + text[2])
    else:
        bot.say("Please use correct format: .countdown 2012 12 21")
        return NOLIMIT
