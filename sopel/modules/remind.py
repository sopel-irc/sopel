# coding=utf-8
"""
remind.py - Sopel Reminder Plugin
Copyright 2011, Sean B. Palmer, inamidst.com
Copyright 2019, dgw, technobabbl.es
Licensed under the Eiffel Forum License 2.

https://sopel.chat
"""
from __future__ import absolute_import, division, print_function, unicode_literals

import collections
from datetime import datetime
import io  # don't use `codecs` for loading the DB; it will split lines on some IRC formatting
import logging
import os
import re
import time

import pytz

from sopel import plugin, tools
from sopel.tools.time import format_time, get_timezone, validate_timezone


LOGGER = logging.getLogger(__name__)


def get_filename(bot):
    """Get the remind database's filename

    :param bot: instance of Sopel
    :type bot: :class:`sopel.bot.Sopel`
    :return: the remind database's filename
    :rtype: str

    The remind database filename is based on the bot's nick and its
    configured ``core.host``, and it is located in the ``bot``'s ``homedir``.
    """
    name = bot.config.basename + '.reminders.db'
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
    with io.open(filename, 'r', encoding='utf-8') as database:
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
    with io.open(filename, 'w', encoding='utf-8') as database:
        for unixtime, reminders in tools.iteritems(data):
            for channel, nick, message in reminders:
                line = '%s\t%s\t%s\t%s\n' % (unixtime, channel, nick, message)
                database.write(line)


def create_reminder(bot, trigger, duration, message):
    """Create a reminder into the ``bot``'s database and reply to the sender

    :param bot: the bot's instance
    :type bot: :class:`~sopel.bot.SopelWrapper`
    :param trigger: the object that triggered the call
    :type trigger: :class:`~sopel.trigger.Trigger`
    :param int duration: duration from now, in seconds, until ``message``
                         must be reminded
    :param str message: message to be reminded
    :return: the reminder's timestamp
    :rtype: :class:`int`
    """
    timestamp = int(time.time()) + duration
    reminder = (trigger.sender, trigger.nick, message)
    try:
        bot.rdb[timestamp].append(reminder)
    except KeyError:
        bot.rdb[timestamp] = [reminder]

    dump_database(bot.rfn, bot.rdb)
    return timestamp


def setup(bot):
    """Load the remind database"""
    bot.rfn = get_filename(bot)

    # Pre-7.0 migration logic. Remove in 8.0 or 9.0.
    old = bot.nick + '-' + bot.config.core.host + '.reminders.db'
    old = os.path.join(bot.config.core.homedir, old)
    if os.path.isfile(old):
        LOGGER.info("Attempting to migrate old 'remind' database {}..."
                    .format(old))
        try:
            os.rename(old, bot.rfn)
        except OSError:
            LOGGER.error("Migration failed!")
            LOGGER.error("Old filename: {}".format(old))
            LOGGER.error("New filename: {}".format(bot.rfn))
            LOGGER.error(
                "See https://sopel.chat/usage/installing/upgrading-to-sopel-7/#reminder-db-migration")
        else:
            LOGGER.info("Migration finished!")
    # End migration logic

    bot.rdb = load_database(bot.rfn)


def shutdown(bot):
    """Dump the remind database before shutdown"""
    dump_database(bot.rfn, bot.rdb)
    bot.rdb = {}
    del bot.rfn
    del bot.rdb


@plugin.interval(2.5)
def remind_monitoring(bot):
    """Check for reminder"""
    now = int(time.time())
    unixtimes = [int(key) for key in bot.rdb]
    oldtimes = [t for t in unixtimes if t <= now]
    if oldtimes:
        for oldtime in oldtimes:
            for (channel, nick, message) in bot.rdb[oldtime]:
                if message:
                    bot.say(nick + ': ' + message, channel)
                else:
                    bot.say(nick + '!', channel)
            del bot.rdb[oldtime]
        dump_database(bot.rfn, bot.rdb)


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


@plugin.command('in')
@plugin.example('.in 3h45m Go to class')
def remind_in(bot, trigger):
    """Gives you a reminder in the given amount of time."""
    if not trigger.group(2):
        bot.reply("Missing arguments for reminder command.")
        return plugin.NOLIMIT
    if trigger.group(3) and not trigger.group(4):
        bot.reply("No message given for reminder.")
        return plugin.NOLIMIT
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
        bot.reply("Sorry, didn't understand the input.")
        return plugin.NOLIMIT

    if duration % 1:
        duration = int(duration) + 1
    else:
        duration = int(duration)
    timezone = get_timezone(
        bot.db, bot.config, None, trigger.nick, trigger.sender)
    timestamp = create_reminder(bot, trigger, duration, reminder)

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


