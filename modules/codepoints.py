#!/usr/bin/env python
"""
codepoints.py - Phenny Codepoints Module
Copyright 2008, Sean B. Palmer, inamidst.com
Licensed under the Eiffel Forum License 2.

http://inamidst.com/phenny/
"""

import re, unicodedata
from itertools import islice

def about(u, cp=None, name=None): 
   if cp is None: 
      cp = ord(u)
   if name is None: 
      try: name = unicodedata.name(u)
      except ValueError: 
         return 'U+%04X (No name found)' % cp

   if not unicodedata.combining(u): 
      template = 'U+%04X %s (%s)'
   else: template = 'U+%04X %s (\xe2\x97\x8c%s)'
   return template % (cp, name, u.encode('utf-8'))

def codepoint_simple(arg): 
   arg = arg.upper()

   r_label = re.compile('\\b' + arg.replace(' ', '.*\\b') + '\\b')

   results = []
   for cp in xrange(0xFFFF): 
      u = unichr(cp)
      try: name = unicodedata.name(u)
      except ValueError: continue

      if r_label.search(name): 
         results.append((len(name), u, cp, name))
   if not results: 
      r_label = re.compile('\\b' + arg.replace(' ', '.*\\b'))
      for cp in xrange(0xFFFF): 
         u = unichr(cp)
         try: name = unicodedata.name(u)
         except ValueError: continue

         if r_label.search(name): 
            results.append((len(name), u, cp, name))

   if not results: 
      return None

   length, u, cp, name = sorted(results)[0]
   return about(u, cp, name)

def codepoint_extended(arg): 
   arg = arg.upper()
   try: r_search = re.compile(arg)
   except: raise ValueError('Broken regexp: %r' % arg)

   for cp in xrange(1, 0x10FFFF): 
      u = unichr(cp)
      name = unicodedata.name(u, '-')

      if r_search.search(name): 
         yield about(u, cp, name)

def u(phenny, input): 
   """Look up unicode information."""
   arg = input.bytes[3:]
   # phenny.msg('#inamidst', '%r' % arg)
   if not arg: 
      return phenny.reply('You gave me zero length input.')
   elif not arg.strip(' '): 
      if len(arg) > 1: return phenny.reply('%s SPACEs (U+0020)' % len(arg))
      return phenny.reply('1 SPACE (U+0020)')

   # @@ space
   if set(arg.upper()) - set(
      'ABCDEFGHIJKLMNOPQRSTUVWYXYZ0123456789- .?+*{}[]\\/^$'): 
      printable = False
   elif len(arg) > 1: 
      printable = True
   else: printable = False

   if printable: 
      extended = False
      for c in '.?+*{}[]\\/^$': 
         if c in arg: 
            extended = True
            break

      if len(arg) == 4: 
         try: u = unichr(int(arg, 16))
         except ValueError: pass
         else: return phenny.say(about(u))

      if extended: 
         # look up a codepoint with regexp
         results = list(islice(codepoint_extended(arg), 4))
         for i, result in enumerate(results): 
            if (i < 2) or ((i == 2) and (len(results) < 4)): 
               phenny.say(result)
            elif (i == 2) and (len(results) > 3): 
               phenny.say(result + ' [...]')
         if not results: 
            phenny.reply('Sorry, no results')
      else: 
         # look up a codepoint freely
         result = codepoint_simple(arg)
         if result is not None: 
            phenny.say(result)
         else: phenny.reply("Sorry, no results for %r." % arg)
   else: 
      text = arg.decode('utf-8')
      # look up less than three podecoints
      if len(text) <= 3: 
         for u in text: 
            phenny.say(about(u))
      # look up more than three podecoints
      elif len(text) <= 10: 
         phenny.reply(' '.join('U+%04X' % ord(c) for c in text))
      else: phenny.reply('Sorry, your input is too long!')
u.commands = ['u']
u.example = '.u 203D'

def bytes(phenny, input): 
   """Show the input as pretty printed bytes."""
   b = input.bytes
   phenny.reply('%r' % b[b.find(' ') + 1:])
bytes.commands = ['bytes']
bytes.example = '.bytes \xe3\x8b\xa1'

if __name__ == '__main__': 
   print __doc__.strip()
