#!/usr/bin/env python
"""
swhack.py - Phenny Swhack Module
Copyright 2008, Sean B. Palmer, inamidst.com
Licensed under the Eiffel Forum License 2.

http://inamidst.com/phenny/
"""

import urllib

def swhack(phenny, input): 
   if not input.sender in ('#swhack', '#inamidst'): 
      return

   query = input.group(2)
   pattern = urllib.quote(query, safe='./')

   u = urllib.urlopen('http://swhack.com/scripts/tail/' + pattern)

   i = None
   for i, line in enumerate(u.readlines()): 
      line = line.rstrip('\r\n')
      if i == 0: 
         phenny.reply(line)
      else: phenny.say('[off] ' + line)
   if i is None: 
      phenny.reply('Sorry, no results found.')

   u.close()
# swhack.commands = ['swhack']

if __name__ == '__main__': 
   print __doc__.strip()
