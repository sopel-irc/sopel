#!/usr/bin/env python
"""
remind.py - Jenni Reminder Module
Copyright 2011, Sean B. Palmer, inamidst.com
Licensed under the Eiffel Forum License 2.

http://inamidst.com/phenny/
"""

import os, re, time, threading
from pytz import timezone, all_timezones
import pytz
from datetime import tzinfo, timedelta, datetime
all_timezones_set = set(all_timezones)

def filename(self):
    name = self.nick + '-' + self.config.host + '.reminders.db'
    return os.path.join(os.path.expanduser('~/.jenni'), name)

def load_database(name):
    data = {}
    if os.path.isfile(name):
        f = open(name, 'rb')
        for line in f:
            unixtime, channel, nick, message = line.split('\t')
            message = message.rstrip('\n')
            t = int(float(unixtime))#WTFs going on here?
            reminder = (channel, nick, message)
            try: data[t].append(reminder)
            except KeyError: data[t] = [reminder]
        f.close()
    return data

def dump_database(name, data):
    f = open(name, 'wb')
    for unixtime, reminders in data.iteritems():
        for channel, nick, message in reminders:
            f.write('%s\t%s\t%s\t%s\n' % (unixtime, channel, nick, message))
    f.close()

def setup(jenni):
    jenni.rfn = filename(jenni)
    jenni.rdb = load_database(jenni.rfn)

    def monitor(jenni):
        time.sleep(5)
        while True:
            now = int(time.time())
            unixtimes = [int(key) for key in jenni.rdb]
            oldtimes = [t for t in unixtimes if t <= now]
            if oldtimes:
                for oldtime in oldtimes:
                    for (channel, nick, message) in jenni.rdb[oldtime]:
                        if message:
                            jenni.msg(channel, nick + ': ' + message)
                        else: jenni.msg(channel, nick + '!')
                    del jenni.rdb[oldtime]
                dump_database(jenni.rfn, jenni.rdb)
            time.sleep(2.5)

    targs = (jenni,)
    t = threading.Thread(target=monitor, args=targs)
    t.start()

scaling = {
    'years': 365.25 * 24 * 3600,
    'year': 365.25 * 24 * 3600,
    'yrs': 365.25 * 24 * 3600,
    'y': 365.25 * 24 * 3600,

    'months': 29.53059 * 24 * 3600,
    'month': 29.53059 * 24 * 3600,
    'mo': 29.53059 * 24 * 3600,

    'weeks': 7 * 24 * 3600,
    'week': 7 * 24 * 3600,
    'wks': 7 * 24 * 3600,
    'wk': 7 * 24 * 3600,
    'w': 7 * 24 * 3600,

    'days': 24 * 3600,
    'day': 24 * 3600,
    'd': 24 * 3600,

    'hours': 3600,
    'hour': 3600,
    'hrs': 3600,
    'hr': 3600,
    'h': 3600,

    'minutes': 60,
    'minute': 60,
    'mins': 60,
    'min': 60,
    'm': 60,

    'seconds': 1,
    'second': 1,
    'secs': 1,
    'sec': 1,
    's': 1
}

periods = '|'.join(scaling.keys())

def remind(jenni, input):
    duration = 0
    message = re.split('(\d+ ?(?:'+periods+')) ?', input.group(2))[1:]
    print input.group(2)
    print message
    reminder = ''
    for piece in message:
        stop = False
        grp = re.match('(\d+) ?(.*) ?', piece)
        if grp and not stop:
            length = float(grp.group(1))
            factor = scaling.get(grp.group(2), 60)
            duration += length * factor
        else:
            reminder = reminder + piece
            stop = True
    if duration == 0:
        return jenni.reply("Sorry, didn't understand the input.")
            
    if duration % 1:
        duration = int(duration) + 1
    else: duration = int(duration)

    create_reminder(jenni, input, duration, reminder)
remind.commands = ['in']


def at(jenni, input):
    hour, minute, second, tz, message = input.groups()
    if not second: second = '0'
    
    # Personal time zones, because they're rad
    if jenni.settings.hascolumn('tz'):
        if input.group(2) and tz in jenni.settings:
            personal_tz = jenni.settings.get(tz, 'tz')
        elif input.nick in jenni.settings:
            personal_tz = jenni.settings.get(input.nick, 'tz')
    if tz not in all_timezones_set and not personal_tz: 
        message=tz+message
        tz = 'UTC'
    elif tz not in all_timezones_set and personal_tz:
        message=tz+message
        tz = personal_tz
    tz = tz.strip()
    
    if tz not in all_timezones_set:
        jenni.say("Sorry, but I don't have data for that timezone or user.")
        return
        
    tzi = timezone(tz)
    now = datetime.now(tzi)

    timediff = (datetime(now.year, now.month, now.day, int(hour), int(minute), int(second), tzinfo = tzi) - now)
    duration = timediff.seconds

    if duration < 0: duration += 86400
    create_reminder(jenni, input, duration, message)
at.rule = r'\.at (\d+):(\d+):?(\d+)? (\S+)?( .*)'

def create_reminder(jenni, input, duration, message):
    t = int(time.time()) + duration
    reminder = (input.sender, input.nick, message)
    try: jenni.rdb[t].append(reminder)
    except KeyError: jenni.rdb[t] = [reminder]

    dump_database(jenni.rfn, jenni.rdb)

    if duration >= 60:
        w = ''
        if duration >= 3600 * 12:
            w += time.strftime(' on %d %b %Y', time.gmtime(t))
        w += time.strftime(' at %H:%MZ', time.gmtime(t))
        jenni.reply('Okay, will remind%s' % w)
    else: jenni.reply('Okay, will remind in %s secs' % duration)

if __name__ == '__main__':
    print __doc__.strip()
