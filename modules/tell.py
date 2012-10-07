#!/usr/bin/env python
"""
tell.py - Willie Tell and Ask Module
Copyright 2008, Sean B. Palmer, inamidst.com
Copyright 2012, Lior Ramati, firerogue517@gmail.com
Licensed under the Eiffel Forum License 2.

http://willie.dftba.net
"""

import os, re, time, random
import threading

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
                try: f.write(line + '\n')
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

def f_remind(willie, trigger):
    teller = trigger.nick

    verb, tellee, msg = trigger.groups()
    verb = verb.encode('utf-8')
    tellee = tellee.encode('utf-8')
    msg = msg.encode('utf-8')

    tellee_original = tellee.rstrip('.,:;')
    tellee = tellee_original.lower()

    if not os.path.exists(willie.tell_filename):
        return

    if len(tellee) > 20:
        return willie.reply('That nickname is too long.')
    if tellee.lower() == willie.nick.lower():
        return willie.reply('I\'m here now, you can tell me whatever you want!')

    timenow = time.strftime('%d %b %H:%MZ', time.gmtime())
    if not tellee in (teller.lower(), willie.nick, 'me'):
        willie.memory['tell_lock'].acquire()
        try:
            willie.memory['reminders'].setdefault(tellee, []).append((teller, verb, timenow, msg))
        finally:
            willie.memory['tell_lock'].release()

        response = "I'll pass that on when %s is around." % tellee_original

        willie.reply(response)
    elif teller.lower() == tellee:
        willie.say('You can %s yourself that.' % verb)
    else: willie.say("Hey, I'm not as stupid as Monty you know!")

    dumpReminders(willie.tell_filename, willie.memory['reminders'], willie.memory['tell_lock']) # @@ tell
f_remind.rule = ('$nick', ['tell', 'ask'], r'(\S+) (.*)')

def delete(willie, trigger):
    if not trigger.nick == trigger.sender: return
    tellee, msgno = trigger.group(3).split(' ')
    tellee = tellee.encode('utf-8').lower()
    msgno = int(msgno) # the msg # to delete
    teller = trigger.nick
    count = 0
    if tellee not in willie.memory['reminders']:
        willie.say("You haven't sent %s any messages!" % tellee)
    else:
        for entry in willie.memory['reminders'][tellee]:
            if entry[0] == teller: count += 1
            if count == msgno:
                willie.say("OK. Wont %s %s %s" % (entry[1], tellee, entry[3])) # verb, tellee, msg
                willie.memory['reminders'][tellee].remove(entry)
                dumpReminders(willie.tell_filename, willie.memory['reminders'], willie.memory['tell_lock'])
                return
        willie.reply("Invalid Message Number. Please check the number and try again")

def f_tell(willie, trigger):
    isPM = trigger.nick == trigger.sender
    try:
        cmd = trigger.group(2).lower()
        args = trigger.group(3).split(' ')
    except AttributeError: willie.reply("usage: .tell [del(ete)/sent/show] \x1Fargs\x0F") 
    else:
        if cmd[:3] == 'del':
            if (isPM): 
                if len(args) == 2:
                    try: int(args[1])
                    except: willie.reply("%s is not a number!" % args[1])
                    else: delete(willie, trigger)
                else: willie.reply("wrong number of args! (usage: .tell delete \x1Freceiver's nick\x0F \x1Fmessage number\x0F)")
            else: willie.reply("that command is PM only")
        elif cmd in ['show', 'list', 'view']:
            if (isPM):
                if len(args) == 1 and args[0]: show(willie, trigger)
                else: willie.reply("wrong number of args! (usage: .tell show \x1Freceiver's nick\x0F")
            else: willie.reply("that command is PM only")
        elif cmd == 'sent':
            if len(args) == 1 and args[0]: sent(willie, trigger)
            else: willie.reply("wrong number of args! (usage: .tell sent \x1Freceiver's nick\x0F")
        else: willie.reply("%s isn't a valid command. (usage: .tell [del(ete)/sent/show] \x1Fargs\x0F)" % cmd)
f_tell.rule = (['tell', 'ask'], r'(\S+) (.*)')

def show(willie, trigger):
    tellee = trigger.group(3).encode('utf-8').lower()
    teller = trigger.nick
    if not teller == trigger.sender:
        willie.reply("Sending you a PM with all the messages you sent %s" % tellee)
    if tellee in willie.memory['reminders']:
        count = 0
        for msg in willie.memory['reminders'][tellee]:
            if msg[0] == teller:
                count += 1
                willie.msg(teller, '%d: %s %s %s' % (count, msg[1], tellee, msg[3]))
    else: willie.msg(teller, "%s doesn't have any pending messages from you" % tellee)

def getReminders(willie, channel, key, tellee):
    lines = []
    template = "%s: %s <%s\x0F %s %s %s"
    today = time.strftime('%d %b',116, time.gmtime())

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

def sent(willie, trigger):
    tellee = trigger.group(3).encode('utf-8').lower()
    teller = trigger.nick
    msgFound = False
    if tellee in willie.memory['reminders']:
        for msg in willie.memory['reminders'][tellee]:
            if msg[0] == teller: 
                msgFound = True
                break
    response = "%s " + ("doesn't have any" if (msgFound) else "has") + " pending messages from you"
    willie.reply(response % tellee)

def message(willie, trigger):

    tellee = trigger.nick
    channel = trigger.sender

    if not os.path.exists(willie.tell_filename):
        return

    reminders = []
    remkeys = list(reversed(sorted(willie.memory['reminders'].keys())))

    for remkey in remkeys:
        if not remkey.endswith('*') or remkey.endswith(':'):
            if tellee.lower() == remkey:
                reminders.extend(getReminders(willie, channel, remkey, tellee))
        elif tellee.lower().startswith(remkey.rstrip('*:')):
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
