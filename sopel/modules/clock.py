# coding=utf-8
"""clock.py - Sopel Clock Plugin

Copyright 2008-9, Sean B. Palmer, inamidst.com
Copyright 2012, Elsie Powell, embolalia.com
Licensed under the Eiffel Forum License 2.

https://sopel.chat
"""
from __future__ import absolute_import, division, print_function, unicode_literals

from sopel import plugin, tools
from sopel.tools.time import (
    format_time,
    get_channel_timezone,
    get_nick_timezone,
    get_timezone,
    validate_timezone
)

PLUGIN_OUTPUT_PREFIX = '[clock] '
ERROR_NO_TIMEZONE = (
    'What timezone do you want to use? '
    'Try one from https://sopel.chat/tz')
ERROR_NO_FORMAT = (
    'What format do you want me to use? '
    'Try using http://strftime.net to make one.')
ERROR_INVALID_TIMEZONE = (
    'Could not find timezone "%s". '
    'Try one from https://sopel.chat/tz')
ERROR_INVALID_FORMAT = (
    "That format doesn't work. Try using "
    "http://strftime.net to make one.")


@plugin.command('t', 'time')
@plugin.example('.t America/New_York', user_help=True)
@plugin.example('.t Exirel', user_help=True)
@plugin.example('.t #sopel', user_help=True)
@plugin.example('.t', user_help=True)
@plugin.output_prefix(PLUGIN_OUTPUT_PREFIX)
def f_time(bot, trigger):
    """Return the current time.

    The command takes an optional parameter: it will try to guess if it's a
    nick, a channel, or a timezone (in that order).

    If it's a known nick or channel but there is no configured timezone, then
    it will complain. If nothing can be found, it'll complain that the argument
    is not a valid timezone.

    The format used can be set with the ``settf`` or ``setctf`` commands.
    """
    argument = trigger.group(2)

    if not argument:
        # get default timezone from nick, or sender, or bot, or UTC
        zone = get_timezone(
            bot.db, bot.config, None, trigger.nick, trigger.sender)
    else:
        # guess if the argument is a nick, a channel, or a timezone
        zone = None
        argument = argument.strip()
        channel_or_nick = tools.Identifier(argument)

        # first, try to get nick or channel's timezone
        help_prefix = bot.config.core.help_prefix
        if channel_or_nick.is_nick():
            zone = get_nick_timezone(bot.db, channel_or_nick)
            if zone is None and channel_or_nick in bot.users:
                # zone not found for a known nick: error case
                set_command = '%ssettz <zone>' % help_prefix
                if channel_or_nick != trigger.nick:
                    bot.reply(
                        'Could not find a timezone for this nick. '
                        '%s can set a timezone with `%s`'
                        % (argument, set_command))
                else:
                    bot.reply(
                        'Could not find a timezone for you. '
                        'You can set your timezone with `%s`'
                        % set_command)
                return
        else:
            zone = get_channel_timezone(bot.db, channel_or_nick)
            if zone is None and channel_or_nick in bot.channels:
                # zone not found for an existing channel: error case
                set_command = '%ssetctz <zone>' % help_prefix
                bot.reply(
                    'Could not find timezone for channel %s. '
                    'It can be set with `%s`. (requires OP privileges)'
                    % (argument, set_command))
                return

        # then, fallback on timezone detection
        if zone is None:
            # argument not found as nick or channel timezone
            try:
                zone = validate_timezone(argument)
            except ValueError:
                bot.reply(ERROR_INVALID_TIMEZONE % argument)
                return

    time = format_time(bot.db, bot.config, zone, trigger.nick, trigger.sender)
    bot.say(time)


@plugin.command('tz', 'timez')
@plugin.example('.tz America/New_York')
@plugin.output_prefix(PLUGIN_OUTPUT_PREFIX)
def f_time_zone(bot, trigger):
    """Return the current time in a timezone.

    Unlike the ``time`` command, it requires an argument, and that argument
    must be a valid timezone.
    """
    argument = trigger.group(2)
    if not argument:
        bot.reply(ERROR_NO_TIMEZONE)
        return

    zone = None
    argument = argument.strip()
    try:
        zone = validate_timezone(argument)
    except ValueError:
        bot.reply(ERROR_INVALID_TIMEZONE % argument)
        return

    time = format_time(bot.db, bot.config, zone, trigger.nick, trigger.sender)
    bot.say(time)


@plugin.command('settz', 'settimezone')
@plugin.example('.settz America/New_York')
def update_user(bot, trigger):
    """Set your preferred timezone.

    Most timezones will work, but it's best to use one from
    <https://sopel.chat/tz>.
    """
    argument = trigger.group(2)
    if not argument:
        bot.reply(ERROR_NO_TIMEZONE)
        return

    try:
        zone = validate_timezone(argument)
    except ValueError:
        bot.reply(ERROR_INVALID_TIMEZONE % argument)
        return

    bot.db.set_nick_value(trigger.nick, 'timezone', zone)

    if len(zone) < 4:
        bot.reply(
            'Okay, but you should use one from https://sopel.chat/tz '
            'if you use DST.')
    else:
        bot.reply('I now have you in the %s timezone.' % zone)