REGEX_AT = re.compile(
    # hours:minutes
    r'(?P<hours>\d+):(?P<minutes>\d+)'
    # optional seconds
    r'(?::(?P<seconds>\d+))?'
    # optional timezone
    r'(?P<tz>[^\s\d]+)?'
    # optional date (start)
    r'(?:\s+'
    # - date 1 (at least one digit)
    r'(?P<date1>\d{1,4})'
    # - separator (one character)
    r'(?P<sep>[./-])'
    # - date 2 (at least one digit)
    r'(?P<date2>\d{1,4})'
    # - optional sep + date 3 (at least one digit)
    r'(?:(?P=sep)(?P<date3>\d{1,4}))?'
    r')?'  # (end)
    # at least one space + message
    r'\s+(?P<message>.*)'
)


class TimeReminder(object):
    """Time reminder for the ``at`` command"""
    def __init__(self,
                 hour,
                 minute,
                 second,
                 timezone,
                 date1,
                 date2,
                 date3,
                 message):
        self.hour = hour
        self.minute = minute
        self.second = second
        self.timezone = pytz.timezone(timezone)
        self.message = message

        year = None
        month = None
        day = None

        if date1 and date2 and date3:
            if len(date1) == 4:
                # YYYY-mm-dd
                year = int(date1)
                month = int(date2)
                day = int(date3)
            else:
                # dd-mm-YYYY or dd/mm/YY
                year = int(date3)
                month = int(date2)
                day = int(date1)
        elif date1 and date2:
            if len(date1) == 4:
                # YYYY-mm
                year = int(date1)
                month = int(date2)
            elif len(date2) == 4:
                # mm-YYYY
                year = int(date2)
                month = int(date1)
            else:
                # dd/mm
                month = int(date2)
                day = int(date1)

        self.year = year
        self.month = month
        self.day = day

    def __eq__(self, other):
        return all(
            getattr(self, attr) == getattr(other, attr, None)
            for attr in [
                'hour',
                'minute',
                'second',
                'timezone',
                'year',
                'month',
                'day',
                'message',
            ]
        )

    def __ne__(self, other):
        return any(
            getattr(self, attr) != getattr(other, attr, None)
            for attr in [
                'hour',
                'minute',
                'second',
                'timezone',
                'year',
                'month',
                'day',
                'message',
            ]
        )

    # Mutable objects probably shouldn't be made hashable
    # https://docs.python.org/3/reference/datamodel.html#object.__hash__
    __hash__ = None

    def get_duration(self, today=None):
        """Get the duration between the reminder and ``today``

        :param today: aware datetime to compare to; defaults to current time
        :type today: aware :class:`datetime.datetime`
        :return: The duration, in second, between ``today`` and the reminder.
        :rtype: :class:`int`

        This method returns the number of seconds given by the
        :class:`datetime.timedelta` obtained by the difference between the
        reminder and ``today``.

        If the delta between the reminder and ``today`` is negative, Python
        will represent it as a negative number of days, and a positive number
        of seconds: since it returns the number of seconds, any past reminder
        will be transformed into a future reminder the next day.

        .. seealso::

            The :mod:`datetime` built-in module's documentation explains what
            is an "aware" datetime.

        """
        if not today:
            today = datetime.now(self.timezone)
        else:
            today = today.astimezone(self.timezone)

        year = self.year if self.year is not None else today.year
        month = self.month if self.month is not None else today.month
        day = self.day if self.day is not None else today.day

        at_time = datetime(
            year, month, day,
            self.hour, self.minute, self.second,
            tzinfo=today.tzinfo)

        timediff = at_time - today
        duration = timediff.seconds

        if timediff.days > 0:
            duration = duration + (86400 * timediff.days)

        return duration


def parse_regex_match(match, default_timezone=None):
    """Parse a time reminder from ``match``

    :param match: :obj:`~.REGEX_AT`'s matching result
    :param default_timezone: timezone used when ``match`` doesn't have one;
                             defaults to ``UTC``
    :rtype: :class:`TimeReminder`
    """
    try:
        # Removing the `or` clause will BREAK the fallback to default_timezone!
        # We need some invalid value other than None to trigger the ValueError.
        # validate_timezone(None) excepting would be easier, but it doesn't.
        timezone = validate_timezone(match.group('tz') or '')
    except ValueError:
        timezone = default_timezone or 'UTC'

    return TimeReminder(
        int(match.group('hours')),
        int(match.group('minutes')),
        int(match.group('seconds') or '0'),
        timezone,
        match.group('date1'),
        match.group('date2'),
        match.group('date3'),
        match.group('message')
    )


