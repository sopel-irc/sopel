# coding=utf8
"""
clock.py - Willie Clock Module
Copyright 2008-9, Sean B. Palmer, inamidst.com
Copyright 2012, Edward Powell, embolalia.net
Licensed under the Eiffel Forum License 2.

http://willie.dfbta.net
"""
from __future__ import unicode_literals

try:
    import pytz
except ImportError:
    pytz = None

import datetime
from willie.module import commands, example, OP
from willie.tools import get_timezone, format_time


def configure(config):
    config.interactive_add('clock', 'tz',
                           'Preferred time zone (http://dft.ba/-tz)', 'UTC')
    config.interactive_add('clock', 'time_format',
                           'Preferred time format (http://strftime.net)', '%F - %T%Z')


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


@commands('settz')
@example('.settz America/New_York')
def update_user(bot, trigger):
    """
    Set your preferred time zone. Most timezones will work, but it's best to
    use one from http://dft.ba/-tz
    """
    if not pytz:
        bot.reply("Sorry, I don't have timezone support installed.")
    else:
        tz = trigger.group(2)
        if not tz:
            bot.reply("What timezone do you want to set? Try one from "
                      "http://dft.ba/-tz")
            return
        if tz not in pytz.all_timezones:
            bot.reply("I don't know that time zone. Try one from "
                      "http://dft.ba/-tz")
            return

        bot.db.set_nick_value(trigger.nick, 'timezone', tz)
        if len(tz) < 7:
            bot.say("Okay, {}, but you should use one from http://dft.ba/-tz "
                    "if you use DST.".format(trigger.nick))
        else:
            bot.reply('I now have you in the %s time zone.' % tz)


@commands('settimeformat', 'settf')
@example('.settf %FT%T%z')
def update_user_format(bot, trigger):
    """
    Sets your preferred format for time. Uses the standard strftime format. You
    can use http://strftime.net or your favorite search engine to learn more.
    """
    tformat = trigger.group(2)
    if not tformat:
        bot.reply("What format do you want me to use? Try using"
                  " http://strftime.net to make one.")

    tz = get_timezone(bot.db, bot.config, None, None, trigger.sender)

    # Get old format as back-up
    old_format = bot.db.get_nick_value(trigger.nick, 'time_format')

    # Save the new format in the database so we can test it.
    bot.db.set_nick_value(trigger.nick, 'time_format', tformat)

    try:
        timef = format_time(db=bot.db, zone=tz, nick=trigger.nick)
    except:
        bot.reply("That format doesn't work. Try using"
                  " http://strftime.net to make one.")
        # New format doesn't work. Revert save in database.
        bot.db.set_nick_value(trigger.nick, 'time_format', old_format)
        return
    bot.reply("Got it. Your time will now appear as %s. (If the "
              "timezone is wrong, you might try the settz command)"
              % timef)


@commands('channeltz')
@example('.chantz America/New_York')
def update_channel(bot, trigger):
    """
    Set the preferred time zone for the channel.
    """
    if bot.privileges[trigger.sender][trigger.nick] < OP:
        return
    elif not pytz:
        bot.reply("Sorry, I don't have timezone support installed.")
    else:
        tz = trigger.group(2)
        if not tz:
            bot.reply("What timezone do you want to set? Try one from "
                      "http://dft.ba/-tz")
            return
        if tz not in pytz.all_timezones:
            bot.reply("I don't know that time zone. Try one from "
                      "http://dft.ba/-tz")
            return

        bot.db.set_channel_value(trigger.sender, 'timezone', tz)
        if len(tz) < 7:
            bot.say("Okay, {}, but you should use one from http://dft.ba/-tz "
                    "if you use DST.".format(trigger.nick))
        else:
            bot.reply(
                'I now have {} in the {} time zone.'.format(trigger.sender, tz))


@commands('setchanneltimeformat', 'setctf')
@example('setctf %FT%T%z')
def update_channel_format(bot, trigger):
    """
    Sets your preferred format for time. Uses the standard strftime format. You
    can use http://strftime.net or your favorite search engine to learn more.
    """
    if bot.privileges[trigger.sender][trigger.nick] < OP:
        return

    tformat = trigger.group(2)
    if not tformat:
        bot.reply("What format do you want me to use? Try using"
                  " http://strftime.net to make one.")

    tz = get_timezone(bot.db, bot.config, None, None, trigger.sender)
    try:
        timef = format_time(zone=tz)
    except:
        bot.reply("That format doesn't work. Try using"
                  " http://strftime.net to make one.")
        return
    bot.db.set_channel_value(trigger.sender, 'time_format', tformat)
    bot.reply("Got it. Times in this channel  will now appear as %s "
              "unless a user has their own format set. (If the timezone"
              " is wrong, you might try the settz and channeltz "
              "commands)" % timef)
