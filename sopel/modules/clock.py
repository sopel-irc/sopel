# coding=utf-8
"""
clock.py - Sopel Clock Module
Copyright 2008-9, Sean B. Palmer, inamidst.com
Copyright 2012, Elsie Powell, embolalia.com
Licensed under the Eiffel Forum License 2.

https://sopel.chat
"""
from __future__ import unicode_literals, absolute_import, print_function, division

from sopel import module, tools
from sopel.config.types import StaticSection, ValidatedAttribute
from sopel.tools.time import (
    format_time,
    get_channel_timezone,
    get_nick_timezone,
    get_timezone,
    validate_format,
    validate_timezone
)


class TimeSection(StaticSection):
    tz = ValidatedAttribute(
        'tz',
        parse=validate_timezone,
        serialize=validate_timezone,
        default='UTC')
    """Default time zone (see https://sopel.chat/tz)"""
    time_format = ValidatedAttribute(
        'time_format',
        parse=validate_format,
        default='%Y-%m-%d - %T%Z')
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


@module.commands('t', 'time')
@module.example('.t America/New_York')
@module.example('.t Exirel')
@module.example('.t #sopel')
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


@module.commands('settz', 'settimezone')
@module.example('.settz America/New_York')
def update_user(bot, trigger):
    """Set your preferred timezone.

    Most timezones will work, but it's best to use one from
    <https://sopel.chat/tz>.
    """
    argument = trigger.group(2)
    if not argument:
        bot.reply("What timezone do you want to set? Try one from "
                  "https://sopel.chat/tz")
        return

    try:
        zone = validate_timezone(argument)
    except ValueError:
        bot.say(
            'I don\'t know that timezone. Try one from https://sopel.chat/tz')
        return

    bot.db.set_nick_value(trigger.nick, 'timezone', zone)

    if len(zone) < 4:
        bot.say(
            'Okay, %s, but you should use one from https://sopel.chat/tz '
            'if you use DST.' % trigger.nick)
    else:
        bot.reply('I now have you in the %s timezone.' % zone)


@module.commands('gettz', 'gettimezone')
@module.example('.gettz [nick]')
def get_user_tz(bot, trigger):
    """Gets a user's preferred time zone; will show yours if no user specified."""
    nick = trigger.group(2)
    if not nick:
        nick = trigger.nick

    nick = nick.strip()
    zone = get_nick_timezone(bot.db, nick)

    if zone:
        bot.say('%s\'s time zone is %s.' % (nick, zone))
    else:
        bot.say('%s has not set their time zone' % nick)


@module.commands('settimeformat', 'settf')
@module.example('.settf %Y-%m-%dT%T%z')
def update_user_format(bot, trigger):
    """
    Sets your preferred format for time. Uses the standard strftime format. You
    can use <http://strftime.net> or your favorite search engine to learn more.
    """
    tformat = trigger.group(2)
    if not tformat:
        bot.reply("What format do you want me to use? Try using "
                  "http://strftime.net to make one.")
        return

    tz = get_timezone(bot.db, bot.config, None, trigger.nick, trigger.sender)

    # Get old format as back-up
    old_format = bot.db.get_nick_value(trigger.nick, 'time_format')

    # Save the new format in the database so we can test it.
    bot.db.set_nick_value(trigger.nick, 'time_format', tformat)

    try:
        timef = format_time(db=bot.db, zone=tz, nick=trigger.nick)
    except Exception:  # TODO: Be specific
        bot.reply("That format doesn't work. Try using "
                  "http://strftime.net to make one.")
        # New format doesn't work. Revert save in database.
        bot.db.set_nick_value(trigger.nick, 'time_format', old_format)
        return
    bot.reply("Got it. Your time will now appear as %s. (If the "
              "timezone is wrong, you might try the settz command)"
              % timef)


@module.commands('gettimeformat', 'gettf')
@module.example('.gettf [nick]')
def get_user_format(bot, trigger):
    """Gets a user's preferred time format; will show yours if no user specified."""
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


@module.commands('setchanneltz', 'setctz')
@module.example('.setctz America/New_York')
@module.require_privilege(module.OP)
def update_channel(bot, trigger):
    """Set the preferred timezone for the channel."""
    argument = trigger.group(2)
    if not argument:
        bot.reply("What timezone do you want to set? Try one from "
                  "https://sopel.chat/tz")
        return

    try:
        zone = validate_timezone(argument)
    except ValueError:
        bot.say(
            'I don\'t know that timezone. Try one from https://sopel.chat/tz')
        return

    channel = trigger.sender
    bot.db.set_channel_value(channel, 'timezone', zone)

    if len(zone) < 4:
        bot.say(
            'Okay, %s, but you should use one from https://sopel.chat/tz '
            'if you use DST.' % trigger.nick)
    else:
        bot.reply('I now have %s in the %s timezone.' % (channel, zone))


@module.commands('getchanneltz', 'getctz')
@module.example('.getctz [channel]')
def get_channel_tz(bot, trigger):
    """
    Gets the channel's preferred timezone; returns the current channel's
    if no channel name is given.
    """
    channel = trigger.group(2)
    if not channel:
        channel = trigger.sender

    channel = channel.strip()
    zone = get_channel_timezone(bot.db, channel)

    if zone:
        bot.say('%s\'s timezone: %s' % (channel, zone))
    else:
        bot.say('%s has no preferred timezone' % channel)


@module.commands('setchanneltimeformat', 'setctf')
@module.example('.setctf %Y-%m-%dT%T%z')
@module.require_privilege(module.OP)
def update_channel_format(bot, trigger):
    """
    Sets your preferred format for time. Uses the standard strftime format. You
    can use <http://strftime.net> or your favorite search engine to learn more.
    """
    tformat = trigger.group(2)
    if not tformat:
        bot.reply("What format do you want me to use? Try using "
                  "http://strftime.net to make one.")

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


@module.commands('getchanneltimeformat', 'getctf')
@module.example('.getctf [channel]')
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
