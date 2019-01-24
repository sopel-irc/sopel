# coding=utf-8
"""
remind.py - Sopel Reminder Module
Copyright 2011, Sean B. Palmer, inamidst.com
Licensed under the Eiffel Forum License 2.

https://sopel.chat
"""
from __future__ import unicode_literals, absolute_import, print_function, division

import os
import re
import time
import threading
import collections
import codecs
from datetime import datetime
from sopel.module import commands, example, NOLIMIT
import sopel.tools
from sopel.tools.time import get_timezone, format_time

try:
    import pytz
except ImportError:
    pytz = None


def filename(self):
    name = self.nick + '-' + self.config.core.host + '.reminders.db'
    return os.path.join(self.config.core.homedir, name)


def load_database(name):
    data = {}
    if os.path.isfile(name):
        f = codecs.open(name, 'r', encoding='utf-8')
        for line in f:
            unixtime, channel, nick, message = line.split('\t')
            message = message.rstrip('\n')
            t = int(float(unixtime))  # WTFs going on here?
            reminder = (channel, nick, message)
            try:
                data[t].append(reminder)
            except KeyError:
                data[t] = [reminder]
        f.close()
    return data


def dump_database(name, data):
    f = codecs.open(name, 'w', encoding='utf-8')
    for unixtime, reminders in sopel.tools.iteritems(data):
        for channel, nick, message in reminders:
            f.write('%s\t%s\t%s\t%s\n' % (unixtime, channel, nick, message))
    f.close()


def setup(bot):
    bot.rfn = filename(bot)
    bot.rdb = load_database(bot.rfn)

    def monitor(bot):
        time.sleep(5)
        while True:
            now = int(time.time())
            unixtimes = [int(key) for key in bot.rdb]
            oldtimes = [t for t in unixtimes if t <= now]
            if oldtimes:
                for oldtime in oldtimes:
                    for (channel, nick, message) in bot.rdb[oldtime]:
                        if message:
                            bot.msg(channel, nick + ': ' + message)
                        else:
                            bot.msg(channel, nick + '!')
                    del bot.rdb[oldtime]
                dump_database(bot.rfn, bot.rdb)
            time.sleep(2.5)

    targs = (bot,)
    t = threading.Thread(target=monitor, args=targs)
    t.start()


scaling = collections.OrderedDict([
    ('years', 365.25 * 24 * 3600),
    ('year', 365.25 * 24 * 3600),
    ('yrs', 365.25 * 24 * 3600),
    ('y', 365.25 * 24 * 3600),

    ('months', 29.53059 * 24 * 3600),
    ('month', 29.53059 * 24 * 3600),
    ('mo', 29.53059 * 24 * 3600),

    ('weeks', 7 * 24 * 3600),
    ('week', 7 * 24 * 3600),
    ('wks', 7 * 24 * 3600),
    ('wk', 7 * 24 * 3600),
    ('w', 7 * 24 * 3600),

    ('days', 24 * 3600),
    ('day', 24 * 3600),
    ('d', 24 * 3600),

    ('hours', 3600),
    ('hour', 3600),
    ('hrs', 3600),
    ('hr', 3600),
    ('h', 3600),

    ('minutes', 60),
    ('minute', 60),
    ('mins', 60),
    ('min', 60),
    ('m', 60),

    ('seconds', 1),
    ('second', 1),
    ('secs', 1),
    ('sec', 1),
    ('s', 1),
])

periods = '|'.join(scaling.keys())


@commands('in')
@example('.in 3h45m Go to class')
def remind(bot, trigger):
    """Gives you a reminder in the given amount of time."""
    if not trigger.group(2):
        bot.say("Missing arguments for reminder command.")
        return NOLIMIT
    if trigger.group(3) and not trigger.group(4):
        bot.say("No message given for reminder.")
        return NOLIMIT
    duration = 0
    message = filter(None, re.split(r'(\d+(?:\.\d+)? ?(?:(?i)' + periods + ')) ?',
                                    trigger.group(2))[1:])
    reminder = ''
    stop = False
    for piece in message:
        grp = re.match(r'(\d+(?:\.\d+)?) ?(.*) ?', piece)
        if grp and not stop:
            length = float(grp.group(1))
            factor = scaling.get(grp.group(2).lower(), 60)
            duration += length * factor
        else:
            reminder = reminder + piece
            stop = True
    if duration == 0:
        return bot.reply("Sorry, didn't understand the input.")

    if duration % 1:
        duration = int(duration) + 1
    else:
        duration = int(duration)
    timezone = get_timezone(
        bot.db, bot.config, None, trigger.nick, trigger.sender)
    create_reminder(bot, trigger, duration, reminder, timezone)


@commands('at')
@example('.at 13:47 Do your homework!')
def at(bot, trigger):
    """
    Gives you a reminder at the given time. Takes `hh:mm:ssTimezone message`.
    Timezone is any timezone Sopel takes elsewhere; the best choices are those
    from the tzdb; a list of valid options is available at
    <https://sopel.chat/tz>. The seconds and timezone are optional.
    """
    if not trigger.group(2):
        bot.say("No arguments given for reminder command.")
        return NOLIMIT
    if trigger.group(3) and not trigger.group(4):
        bot.say("No message given for reminder.")
        return NOLIMIT
    regex = re.compile(r'(\d+):(\d+)(?::(\d+))?([^\s\d]+)? (.*)')
    match = regex.match(trigger.group(2))
    if not match:
        bot.reply("Sorry, but I didn't understand your input.")
        return NOLIMIT
    hour, minute, second, tz, message = match.groups()
    if not second:
        second = '0'

    if pytz:
        timezone = get_timezone(bot.db, bot.config, tz,
                                trigger.nick, trigger.sender)
        if not timezone:
            timezone = 'UTC'
        now = datetime.now(pytz.timezone(timezone))
        at_time = datetime(now.year, now.month, now.day,
                           int(hour), int(minute), int(second),
                           tzinfo=now.tzinfo)
        timediff = at_time - now
    else:
        if tz and tz.upper() != 'UTC':
            bot.reply("I don't have timezone support installed.")
            return NOLIMIT
        now = datetime.now()
        at_time = datetime(now.year, now.month, now.day,
                           int(hour), int(minute), int(second))
        timediff = at_time - now

    duration = timediff.seconds

    if duration < 0:
        duration += 86400
    create_reminder(bot, trigger, duration, message, timezone)


def create_reminder(bot, trigger, duration, message, tz):
    t = int(time.time()) + duration
    reminder = (trigger.sender, trigger.nick, message)
    try:
        bot.rdb[t].append(reminder)
    except KeyError:
        bot.rdb[t] = [reminder]

    dump_database(bot.rfn, bot.rdb)

    if duration >= 60:
        remind_at = datetime.utcfromtimestamp(t)
        timef = format_time(bot.db, bot.config, tz, trigger.nick,
                            trigger.sender, remind_at)

        bot.reply('Okay, will remind at %s' % timef)
    else:
        bot.reply('Okay, will remind in %s secs' % duration)
