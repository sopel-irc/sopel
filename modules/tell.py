#!/usr/bin/env python
"""
tell.py - Phenny Tell and Ask Module
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
         tellee, teller, verb, timenow, msg = line.split('\t', 4)
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
   self.tell_filename = os.path.join(os.path.expanduser('~/.phenny'), fn)
   if not os.path.exists(self.tell_filename): 
      try: f = open(self.tell_filename, 'w')
      except OSError: pass
      else: 
         f.write('')
         f.close()
   self.reminders = loadReminders(self.tell_filename) # @@ tell

def f_remind(phenny, input): 
   teller = input.nick

   # @@ Multiple comma-separated tellees? Cf. Terje, #swhack, 2006-04-15
   verb, tellee, msg = input.groups()
   verb = verb.encode('utf-8')
   tellee = tellee.encode('utf-8')
   msg = msg.encode('utf-8')

   tellee_original = tellee.rstrip('.,:;')
   tellee = tellee_original.lower()

   if not os.path.exists(phenny.tell_filename): 
      return

   if len(tellee) > 20: 
      return phenny.reply('That nickname is too long.')

   timenow = time.strftime('%d %b %H:%MZ', time.gmtime())
   if not tellee in (teller.lower(), phenny.nick, 'me'): # @@
      # @@ <deltab> and year, if necessary
      warn = False
      if not phenny.reminders.has_key(tellee): 
         phenny.reminders[tellee] = [(teller, verb, timenow, msg)]
      else: 
         if len(phenny.reminders[tellee]) >= maximum: 
            warn = True
         phenny.reminders[tellee].append((teller, verb, timenow, msg))
      # @@ Stephanie's augmentation
      response = "I'll pass that on when %s is around." % tellee_original
      if warn: response += (" I'll have to use a pastebin, though, so " + 
                            "your message may get lost.")

      rand = random.random()
      if rand > 0.9999: response = "yeah, yeah"
      elif rand > 0.999: response = "yeah, sure, whatever"

      phenny.reply(response)
   elif teller.lower() == tellee: 
      phenny.say('You can %s yourself that.' % verb)
   else: phenny.say("Hey, I'm not as stupid as Monty you know!")

   dumpReminders(phenny.tell_filename, phenny.reminders) # @@ tell
f_remind.rule = ('$nick', ['tell', 'ask'], r'(\S+) (.*)')

def getReminders(phenny, channel, key, tellee): 
   lines = []
   template = "%s: %s <%s> %s %s %s"
   today = time.strftime('%d %b', time.gmtime())

   for (teller, verb, datetime, msg) in phenny.reminders[key]: 
      if datetime.startswith(today): 
         datetime = datetime[len(today)+1:]
      lines.append(template % (tellee, datetime, teller, verb, tellee, msg))

   try: del phenny.reminders[key]
   except KeyError: phenny.msg(channel, 'Er...')
   return lines

def message(phenny, input): 
   if not input.sender.startswith('#'): return

   tellee = input.nick
   channel = input.sender

   if not os.path.exists(phenny.tell_filename): 
      return

   reminders = []
   remkeys = list(reversed(sorted(phenny.reminders.keys())))
   for remkey in remkeys: 
      if not remkey.endswith('*') or remkey.endswith(':'): 
         if tellee.lower() == remkey: 
            reminders.extend(getReminders(phenny, channel, remkey, tellee))
      elif tellee.lower().startswith(remkey.rstrip('*:')): 
         reminders.extend(getReminders(phenny, channel, remkey, tellee))

   for line in reminders[:maximum]: 
      phenny.say(line)

   if reminders[maximum:]: 
      try: 
         if origin.sender in lispchannels: 
            chan = origin.sender
         else: chan = 'None'

         result = web.post('http://paste.lisp.org/submit', 
            {'channel': chan, 
             'username': phenny.nick, 
             'title': 'Further Messages for %s' % tellee, 
             'colorize': 'None', 
             'text': '\n'.join(reminders[maximum:]) + '\n', 
             'captcha': 'lisp', 
             'captchaid': 'bdf447484f62a3e8b23816f9acee79d9'
            }
         )
         uris = re.findall('http://paste.lisp.org/display/\d+', result)
         uri = list(reversed(uris)).pop()
         if not origin.sender in lispchannels: 
            message = '%s: see %s for further messages' % (tellee, uri)
            phenny.say(message)
      except: 
         error = '[Sorry, some messages were elided and lost...]'
         phenny.say(error)

   if len(phenny.reminders.keys()) != remkeys: 
      dumpReminders(phenny.tell_filename, phenny.reminders) # @@ tell
message.rule = r'(.*)'
message.priority = 'low'

if __name__ == '__main__': 
   print __doc__.strip()
