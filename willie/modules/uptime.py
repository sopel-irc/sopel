# coding=utf8
"""
uptime.py - Uptime module
Copyright 2014, Fabian Neundorf
Licensed under the Eiffel Forum License 2.

http://willie.dftba.net
"""
from __future__ import unicode_literals

from willie.module import commands
import datetime


def setup(bot):
    if "uptime" not in bot.memory:
        bot.memory["uptime"] = datetime.datetime.utcnow()


@commands('uptime')
def uptime(bot, trigger):
    """.uptime - Returns the uptime of Willie."""
    delta = datetime.timedelta(seconds=round((datetime.datetime.utcnow() -
                                              bot.memory["uptime"])
                                             .total_seconds()))
    bot.say("I've been sitting here for {} and I keep "
            "going!".format(delta))
