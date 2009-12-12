#!/usr/bin/env python
"""
dict.py - Phenny Dictionary Module
Copyright 2008-9, Sean B. Palmer, inamidst.com
Licensed under the Eiffel Forum License 2.

http://inamidst.com/phenny/
"""

import re, urllib
import web
from tools import deprecated

r_li = re.compile(r'(?ims)<li>.*?</li>')
r_tag = re.compile(r'<[^>]+>')
r_parens = re.compile(r'(?<=\()(?:[^()]+|\([^)]+\))*(?=\))')
r_word = re.compile(r'^[A-Za-z0-9\' -]+$')

uri = 'http://encarta.msn.com/dictionary_/%s.html'
r_info = re.compile(
   r'(?:ResultBody"><br /><br />(.*?)&nbsp;)|(?:<b>(.*?)</b>)'
)

def dict(phenny, input): 
   word = input.group(2)
   word = urllib.quote(word.encode('utf-8'))

   def trim(thing): 
      if thing.endswith('&nbsp;'): 
         thing = thing[:-6]
      return thing.strip(' :.')

   bytes = web.get(uri % word)
   results = {}
   wordkind = None
   for kind, sense in r_info.findall(bytes): 
      kind, sense = trim(kind), trim(sense)
      if kind: wordkind = kind
      elif sense: 
         results.setdefault(wordkind, []).append(sense)
   result = input.group(2).encode('utf-8') + ' - '
   for key in sorted(results.keys()): 
      if results[key]: 
         result += (key or '') + ' 1. ' + results[key][0]
         if len(results[key]) > 1: 
            result += ', 2. ' + results[key][1]
         result += '; '
   result = result.rstrip('; ')
   if result.endswith('-') and (len(result) < 30): 
      phenny.reply('Sorry, no definition found.')
   else: phenny.say(result)
dict.commands = ['dict']

if __name__ == '__main__': 
   print __doc__.strip()
