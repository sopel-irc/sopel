# coding=utf-8
"""
uptime.py - Sopel Uptime Plugin
Copyright 2014, Fabian Neundorf
Licensed under the Eiffel Forum License 2.

https://sopel.chat
"""
from __future__ import absolute_import, division, print_function, unicode_literals

import datetime

from sopel import plugin


def setup(bot):
    if "start_time" not in bot.memory:
        bot.memory["start_time"] = datetime.datetime.utcnow()


@plugin.command('uptime')
@plugin.example('.uptime', user_help=True)
@plugin.output_prefix('[uptime] ')
def uptime(bot, trigger):
    """Return the uptime of Sopel."""
    delta = datetime.timedelta(seconds=round((datetime.datetime.utcnow() -
                                              bot.memory["start_time"])
                                             .total_seconds()))
    bot.say("I've been sitting here for {} and I keep going!".format(delta))
