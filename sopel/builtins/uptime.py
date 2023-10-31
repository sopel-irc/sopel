"""
uptime.py - Sopel Uptime Plugin
Copyright 2014, Fabian Neundorf
Licensed under the Eiffel Forum License 2.

https://sopel.chat
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sopel import plugin


def setup(bot):
    if "start_time" not in bot.memory:
        bot.memory["start_time"] = datetime.now(timezone.utc)


@plugin.command('uptime')
@plugin.example('.uptime', user_help=True)
@plugin.output_prefix('[uptime] ')
def uptime(bot, trigger):
    """Return the uptime of Sopel."""
    delta = timedelta(seconds=round((datetime.now(timezone.utc) -
                                    bot.memory["start_time"])
                                    .total_seconds()))
    bot.say("I've been sitting here for {} and I keep going!".format(delta))
