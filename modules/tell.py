#!/usr/bin/env python
"""
tell.py - Jenni Tell and Ask Module
Copyright 2008, Sean B. Palmer, inamidst.com
Licensed under the Eiffel Forum License 2.

http://inamidst.com/phenny/
"""

import os, re, time, random
import web

maximum = 4
lispchannels = frozenset([ '#lisp', '#scheme', '#opendarwin', '#macdev',
'#fink', '#jedit', '#dylan', '#emacs', '#xemacs', '#colloquy', '#adium',
'#growl', '#chicken', '#quicksilver', '#svn', '#slate', '#squeak', '#wiki',
'#nebula', '#myko', '#lisppaste', '#pearpc', '#fpc', '#hprog',
'#concatenative', '#slate-users', '#swhack', '#ud', '#t', '#compilers',
'#erights', '#esp', '#scsh', '#sisc', '#haskell', '#rhype', '#sicp', '#darcs',
'#hardcider', '#lisp-it', '#webkit', '#launchd', '#mudwalker', '#darwinports',
'#muse', '#chatkit', '#kowaleba', '#vectorprogramming', '#opensolaris',
'#oscar-cluster', '#ledger', '#cairo', '#idevgames', '#hug-bunny', '##parsers',
'#perl6', '#sdlperl', '#ksvg', '#rcirc', '#code4lib', '#linux-quebec',
'#programmering', '#maxima', '#robin', '##concurrency', '#paredit' ])

def loadReminders(fn):
    result = {}
    f = open(fn)
    for line in f:
        line = line.strip()
        if line:
            try: tellee, teller, verb, timenow, msg = line.split('\t', 4)
            except ValueError: continue # @@ hmm
            result.setdefault(tellee, []).append((teller, verb, timenow, msg))
    f.close()
    return result

def dumpReminders(fn, data):
    f = open(fn, 'w')
    for tellee in data.iterkeys():
        for remindon in data[tellee]:
            line = '\t'.join((tellee,) + remindon)
            try: f.write(line + '\n')
            except IOError: break
    try: f.close()
    except IOError: pass
    return True

def setup(self):
    fn = self.nick + '-' + self.config.host + '.tell.db'
    self.tell_filename = os.path.join(os.path.expanduser('~/.jenni'), fn)
    if not os.path.exists(self.tell_filename):
        try: f = open(self.tell_filename, 'w')
        except OSError: pass
        else:
            f.write('')
            f.close()
    self.reminders = loadReminders(self.tell_filename) # @@ tell

def f_remind(jenni, input):
    teller = input.nick

    # @@ Multiple comma-separated tellees? Cf. Terje, #swhack, 2006-04-15
    verb, tellee, msg = input.groups()
    verb = verb.encode('utf-8')
    tellee = tellee.encode('utf-8')
    msg = msg.encode('utf-8')

    tellee_original = tellee.rstrip('.,:;')
    tellee = tellee_original.lower()

    if not os.path.exists(jenni.tell_filename):
        return

    if len(tellee) > 20:
        return jenni.reply('That nickname is too long.')

    timenow = time.strftime('%d %b %H:%MZ', time.gmtime())
    if not tellee in (teller.lower(), jenni.nick, 'me'): # @@
        # @@ <deltab> and year, if necessary
        warn = False
        if not jenni.reminders.has_key(tellee):
            jenni.reminders[tellee] = [(teller, verb, timenow, msg)]
        else:
            # if len(jenni.reminders[tellee]) >= maximum:
            #     warn = True
            jenni.reminders[tellee].append((teller, verb, timenow, msg))
        # @@ Stephanie's augmentation
        response = "I'll pass that on when %s is around." % tellee_original
        # if warn: response += (" I'll have to use a pastebin, though, so " +
        #                              "your message may get lost.")

        rand = random.random()
        if rand > 0.9999: response = "yeah, yeah"
        elif rand > 0.999: response = "yeah, sure, whatever"

        jenni.reply(response)
    elif teller.lower() == tellee:
        jenni.say('You can %s yourself that.' % verb)
    else: jenni.say("Hey, I'm not as stupid as Monty you know!")

    dumpReminders(jenni.tell_filename, jenni.reminders) # @@ tell
f_remind.rule = ('$nick', ['tell', 'ask'], r'(\S+) (.*)')
f_remind.rate = 45

def getReminders(jenni, channel, key, tellee):
    lines = []
    template = "%s: %s <%s> %s %s %s"
    today = time.strftime('%d %b', time.gmtime())

    for (teller, verb, datetime, msg) in jenni.reminders[key]:
        if datetime.startswith(today):
            datetime = datetime[len(today)+1:]
        lines.append(template % (tellee, datetime, teller, verb, tellee, msg))

    try: del jenni.reminders[key]
    except KeyError: jenni.msg(channel, 'Er...')
    return lines

def message(jenni, input):
    if not input.sender.startswith('#'): return

    tellee = input.nick
    channel = input.sender

    if not os: return
    if not os.path.exists(jenni.tell_filename):
        return

    reminders = []
    remkeys = list(reversed(sorted(jenni.reminders.keys())))
    for remkey in remkeys:
        if not remkey.endswith('*') or remkey.endswith(':'):
            if tellee.lower() == remkey:
                reminders.extend(getReminders(jenni, channel, remkey, tellee))
        elif tellee.lower().startswith(remkey.rstrip('*:')):
            reminders.extend(getReminders(jenni, channel, remkey, tellee))

    for line in reminders[:maximum]:
        jenni.say(line)

    if reminders[maximum:]:
        jenni.say('Further messages sent privately')
        for line in reminders[maximum:]:
            jenni.msg(tellee, line)

    if len(jenni.reminders.keys()) != remkeys:
        dumpReminders(jenni.tell_filename, jenni.reminders) # @@ tell
message.rule = r'(.*)'
message.priority = 'low'

if __name__ == '__main__':
    print __doc__.strip()
