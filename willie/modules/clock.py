"""
clock.py - Willie Clock Module
Copyright 2008-9, Sean B. Palmer, inamidst.com
Copyright 2012, Edward Powell, embolalia.net
Licensed under the Eiffel Forum License 2.

http://willie.dfbta.net
"""
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


def f_time(willie, trigger):
    """Returns the current time."""
    tz = trigger.group(2) or 'UTC'
    tz = tz.strip()
    goodtz = False

    #They didn't give us an argument, so do they want their own time?
    if not trigger.group(2) and willie.db:
        if trigger.nick in willie.db.preferences:
            utz = willie.db.preferences.get(trigger.nick, 'tz')
            if utz != '':
                tz = utz
                goodtz = True
        elif trigger.sender in willie.db.preferences:
            utz = willie.db.preferences.get(trigger.sender, 'tz')
            if utz != '':
                tz = utz
                goodtz = True
    if not goodtz:
        try:
            from pytz import all_timezones
            goodtz = (tz in all_timezones)
        except:
            pass
    #Not in pytz, either, so maybe it's another user.
    if not goodtz:
        if willie.db and tz in willie.db.preferences:
            utz = willie.db.preferences.get(tz, 'tz')
            if utz != '':
                tz = utz
    #If we still haven't found it at this point, well, fuck it.

    TZ = tz.upper()
    if len(tz) > 30:
        return

    if (TZ == 'UTC') or (TZ == 'Z'):
        msg = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
        willie.msg(trigger.sender, msg)
    elif r_local.match(tz):  # thanks to Mark Shoulsdon (clsn)
        locale.setlocale(locale.LC_TIME, (tz[1:-1], 'UTF-8'))
        msg = time.strftime("%A, %d %B %Y %H:%M:%SZ", time.gmtime())
        willie.msg(trigger.sender, msg)
    elif tz and tz[0] in ('+', '-') and 4 <= len(tz) <= 6:
        timenow = time.gmtime(time.time() + (int(tz[:3]) * 3600))
        msg = time.strftime("%a, %d %b %Y %H:%M:%S " + str(tz), timenow)
        willie.msg(trigger.sender, msg)
    else:
        try:
            t = float(tz)
        except ValueError:
            import os
            import re
            import subprocess
            r_tz = re.compile(r'^[A-Za-z]+(?:/[A-Za-z_]+)*$')
            if r_tz.match(tz) and os.path.isfile('/usr/share/zoneinfo/' + tz):
                cmd, PIPE = 'TZ=%s date' % tz, subprocess.PIPE
                proc = subprocess.Popen(cmd, shell=True, stdout=PIPE)
                willie.msg(trigger.sender, proc.communicate()[0])
            else:
                error = "Sorry, I don't know about the '%s' timezone or user." % tz
                willie.msg(trigger.sender, trigger.nick + ': ' + error)
        else:
            timenow = time.gmtime(time.time() + (t * 3600))
            msg = time.strftime("%a, %d %b %Y %H:%M:%S " + str(tz), timenow)
            willie.msg(trigger.sender, msg)
f_time.commands = ['t', 'time']
f_time.name = 't'
f_time.example = '.t UTC'


def beats(willie, trigger):
    """Shows the internet time in Swatch beats."""
    beats = ((time.time() + 3600) % 86400) / 86.4
    beats = int(math.floor(beats))
    willie.say('@%03i' % beats)
beats.commands = ['beats']
beats.priority = 'low'


def divide(input, by):
    return (input / by), (input % by)


def tock(willie, trigger):
    """Shows the time from the USNO's atomic clock."""
    u = urllib.urlopen('http://tycho.usno.navy.mil/cgi-bin/timer.pl')
    info = u.info()
    u.close()
    willie.say('"' + info['Date'] + '" - tycho.usno.navy.mil')
tock.commands = ['tock']
tock.priority = 'high'


def npl(willie, trigger):
    """Shows the time from NPL's SNTP server."""
    # for server in ('ntp1.npl.co.uk', 'ntp2.npl.co.uk'):
    client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client.sendto('\x1b' + 47 * '\0', ('ntp1.npl.co.uk', 123))
    data, address = client.recvfrom(1024)
    if data:
        buf = struct.unpack('B' * 48, data)
        d = dec('0.0')
        for i in range(8):
            d += dec(buf[32 + i]) * dec(str(math.pow(2, (3 - i) * 8)))
        d -= dec(2208988800L)
        a, b = str(d).split('.')
        f = '%Y-%m-%d %H:%M:%S'
        result = datetime.datetime.fromtimestamp(d).strftime(f) + '.' + b[:6]
        willie.say(result + ' - ntp1.npl.co.uk')
    else:
        willie.say('No data received, sorry')
npl.commands = ['npl']
npl.priority = 'high'


def update_user(willie, trigger):
    """
    Set your preferred time zone. Most timezones will work, but it's best to use
    one from http://dft.ba/-tz
    """
    if willie.db:
        tz = trigger.group(2)
        goodtz = False
        #We don't see it in our short db, so let's give pytz a try
        try:
            from pytz import all_timezones
            goodtz = (tz in all_timezones)
        except:
            pass

        if not goodtz:
            willie.reply("I don't know that time zone.")
        else:
            willie.db.preferences.update(trigger.nick, {'tz': tz})
            if len(tz) < 7:
                willie.say("Okay, " + trigger.nick +
                           ", but you should use one from http://dft.ba/-tz if you use DST.")
            else:
                willie.reply('I now have you in the %s time zone.' % tz)
    else:
        willie.reply("I can't remember that; I don't have a database.")
update_user.commands = ['settz']


def update_channel(willie, trigger):
    """
    Set the preferred time zone for the channel.
    """
    if willie.db:
        tz = trigger.group(2)
        goodtz = False
        #We don't see it in our short db, so let's give pytz a try
        try:
            from pytz import all_timezones
            goodtz = (tz in all_timezones)
        except:
            pass

        if not goodtz:
            willie.reply("I don't know that time zone.")
        else:
            willie.db.preferences.update(trigger.sender, {'tz': tz})
            if len(tz) < 7:
                willie.say("Okay, " + trigger.nick +
                           ", but you should use one from http://dft.ba/-tz if you use DST.")
            else:
                willie.say("Gotcha, " + trigger.nick)
    else:
        willie.reply("I can't remember that; I don't have a database.")
update_channel.commands = ['channeltz']

if __name__ == '__main__':
    print __doc__.strip()
