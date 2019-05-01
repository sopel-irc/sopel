# coding=utf-8
"""
remind.py - Sopel Reminder Module
Copyright 2011, Sean B. Palmer, inamidst.com
Licensed under the Eiffel Forum License 2.

https://sopel.chat
"""
from __future__ import unicode_literals, absolute_import, print_function, division

import codecs
import collections
from datetime import datetime
import os
import re
import time
import threading

import pytz

from sopel import tools, module
from sopel.tools.time import get_timezone, format_time


def get_filename(bot):
    """Get the remind database's filename

    :param bot: instance of Sopel
    :type bot: :class:`sopel.bot.Sopel`
    :return: the remind database's filename
    :rtype: str

    The remind database filename is based on the bot's nick and its
    configured ``core.host``, and it is located in the ``bot``'s ``homedir``.
    """
    name = bot.nick + '-' + bot.config.core.host + '.reminders.db'
    return os.path.join(bot.config.core.homedir, name)


def load_database(filename):
    """Load the remind database from a file

    :param str filename: absolute path to the remind database file
    :return: a :class:`dict` of reminders stored by timestamp
    :rtype: dict

    The remind database is a plain text file (utf-8 encoded) with tab-separated
    columns of data: time, channel, nick, and message. This function reads this
    file and outputs a :class:`dict` where keys are the timestamps of the
    reminders, and values are list of 3-value tuple of reminder data:
    ``(channel, nick, message)``.

    .. note::

        This function ignores microseconds from the timestamp, if any, meaning
        that ``523549800.245`` will be read as ``523549800``.

    .. note::

        If ``filename`` is not an existing file, this function returns an
        empty :class:`dict`.

    """
    if not os.path.isfile(filename):
        # no file to read
        return {}

    data = {}
    with codecs.open(filename, 'r', encoding='utf-8') as database:
        for line in database:
            unixtime, channel, nick, message = line.split('\t', 3)
            message = message.rstrip('\n')
            timestamp = int(float(unixtime))  # ignore microseconds
            reminder = (channel, nick, message)
            try:
                data[timestamp].append(reminder)
            except KeyError:
                data[timestamp] = [reminder]
    return data


def dump_database(filename, data):
    """Dump the remind database into a file

    :param str filename: absolute path to the remind database file
    :param dict data: remind database to dump

    The remind database is dumped into a plain text file (utf-8 encoded) as
    tab-separated columns of data: unixtime, channel, nick, and message.

    If the file does not exist, it is created.
    """
    with codecs.open(filename, 'w', encoding='utf-8') as database:
        for unixtime, reminders in tools.iteritems(data):
            for channel, nick, message in reminders:
                line = '%s\t%s\t%s\t%s\n' % (unixtime, channel, nick, message)
                database.write(line)


def create_reminder(bot, trigger, duration, message, timezone):
    """Create a reminder into the ``bot``'s database and reply to the sender"""
    timestamp = int(time.time()) + duration
    reminder = (trigger.sender, trigger.nick, message)
    try:
        bot.rdb[timestamp].append(reminder)
    except KeyError:
        bot.rdb[timestamp] = [reminder]

    dump_database(bot.rfn, bot.rdb)

    if duration >= 60:
        human_time = format_time(
            bot.db,
            bot.config,
            timezone,
            trigger.nick,
            trigger.sender,
            datetime.utcfromtimestamp(timestamp))
        bot.reply('Okay, will remind at %s' % human_time)
    else:
        bot.reply('Okay, will remind in %s secs' % duration)


def setup(bot):
    """Setup the remind database and the remind monitoring"""
    bot.rfn = get_filename(bot)
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
    monitoring = threading.Thread(target=monitor, args=targs)
    monitoring.start()


SCALING = collections.OrderedDict([
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

PERIODS = '|'.join(SCALING.keys())


@module.commands('in')
@module.example('.in 3h45m Go to class')
def remind_in(bot, trigger):
    """Gives you a reminder in the given amount of time."""
    if not trigger.group(2):
        bot.say("Missing arguments for reminder command.")
        return module.NOLIMIT
    if trigger.group(3) and not trigger.group(4):
        bot.say("No message given for reminder.")
        return module.NOLIMIT
    duration = 0
    message = filter(None, re.split(r'(\d+(?:\.\d+)? ?(?:(?i)' + PERIODS + ')) ?',
                                    trigger.group(2))[1:])
    reminder = ''
    stop = False
    for piece in message:
        grp = re.match(r'(\d+(?:\.\d+)?) ?(.*) ?', piece)
        if grp and not stop:
            length = float(grp.group(1))
            factor = SCALING.get(grp.group(2).lower(), 60)
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


REGEX_AT = re.compile(r'(\d+):(\d+)(?::(\d+))?([^\s\d]+)? (.*)')


@module.commands('at')
@module.example('.at 13:47 Do your homework!')
def remind_at(bot, trigger):
    """
    Gives you a reminder at the given time. Takes `hh:mm:ssTimezone message`.
    Timezone is any timezone Sopel takes elsewhere; the best choices are those
    from the tzdb; a list of valid options is available at
    <https://sopel.chat/tz>. The seconds and timezone are optional.
    """
    if not trigger.group(2):
        bot.say("No arguments given for reminder command.")
        return module.NOLIMIT
    if trigger.group(3) and not trigger.group(4):
        bot.say("No message given for reminder.")
        return module.NOLIMIT
    match = REGEX_AT.match(trigger.group(2))
    if not match:
        bot.reply("Sorry, but I didn't understand your input.")
        return module.NOLIMIT
    hour, minute, second, timezone, message = match.groups()
    if not second:
        second = '0'

    timezone = get_timezone(bot.db, bot.config, timezone,
                            trigger.nick, trigger.sender)
    if not timezone:
        timezone = 'UTC'

    now = datetime.now(pytz.timezone(timezone))
    at_time = datetime(now.year, now.month, now.day,
                       int(hour), int(minute), int(second),
                       tzinfo=now.tzinfo)
    timediff = at_time - now
    duration = timediff.seconds

    if duration < 0:
        duration += 86400
    create_reminder(bot, trigger, duration, message, timezone)
