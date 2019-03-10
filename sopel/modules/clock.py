# coding=utf-8
# Copyright 2008-9, Sean B. Palmer, inamidst.com
# Copyright 2012, Elsie Powell, embolalia.com
# Licensed under the Eiffel Forum License 2.
from __future__ import unicode_literals, absolute_import, print_function, division

try:
    import pytz
except ImportError:
    pytz = None

from sopel.module import commands, example, OP
from sopel.tools.time import (
    get_timezone, format_time, validate_format, validate_timezone
)
from sopel.config.types import StaticSection, ValidatedAttribute


class TimeSection(StaticSection):
    tz = ValidatedAttribute(
        'tz',
        parse=validate_timezone,
        serialize=validate_timezone,
        default='UTC'
    )
    """Default time zone (see https://sopel.chat/tz)"""
    time_format = ValidatedAttribute(
        'time_format',
        parse=validate_format,
        default='%Y-%m-%d - %T%Z'
    )
    """Default time format (see http://strftime.net)"""


def configure(config):
    """
    | name | example | purpose |
    | ---- | ------- | ------- |
    | tz | America/Chicago | Preferred time zone (see <https://sopel.chat/tz>); defaults to UTC |
    | time\\_format | %Y-%m-%d - %T%Z | Preferred time format (see <http://strftime.net>) |
    """
    config.define_section('clock', TimeSection)
    config.clock.configure_setting(
        'tz', 'Preferred time zone (https://sopel.chat/tz)')
    config.clock.configure_setting(
        'time_format', 'Preferred time format (http://strftime.net)')


def setup(bot):
    bot.config.define_section('clock', TimeSection)


@commands('t', 'time')
@example('.t America/New_York')
def f_time(bot, trigger):
    """Returns the current time."""
    if trigger.group(2):
        zone = get_timezone(bot.db, bot.config, trigger.group(2).strip(), None, None)
        if not zone:
            bot.say('Could not find timezone %s.' % trigger.group(2).strip())
            return
    else:
        zone = get_timezone(bot.db, bot.config, None, trigger.nick,
                            trigger.sender)
    time = format_time(bot.db, bot.config, zone, trigger.nick, trigger.sender)
    bot.say(time)


@commands('settz', 'settimezone')
@example('.settz America/New_York')
def update_user(bot, trigger):
    """
    Set your preferred time zone. Most timezones will work, but it's best to
    use one from <https://sopel.chat/tz>.
    """
    if not pytz:
        bot.reply("Sorry, I don't have timezone support installed.")
    else:
        tz = trigger.group(2)
        if not tz:
            bot.reply("What timezone do you want to set? Try one from "
                      "https://sopel.chat/tz")
            return
        if tz not in pytz.all_timezones:
            bot.reply("I don't know that time zone. Try one from "
                      "https://sopel.chat/tz")
            return

        bot.db.set_nick_value(trigger.nick, 'timezone', tz)
        if len(tz) < 7:
            bot.say("Okay, {}, but you should use one from https://sopel.chat/tz "
                    "if you use DST.".format(trigger.nick))
        else:
            bot.reply('I now have you in the %s time zone.' % tz)


@commands('gettz', 'gettimezone')
@example('.gettz [nick]')
def get_user_tz(bot, trigger):
    """
    Gets a user's preferred time zone; will show yours if no user specified.
    """
    if not pytz:
        bot.reply("Sorry, I don't have timezone support installed.")
    else:
        nick = trigger.group(2)
        if not nick:
            nick = trigger.nick

        nick = nick.strip()

        tz = bot.db.get_nick_value(nick, 'timezone')
        if tz:
            bot.say('%s\'s time zone is %s.' % (nick, tz))
        else:
            bot.say('%s has not set their time zone' % nick)


@commands('settimeformat', 'settf')
@example('.settf %Y-%m-%dT%T%z')
def update_user_format(bot, trigger):
    """
    Sets your preferred format for time. Uses the standard strftime format. You
    can use <http://strftime.net> or your favorite search engine to learn more.
    """
    tformat = trigger.group(2)
    if not tformat:
        bot.reply("What format do you want me to use? Try using"
                  " http://strftime.net to make one.")
        return

    tz = get_timezone(bot.db, bot.config, None, trigger.nick, trigger.sender)

    # Get old format as back-up
    old_format = bot.db.get_nick_value(trigger.nick, 'time_format')

    # Save the new format in the database so we can test it.
    bot.db.set_nick_value(trigger.nick, 'time_format', tformat)

    try:
        timef = format_time(db=bot.db, zone=tz, nick=trigger.nick)
    except Exception:  # TODO: Be specific
        bot.reply("That format doesn't work. Try using"
                  " http://strftime.net to make one.")
        # New format doesn't work. Revert save in database.
        bot.db.set_nick_value(trigger.nick, 'time_format', old_format)
        return
    bot.reply("Got it. Your time will now appear as %s. (If the "
              "timezone is wrong, you might try the settz command)"
              % timef)


