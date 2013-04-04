"""
tell.py - Willie Tell and Ask Module
Copyright 2008, Sean B. Palmer, inamidst.com
Licensed under the Eiffel Forum License 2.

http://willie.dftba.net
"""

import os
import re
import time
import datetime
import pytz
import random
import threading
from willie.tools import Nick

maximum = 4

def loadReminders(fn, lock):
    lock.acquire()
    try:
        result = {}
        f = open(fn)
        for line in f:
            line = line.strip()
            if line:
                try: tellee, teller, verb, timenow, msg = line.split('\t', 4)
                except ValueError: continue # @@ hmm
                result.setdefault(tellee, []).append((teller, verb, timenow, msg))
        f.close()
    finally:
        lock.release()
    return result

def dumpReminders(fn, data, lock):
    lock.acquire()
    try:
        f = open(fn, 'w')
        for tellee in data.iterkeys():
            for remindon in data[tellee]:
                line = '\t'.join((tellee,) + remindon)
                try: f.write((line + '\n').encode('utf-8'))
                except IOError: break
        try: f.close()
        except IOError: pass
    finally:
        lock.release()
    return True

def setup(self):
    fn = self.nick + '-' + self.config.host + '.tell.db'
    self.tell_filename = os.path.join(self.config.dotdir, fn)
    if not os.path.exists(self.tell_filename):
        try: f = open(self.tell_filename, 'w')
        except OSError: pass
        else:
            f.write('')
            f.close()
    self.memory['tell_lock'] = threading.Lock()
    self.memory['reminders'] = loadReminders(self.tell_filename, self.memory['tell_lock'])


def get_user_time(willie, nick):
    tz = 'UTC'
    tformat = None
    if willie.db and nick in willie.db.preferences:
            tz = willie.db.preferences.get(nick, 'tz') or 'UTC'
            tformat = willie.db.preferences.get(nick, 'time_format')
    if tz not in pytz.all_timezones_set:
        tz = 'UTC'
    return (pytz.timezone(tz.strip()), tformat or '%Y-%m-%d %H:%M:%S %Z')


def f_remind(willie, trigger):
    teller = trigger.nick

    verb, tellee, msg = trigger.groups()
    verb = unicode(verb)
    tellee = Nick(tellee.rstrip('.,:;'))
    msg = unicode(msg)

    if not os.path.exists(willie.tell_filename):
        return

    if len(tellee) > 20:
        return willie.reply('That nickname is too long.')
    if tellee == willie.nick:
        return willie.reply("I'm here now, you can tell me whatever you want!")
    
    tz, tformat = get_user_time(willie, tellee)
    print tellee, tz, tformat
    timenow = datetime.datetime.now(tz).strftime(tformat)
    if not tellee in (Nick(teller), willie.nick, 'me'):
        willie.memory['tell_lock'].acquire()
        try:
            if not willie.memory['reminders'].has_key(tellee):
                willie.memory['reminders'][tellee] = [(teller, verb, timenow, msg)]
            else:
                willie.memory['reminders'][tellee].append((teller, verb, timenow, msg))
        finally:
            willie.memory['tell_lock'].release()

        response = "I'll pass that on when %s is around." % tellee

        willie.reply(response)
    elif Nick(teller) == tellee:
        willie.say('You can %s yourself that.' % verb)
    else: willie.say("Hey, I'm not as stupid as Monty you know!")

    dumpReminders(willie.tell_filename, willie.memory['reminders'], willie.memory['tell_lock']) # @@ tell
f_remind.rule = ('$nick', ['tell', 'ask'], r'(\S+) (.*)')

def getReminders(willie, channel, key, tellee):
    lines = []
    template = "%s: %s <%s> %s %s %s"
    today = time.strftime('%d %b', time.gmtime())

    willie.memory['tell_lock'].acquire()
    try:
        for (teller, verb, datetime, msg) in willie.memory['reminders'][key]:
            if datetime.startswith(today):
                datetime = datetime[len(today)+1:]
            lines.append(template % (tellee, datetime, teller, verb, tellee, msg))

        try: del willie.memory['reminders'][key]
        except KeyError: willie.msg(channel, 'Er...')
    finally:
        willie.memory['tell_lock'].release()
    return lines

def message(willie, trigger):

    tellee = trigger.nick
    channel = trigger.sender

    if not os.path.exists(willie.tell_filename):
        return

    reminders = []
    remkeys = list(reversed(sorted(willie.memory['reminders'].keys())))

    for remkey in remkeys:
        if not remkey.endswith('*') or remkey.endswith(':'):
            if tellee == remkey:
                reminders.extend(getReminders(willie, channel, remkey, tellee))
        elif tellee.startswith(remkey.rstrip('*:')):
            reminders.extend(getReminders(willie, channel, remkey, tellee))

    for line in reminders[:maximum]:
        willie.say(line)

    if reminders[maximum:]:
        willie.say('Further messages sent privately')
        for line in reminders[maximum:]:
            willie.msg(tellee, line)

    if len(willie.memory['reminders'].keys()) != remkeys:
        dumpReminders(willie.tell_filename, willie.memory['reminders'], willie.memory['tell_lock']) # @@ tell
message.rule = r'(.*)'
message.priority = 'low'

if __name__ == '__main__':
    print __doc__.strip()
