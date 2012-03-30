#!/usr/bin/env python
"""
remind.py - Jenni Reminder Module
Copyright 2011, Sean B. Palmer, inamidst.com
Licensed under the Eiffel Forum License 2.

http://inamidst.com/phenny/
"""

import os, re, time, threading
from pytz import timezone
import pytz
from datetime import tzinfo, timedelta, datetime

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
p_command = r'\.in ([0-9]+(?:\.[0-9]+)?)\s?((?:%s)\b)?:?\s?(.*)' % periods
r_command = re.compile(p_command)

def remind(jenni, input):
    m = r_command.match(input.bytes)
    if not m:
        return jenni.reply("Sorry, didn't understand the input.")
    length, scale, message = m.groups()

    length = float(length)
    factor = scaling.get(scale, 60)
    duration = length * factor

    if duration % 1:
        duration = int(duration) + 1
    else: duration = int(duration)

    create_reminder(jenni, input, duration, message)
remind.commands = ['in']


def at(jenni, input):
    hour, minute, second, tz, message = input.groups()
    if not second: second = '0'
    

    # Personal time zones, because they're rad, copied from clock.py
    if hasattr(jenni.config, 'timezones'):
        People = jenni.config.timezones
    else: People = {}

    if People.has_key(tz):
        ltz = People[tz]
    elif (tz == ''):
        if People.has_key(input.nick):
            ltz = People[input.nick]
        else: ltz = 'UTC'
    else: ltz = get_ltz(tz)
    
    # Now take that long-form timezone name, and try to get the data for it.
    try:
        tzi = timezone(ltz)
    except KeyError: 
        jenni.say("Sorry, but I don't have data for that timezone or user.")
        return
    
    now = datetime.now(tzi)
    days = int(now.day)
    
    timediff = (datetime(now.year, now.month, days, 
                    int(hour), int(minute), int(second), tzinfo = tzi) 
                    - now)
    duration = timediff.total_seconds()
    if duration < 0: duration += 86400
    create_reminder(jenni, input, duration, message)
at.rule = r'\.at (\d+):(\d+):?(\d+)?([\w\d]{0,4}) (.*)'

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

def get_ltz(tz):
    return "US/Eastern"



#An attempt to do a tzinfo implementation. God, it's crap, though.

TimeZones = {'KST': 9, 'CADT': 10.5, 'EETDST': 3, 'MESZ': 2, 'WADT': 9,
            'EET': 2, 'MST': -7, 'WAST': 8, 'IST': 5.5, 'B': 2,
            'MSK': 3, 'X': -11, 'MSD': 4, 'CETDST': 2, 'AST': -4,
            'HKT': 8, 'JST': 9, 'CAST': 9.5, 'CET': 1, 'CEST': 2,
            'EEST': 3, 'EAST': 10, 'METDST': 2, 'MDT': -6, 'A': 1,
            'UTC': 0, 'ADT': -3, 'EST': -5, 'E': 5, 'D': 4, 'G': 7,
            'F': 6, 'I': 9, 'H': 8, 'K': 10, 'PDT': -7, 'M': 12,
            'L': 11, 'O': -2, 'MEST': 2, 'Q': -4, 'P': -3, 'S': -6,
            'R': -5, 'U': -8, 'T': -7, 'W': -10, 'WET': 0, 'Y': -12,
            'CST': -6, 'EADT': 11, 'Z': 0, 'GMT': 0, 'WETDST': 1,
            'C': 3, 'WEST': 1, 'CDT': -5, 'MET': 1, 'N': -1, 'V': -9,
            'EDT': -4, 'UT': 0, 'PST': -8, 'MEZ': 1, 'BST': 1,
            'ACS': 9.5, 'ATL': -4, 'ALA': -9, 'HAW': -10, 'AKDT': -8,
            'AKST': -9,
            'BDST': 2}