@plugin.command('gettz', 'gettimezone')
@plugin.example('.gettz Exirel', user_help=True)
@plugin.example('.gettz', user_help=True)
@plugin.output_prefix(PLUGIN_OUTPUT_PREFIX)
def get_user_tz(bot, trigger):
    """Gets a user's preferred time zone.

    It will show yours if no user specified.
    """
    nick = trigger.group(2)
    if not nick:
        nick = trigger.nick

    nick = nick.strip()
    zone = get_nick_timezone(bot.db, nick)

    if zone:
        bot.say('%s\'s time zone is %s.' % (nick, zone))
    else:
        bot.say('%s has not set their time zone' % nick)


@plugin.command('settimeformat', 'settf')
@plugin.example('.settf %Y-%m-%dT%T%z')
def update_user_format(bot, trigger):
    """Sets your preferred format for time.

    Uses the standard strftime format. You can use <http://strftime.net> or
    your favorite search engine to learn more.
    """
    tformat = trigger.group(2)
    if not tformat:
        bot.reply(ERROR_NO_FORMAT)
        return

    tz = get_timezone(bot.db, bot.config, None, trigger.nick, trigger.sender)

    # Get old format as back-up
    old_format = bot.db.get_nick_value(trigger.nick, 'time_format')

    # Save the new format in the database so we can test it.
    bot.db.set_nick_value(trigger.nick, 'time_format', tformat)

    try:
        timef = format_time(db=bot.db, zone=tz, nick=trigger.nick)
    except Exception:  # TODO: Be specific
        bot.reply(ERROR_INVALID_FORMAT)
        # New format doesn't work. Revert save in database.
        bot.db.set_nick_value(trigger.nick, 'time_format', old_format)
        return

    set_command = '%ssettz' % bot.settings.core.help_prefix
    bot.reply('Your time will now appear as %s. '
              '(If the timezone is wrong, you might try the %s command)'
              % (timef, set_command))


@plugin.command('gettimeformat', 'gettf')
@plugin.example('.gettf Exirel', user_help=True)
@plugin.example('.gettf', user_help=True)
@plugin.output_prefix(PLUGIN_OUTPUT_PREFIX)
def get_user_format(bot, trigger):
    """Gets a user's preferred time format.

    It will show yours if no user specified.
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


@plugin.command('setchanneltz', 'setctz')
@plugin.example('.setctz America/New_York')
@plugin.require_chanmsg
@plugin.require_privilege(plugin.OP, message='Changing the channel timezone requires OP privileges.')
def update_channel(bot, trigger):
    """Set the preferred timezone for the current channel."""
    argument = trigger.group(2)
    if not argument:
        bot.reply(ERROR_NO_TIMEZONE)
        return

    try:
        zone = validate_timezone(argument)
    except ValueError:
        bot.reply(ERROR_INVALID_TIMEZONE % argument)
        return

    channel = trigger.sender
    bot.db.set_channel_value(channel, 'timezone', zone)

    if len(zone) < 4:
        bot.reply(
            'Okay, but you should use one from https://sopel.chat/tz '
            'if you use DST.')
    else:
        bot.reply('I now have %s in the %s timezone.' % (channel, zone))


@plugin.command('getchanneltz', 'getctz')
@plugin.example('.getctz #sopel', user_help=True)
@plugin.example('.getctz', user_help=True)
@plugin.output_prefix(PLUGIN_OUTPUT_PREFIX)
def get_channel_tz(bot, trigger):
    """Gets the channel's preferred timezone.

    It returns the current channel's if no channel name is given.
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


@plugin.command('setchanneltimeformat', 'setctf')
@plugin.example('.setctf %Y-%m-%dT%T%z')
@plugin.require_chanmsg
@plugin.require_privilege(plugin.OP)
@plugin.output_prefix(PLUGIN_OUTPUT_PREFIX)
def update_channel_format(bot, trigger):
    """Sets your preferred format for time.

    Uses the standard strftime format. You can use <http://strftime.net> or
    your favorite search engine to learn more.
    """
    tformat = trigger.group(2)
    if not tformat:
        bot.reply(ERROR_NO_FORMAT)
        return

    tz = get_timezone(bot.db, bot.config, None, None, trigger.sender)

    # Get old format as back-up
    old_format = bot.db.get_channel_value(trigger.sender, 'time_format')

    # Save the new format in the database so we can test it.
    bot.db.set_channel_value(trigger.sender, 'time_format', tformat)

    try:
        timef = format_time(db=bot.db, zone=tz, channel=trigger.sender)
    except Exception:  # TODO: Be specific
        bot.reply(ERROR_INVALID_FORMAT)
        # New format doesn't work. Revert save in database.
        bot.db.set_channel_value(trigger.sender, 'time_format', old_format)
        return
    bot.db.set_channel_value(trigger.sender, 'time_format', tformat)

    help_prefix = bot.settings.core.help_prefix
    set_command = '%ssettz' % help_prefix
    channel_command = '%schanneltz' % help_prefix
    bot.say("Times in this channel will now appear as %s "
            "unless a user has their own format set. (If the timezone"
            " is wrong, you might try the %s and %s "
            "commands)" % (timef, set_command, channel_command))


@plugin.command('getchanneltimeformat', 'getctf')
@plugin.example('.getctf #sopel', user_help=True)
@plugin.example('.getctf', user_help=True)
@plugin.output_prefix(PLUGIN_OUTPUT_PREFIX)
def get_channel_format(bot, trigger):
    """Gets the channel's preferred time format

    It returns the current channel's if no channel name is given.
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
