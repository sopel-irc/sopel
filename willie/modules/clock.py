"""
clock.py - Willie Clock Module
Copyright 2008-9, Sean B. Palmer, inamidst.com
Copyright 2012, Edward Powell, embolalia.net
Licensed under the Eiffel Forum License 2.

http://willie.dfbta.net
"""
import pytz
import re
import math
import time
import urllib
import locale
import socket
import struct
import datetime
from decimal import Decimal as dec


def setup(willie):
    #Having a db means pref's exists. Later, we can just use `if willie.db`.
    if willie.db and not willie.db.preferences.has_columns('tz'):
        willie.db.preferences.add_columns(['tz'])
    if willie.db and not willie.db.preferences.has_columns('time_format'):
        willie.db.preferences.add_columns(['time_format'])


def f_time(willie, trigger):
    """Returns the current time."""
    tz = trigger.group(2)
    if tz:
        tz = tz.strip()
        #We have a tz. If it's in all_timezones, we don't need to do anything
        #more, because we know it's valid. Otherwise, we have to check if it's
        #supposed to be a user, or just invalid
        if tz not in pytz.all_timezones:
            if willie.db and tz in willie.db.preferences:
                tz = willie.db.preferences.get(tz, 'tz')
                if not tz:
                    willie.say("I'm sorry, I don't know %s's timezone" % tz)
            else:
                willie.say("I'm sorry, I don't know about the %s timezone or"
                           " user." % tz)
                return
    #We don't have a timzeone. Is there one set? If not, just use UTC
    elif willie.db:
        if trigger.nick in willie.db.preferences:
            tz = willie.db.preferences.get(trigger.nick, 'tz')
        if not tz and trigger.sender in willie.db.preferences:
            tz = willie.db.preferences.get(trigger.sender, 'tz') or 'UTC'
    else:
        tz = 'UTC'
    tzi = pytz.timezone(tz)
    now = datetime.datetime.now(tzi)

    tformat = ''
    if willie.db:
        if trigger.nick in willie.db.preferences:
            tformat = willie.db.preferences.get(trigger.nick, 'time_format')
        if not tformat and trigger.sender in willie.db.preferences:
            tformat = willie.db.preferences.get(trigger.sender, 'time_format')

    willie.say(now.strftime(tformat or "%F - %T%Z"))
f_time.commands = ['t', 'time']
f_time.name = 't'
f_time.example = '.t UTC'


def update_user(willie, trigger):
    """
    Set your preferred time zone. Most timezones will work, but it's best to
    use one from http://dft.ba/-tz
    """
    if willie.db:
        tz = trigger.group(2)
        if not tz:
            willie.reply("What timzeone do you want to set? Try one from "
                         "http://dft.ba/-tz")
            return
        if tz not in pytz.all_timezones:
            willie.reply("I don't know that time zone. Try one from "
                         "http://dft.ba/-tz")
            return

        willie.db.preferences.update(trigger.nick, {'tz': tz})
        if len(tz) < 7:
            willie.say("Okay, " + trigger.nick +
                        ", but you should use one from http://dft.ba/-tz if "
                        "you use DST.")
        else:
            willie.reply('I now have you in the %s time zone.' % tz)
    else:
        willie.reply("I can't remember that; I don't have a database.")
update_user.commands = ['settz']


def update_user_format(willie, trigger):
    """
    Sets your preferred format for time. Uses the standard strftime format. You
    can use http://strftime.net or your favorite search engine to learn more.
    """
    if willie.db:
        tformat = trigger.group(2)
        if not tformat:
            willie.reply("What format do you want me to use? Try using"
                         " http://strftime.net to make one.")

        tz = ''
        if willie.db:
            if trigger.nick in willie.db.preferences:
                tz = willie.db.preferences.get(trigger.nick, 'tz')
            if not tz and trigger.sender in willie.db.preferences:
                tz = willie.db.preferences.get(trigger.sender, 'tz')
        now = datetime.datetime.now(pytz.timezone(tz or 'UTC'))
        timef = ''
        try:
            timef = now.strftime(tformat)
        except:
            willie.reply("That format doesn't work. Try using"
                         " http://strftime.net to make one.")
            return
        willie.db.preferences.update(trigger.nick, {'time_format': tformat})
        willie.reply("Got it. Your time will now appear as %s. (If the "
                     "timezone is wrong, you might try the settz command)"
                     % timef)
    else:
        willie.reply("I can't remember that; I don't have a database.")
update_user_format.commands = ['settimeformat', 'settf']
update_user_format.example = ".settf %FT%T%z"


def update_channel(willie, trigger):
    """
    Set the preferred time zone for the channel.
    """
    if not trigger.isop:
        return
    if willie.db:
        tz = trigger.group(2)
        if not tz:
            willie.reply("What timzeone do you want to set? Try one from "
                         "http://dft.ba/-tz")
            return
        if tz not in pytz.all_timezones:
            willie.reply("I don't know that time zone. Try one from "
                         "http://dft.ba/-tz")
            return

        willie.db.preferences.update(trigger.sender, {'tz': tz})
        if len(tz) < 7:
            willie.say("Okay, " + trigger.nick +
                        ", but you should use one from http://dft.ba/-tz if "
                        "you use DST.")
        else:
            willie.reply('I now have you in the %s time zone.' % tz)
    else:
        willie.reply("I can't remember that; I don't have a database.")
update_channel.commands = ['channeltz']


def update_channel_format(willie, trigger):
    """
    Sets your preferred format for time. Uses the standard strftime format. You
    can use http://strftime.net or your favorite search engine to learn more.
    """
    if not trigger.isop:
        return
    if willie.db:
        tformat = trigger.group(2)
        if not tformat:
            willie.reply("What format do you want me to use? Try using"
                         " http://strftime.net to make one.")

        tz = ''
        if willie.db:
            if trigger.nick in willie.db.preferences:
                tz = willie.db.preferences.get(trigger.nick, 'tz')
            if not tz and trigger.sender in willie.db.preferences:
                tz = willie.db.preferences.get(trigger.sender, 'tz')
        now = datetime.datetime.now(pytz.timezone(tz or 'UTC'))
        timef = ''
        try:
            timef = now.strftime(tformat)
        except:
            willie.reply("That format doesn't work. Try using"
                         " http://strftime.net to make one.")
            return
        willie.db.preferences.update(trigger.sender, {'time_format': tformat})
        willie.reply("Got it. Times in this channel  will now appear as %s "
                     "unless a user has their own format set. (If the timezone"
                     " is wrong, you might try the settz and channeltz "
                     "commands)" % timef)
    else:
        willie.reply("I can't remember that; I don't have a database.")
update_channel_format.commands = ['setchanneltimeformat', 'setctf']
update_channel_format.example = ".settf %FT%T%z"


if __name__ == '__main__':
    print __doc__.strip()