TZ1 = {
 'NDT': -2.5,
 'BRST': -2,
 'ADT': -3,
 'EDT': -4,
 'CDT': -5,
 'MDT': -6,
 'PDT': -7,
 'YDT': -8,
 'HDT': -9,
 'BST': 1,
 'MEST': 2,
 'SST': 2,
 'FST': 2,
 'CEST': 2,
 'EEST': 3,
 'WADT': 8,
 'KDT': 10,
 'EADT': 13,
 'NZD': 13,
 'NZDT': 13,
 'GMT': 0,
 'UT': 0,
 'UTC': 0,
 'WET': 0,
 'WAT': -1,
 'AT': -2,
 'FNT': -2,
 'BRT': -3,
 'MNT': -4,
 'EWT': -4,
 'AST': -4,
 'EST': -5,
 'ACT': -5,
 'CST': -6,
 'MST': -7,
 'PST': -8,
 'YST': -9,
 'HST': -10,
 'CAT': -10,
 'AHST': -10,
 'NT': -11,
 'IDLW': -12,
 'CET': 1,
 'MEZ': 1,
 'ECT': 1,
 'MET': 1,
 'MEWT': 1,
 'SWT': 1,
 'SET': 1,
 'FWT': 1,
 'EET': 2,
 'UKR': 2,
 'BT': 3,
 'ZP4': 4,
 'ZP5': 5,
 'ZP6': 6,
 'WST': 8,
 'HKT': 8,
 'CCT': 8,
 'JST': 9,
 'KST': 9,
 'EAST': 10,
 'GST': 10,
 'NZT': 12,
 'NZST': 12,
 'IDLE': 12
}

TZ2 = {
 'ACDT': 10.5,
 'ACST': 9.5,
 'ADT': 3,
 'AEDT': 11, # hmm
 'AEST': 10, # hmm
 'AHDT': 9,
 'AHST': 10,
 'AST': 4,
 'AT': 2,
 'AWDT': -9,
 'AWST': -8,
 'BAT': -3,
 'BDST': -2,
 'BET': 11,
 'BST': -1,
 'BT': -3,
 'BZT2': 3,
 'CADT': -10.5,
 'CAST': -9.5,
 'CAT': 10,
 'CCT': -8,
 # 'CDT': 5,
 'CED': -2,
 'CET': -1,
 'CST': 6,
 'EAST': -10,
 # 'EDT': 4,
 'EED': -3,
 'EET': -2,
 'EEST': -3,
 'EST': 5,
 'FST': -2,
 'FWT': -1,
 'GMT': 0,
 'GST': -10,
 'HDT': 9,
 'HST': 10,
 'IDLE': -12,
 'IDLW': 12,
 # 'IST': -5.5,
 'IT': -3.5,
 'JST': -9,
 'JT': -7,
 'KST': -9,
 'MDT': 6,
 'MED': -2,
 'MET': -1,
 'MEST': -2,
 'MEWT': -1,
 'MST': 7,
 'MT': -8,
 'NDT': 2.5,
 'NFT': 3.5,
 'NT': 11,
 'NST': -6.5,
 'NZ': -11,
 'NZST': -12,
 'NZDT': -13,
 'NZT': -12,
 # 'PDT': 7,
 'PST': 8,
 'ROK': -9,
 'SAD': -10,
 'SAST': -9,
 'SAT': -9,
 'SDT': -10,
 'SST': -2,
 'SWT': -1,
 'USZ3': -4,
 'USZ4': -5,
 'USZ5': -6,
 'USZ6': -7,
 'UT': 0,
 'UTC': 0,
 'UZ10': -11,
 'WAT': 1,
 'WET': 0,
 'WST': -8,
 'YDT': 8,
 'YST': 9,
 'ZP4': -4,
 'ZP5': -5,
 'ZP6': -6
}

TZ3 = {
   'AEST': 10,
   'AEDT': 11
}

# TimeZones.update(TZ2) # do these have to be negated?
TimeZones.update(TZ1)
TimeZones.update(TZ3)

ZERO = timedelta(0)
HOUR = timedelta(hours=1)


class timez(tzinfo):
    
    def __init__(self, name):
        if name not in TimeZones: name = "UTC" #Make an error here
        self.__offset = timedelta(minutes = TimeZones[name] * 60)
        self.__name = name    

    def utcoffset(self, dt):
        return self.__offset
        
    def dst(self, dt):
        return ZERO
    
if __name__ == '__main__':
    print __doc__.strip()
