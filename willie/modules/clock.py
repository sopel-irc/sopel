"""
clock.py - Willie Clock Module
Copyright 2008-9, Sean B. Palmer, inamidst.com
Copyright 2012, Edward Powell, embolalia.net
Licensed under the Eiffel Forum License 2.

http://willie.dfbta.net
"""

import re, math, time, urllib, locale, socket, struct, datetime
from decimal import Decimal as dec

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

r_local = re.compile(r'\([a-z]+_[A-Z]+\)')

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
    #They gave us a timezone (or there's no tz column), so let's find it
    #Though, I think this might be duplicated work from below..?
    else: goodtz = tz in TimeZones
    #We don't see it in our short db, so let's give pytz a try
    if not goodtz:
        try:
            from pytz import all_timezones
            goodtz = (tz in all_timezones)
        except: pass
    #Not in pytz, either, so maybe it's another user.
    if not goodtz:
        if willie.db and tz in willie.db.preferences:
            utz = willie.db.preferences.get(tz, 'tz')
            if utz != '': tz = utz
    #If we still haven't found it at this point, well, fuck it.

    TZ = tz.upper()
    if len(tz) > 30: return

    if (TZ == 'UTC') or (TZ == 'Z'):
        msg = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
        willie.msg(trigger.sender, msg)
    elif r_local.match(tz): # thanks to Mark Shoulsdon (clsn)
        locale.setlocale(locale.LC_TIME, (tz[1:-1], 'UTF-8'))
        msg = time.strftime("%A, %d %B %Y %H:%M:%SZ", time.gmtime())
        willie.msg(trigger.sender, msg)
    elif TimeZones.has_key(TZ):
        offset = TimeZones[TZ] * 3600
        timenow = time.gmtime(time.time() + offset)
        msg = time.strftime("%a, %d %b %Y %H:%M:%S " + str(TZ), timenow)
        willie.msg(trigger.sender, msg)
    elif tz and tz[0] in ('+', '-') and 4 <= len(tz) <= 6:
        timenow = time.gmtime(time.time() + (int(tz[:3]) * 3600))
        msg = time.strftime("%a, %d %b %Y %H:%M:%S " + str(tz), timenow)
        willie.msg(trigger.sender, msg)
    else:
        try: t = float(tz)
        except ValueError:
            import os, re, subprocess
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
    else: willie.say('No data received, sorry')
npl.commands = ['npl']
npl.priority = 'high'

def update_user(willie, trigger):
    """
    Set your preferred time zone. Most timezones will work, but it's best to use
    one from http://dft.ba/-tz
    """
    if willie.db:
        tz = trigger.group(2)
        goodtz = tz in TimeZones
        #We don't see it in our short db, so let's give pytz a try
        if not goodtz:
            try:
                from pytz import all_timezones
                goodtz = (tz in all_timezones)
            except: pass
        
        if not goodtz:
            willie.reply("I don't know that time zone.")
        else:
            willie.db.preferences.update(trigger.nick, {'tz': tz})
            if len(tz) < 7:
                willie.say("Okay, "+trigger.nick+
              ", but you should use one from http://dft.ba/-tz if you use DST.")
            else: willie.reply('I now have you in the %s time zone.' %tz)
    else:
        willie.reply("I can't remember that; I don't have a database.")
update_user.commands = ['settz']

def update_channel(willie, trigger):
    """
    Set the preferred time zone for the channel.
    """
    if willie.db:
        tz = trigger.group(2)
        goodtz = tz in TimeZones
        #We don't see it in our short db, so let's give pytz a try
        if not goodtz:
            try:
                from pytz import all_timezones
                goodtz = (tz in all_timezones)
            except: pass
        
        if not goodtz:
            willie.reply("I don't know that time zone.")
        else:
            willie.db.preferences.update(trigger.sender, {'tz': tz})
            if len(tz) < 7:
                willie.say("Okay, "+trigger.nick+
              ", but you should use one from http://dft.ba/-tz if you use DST.")
            else: willie.say("Gotcha, " + trigger.nick)
    else:
        willie.reply("I can't remember that; I don't have a database.")
update_channel.commands = ['channeltz']

if __name__ == '__main__':
    print __doc__.strip()