@plugin.command('at')
@plugin.example('.at 13:47 Do your homework!', user_help=True)
@plugin.example('.at 03:14:07 2038-01-19 End of signed 32-bit int timestamp',
                user_help=True)
@plugin.example('.at 00:01 25/12 Open your gift!', user_help=True)
def remind_at(bot, trigger):
    """Gives you a reminder at the given time.

    Takes ``hh:mm:ssTimezone Date message`` where seconds, Timezone, and Date
    are optional.

    Timezone is any timezone Sopel takes elsewhere; the best choices are those
    from the tzdb; a list of valid options is available at
    <https://sopel.chat/tz>.

    The Date can be expressed in one of these formats: YYYY-mm-dd, dd-mm-YYYY,
    dd-mm-YY, or dd-mm. The separator can be ``.``, ``-``, or ``/``.
    """
    if not trigger.group(2):
        bot.reply("No arguments given for reminder command.")
        return plugin.NOLIMIT
    if trigger.group(3) and not trigger.group(4):
        bot.reply("No message given for reminder.")
        return plugin.NOLIMIT

    match = REGEX_AT.match(trigger.group(2))
    if not match:
        bot.reply("Sorry, but I didn't understand your input.")
        return plugin.NOLIMIT

    default_timezone = get_timezone(bot.db, bot.config, None,
                                    trigger.nick, trigger.sender)

    reminder = parse_regex_match(match, default_timezone)

    try:
        duration = reminder.get_duration()
    except ValueError as error:
        bot.reply(
            "Sorry, but I didn't understand your input: %s" % str(error))
        return plugin.NOLIMIT

    # save reminder
    timestamp = create_reminder(bot, trigger, duration, reminder.message)

    if duration >= 60:
        human_time = format_time(
            bot.db,
            bot.config,
            reminder.timezone.zone,
            trigger.nick,
            trigger.sender,
            datetime.utcfromtimestamp(timestamp))
        bot.reply('Okay, will remind at %s' % human_time)
    else:
        bot.reply('Okay, will remind in %s secs' % duration)


@plugin.command('reminders')
@plugin.example('.reminders forget *', user_help=True)
@plugin.example('.reminders count #channel', user_help=True)
@plugin.example('.reminders count', user_help=True)
def manage_reminders(bot, trigger):
    """Count or forget your reminders in the current channel.

    Use a subcommand "count" (default) or "forget". The second argument is
    optional and can be either a channel name, your nick, or * (for all).
    """
    owner = trigger.nick
    action = trigger.group(3) or trigger.sender
    target = trigger.group(4)

    if action not in ['count', 'forget'] and not target:
        # assume `.reminders` or `.reminders #channel`
        # in that case, invalid action will just count 0 reminder
        action, target = 'count', action

    if action == 'count':
        tpl = 'You have {count} reminders for all channels.'
        nick_reminders = (
            (timestamp, channel, nick, message)
            for timestamp, reminders in bot.rdb.items()
            for channel, nick, message in reminders
            if nick == owner
        )
        if target and target != '*':
            tpl = 'You have {count} reminders in {target}.'
            nick_reminders = (
                (timestamp, channel, nick, message)
                for timestamp, channel, nick, message in nick_reminders
                if channel == target
            )

        count = sum(1 for __ in nick_reminders)

        if target == owner:
            target = 'private'

        bot.reply(tpl.format(count=count, target=target))

    elif action == 'forget':
        bot.rdb = {
            timestamp: [
                (channel, nick, message)
                for channel, nick, message in reminders
                if not (
                    nick == owner
                    and (target == '*' or target == channel)
                )
            ]
            for timestamp, reminders in bot.rdb.items()
        }
        dump_database(bot.rfn, bot.rdb)

        if not target or target == '*':
            bot.reply('I forgot all your reminders.')
        elif target == owner:
            bot.reply('I forgot your private reminders.')
        else:
            bot.reply('I forgot your reminders in %s' % target)

    else:
        bot.reply(
            'Unrecognized action. '
            'Usage: {}reminders [count|forget [nickname|channel|*]]'
            .format(bot.config.core.help_prefix))
