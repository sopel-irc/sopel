# coding=utf-8
"""
uptime.py - Sopel Uptime Module
Copyright 2014, Fabian Neundorf
Licensed under the Eiffel Forum License 2.

https://sopel.chat
"""
from __future__ import unicode_literals, absolute_import, print_function, division

import datetime

from sopel.module import commands


def setup(bot):
    if "start_time" not in bot.memory:
        bot.memory["start_time"] = datetime.datetime.utcnow()


@commands('uptime')
def uptime(bot, trigger):
    """.uptime - Returns the uptime of Sopel."""
    delta = datetime.timedelta(seconds=round((datetime.datetime.utcnow() -
                                              bot.memory["start_time"])
                                             .total_seconds()))
    bot.say("I've been sitting here for {} and I keep going!".format(delta))