@commands('gettimeformat', 'gettf')
@example('.gettf [nick]')
def get_user_format(bot, trigger):
    """
    Gets a user's preferred time format; will show yours if no user specified.
    """
    nick = trigger.group(2)
    if not nick:
        nick = trigger.nick

    nick = nick.strip()

    # Get old format as back-up
    format = bot.db.get_nick_value(nick, 'time_format')

    if format:
        bot.say("%s's time format: %s." % (nick, format))
    else:
        bot.say("%s hasn't set a custom time format" % nick)


@commands('setchanneltz', 'setctz')
@example('.setctz America/New_York')
def update_channel(bot, trigger):
    """
    Set the preferred timezone for the channel.
    """
    if bot.channels[trigger.sender].privileges[trigger.nick] < OP:
        return
    elif not pytz:
        bot.reply("Sorry, I don't have timezone support installed.")
    else:
        tz = trigger.group(2)
        if not tz:
            bot.reply("What timezone do you want to set? Try one from "
                      "https://sopel.chat/tz")
            return
        if tz not in pytz.all_timezones:
            bot.reply("I don't know that time zone. Try one from "
                      "https://sopel.chat/tz")
            return

        bot.db.set_channel_value(trigger.sender, 'timezone', tz)
        if len(tz) < 7:
            bot.say("Okay, {}, but you should use one from https://sopel.chat/tz "
                    "if you use DST.".format(trigger.nick))
        else:
            bot.reply(
                'I now have {} in the {} time zone.'.format(trigger.sender, tz))


@commands('getchanneltz', 'getctz')
@example('.getctz [channel]')
def get_channel_tz(bot, trigger):
    """
    Gets the channel's preferred timezone; returns the current channel's
    if no channel name is given.
    """
    if not pytz:
        bot.reply("Sorry, I don't have timezone support installed.")
    else:
        channel = trigger.group(2)
        if not channel:
            channel = trigger.sender

        channel = channel.strip()

        timezone = bot.db.get_channel_value(channel, 'timezone')
        if timezone:
            bot.say('%s\'s timezone: %s' % (channel, timezone))
        else:
            bot.say('%s has no preferred timezone' % channel)


@commands('setchanneltimeformat', 'setctf')
@example('.setctf %Y-%m-%dT%T%z')
def update_channel_format(bot, trigger):
    """
    Sets your preferred format for time. Uses the standard strftime format. You
    can use <http://strftime.net> or your favorite search engine to learn more.
    """
    if bot.channels[trigger.sender].privileges[trigger.nick] < OP:
        return

    tformat = trigger.group(2)
    if not tformat:
        bot.reply("What format do you want me to use? Try using"
                  " http://strftime.net to make one.")

    tz = get_timezone(bot.db, bot.config, None, None, trigger.sender)

    # Get old format as back-up
    old_format = bot.db.get_channel_value(trigger.sender, 'time_format')

    # Save the new format in the database so we can test it.
    bot.db.set_channel_value(trigger.sender, 'time_format', tformat)

    try:
        timef = format_time(db=bot.db, zone=tz, channel=trigger.sender)
    except Exception:  # TODO: Be specific
        bot.reply("That format doesn't work. Try using"
                  " http://strftime.net to make one.")
        # New format doesn't work. Revert save in database.
        bot.db.set_channel_value(trigger.sender, 'time_format', old_format)
        return
    bot.db.set_channel_value(trigger.sender, 'time_format', tformat)
    bot.reply("Got it. Times in this channel  will now appear as %s "
              "unless a user has their own format set. (If the timezone"
              " is wrong, you might try the settz and channeltz "
              "commands)" % timef)


@commands('getchanneltimeformat', 'getctf')
@example('.getctf [channel]')
def get_channel_format(bot, trigger):
    """
    Gets the channel's preferred time format; will return current channel's if
    no channel name is given.
    """

    channel = trigger.group(2)
    if not channel:
        channel = trigger.sender

    channel = channel.strip()

    tformat = bot.db.get_channel_value(channel, 'time_format')
    if tformat:
        bot.say('%s\'s time format: %s' % (channel, tformat))
    else:
        bot.say('%s has no preferred time format' % channel)
