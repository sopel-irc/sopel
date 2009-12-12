#!/usr/bin/env python
"""
wiktionary.py - Phenny Wiktionary Module
Copyright 2009, Sean B. Palmer, inamidst.com
Licensed under the Eiffel Forum License 2.

http://inamidst.com/phenny/
"""

import re
import web

uri = 'http://en.wiktionary.org/w/index.php?title=%s&printable=yes'
r_tag = re.compile(r'<[^>]+>')
r_ul = re.compile(r'(?ims)<ul>.*?</ul>')

def text(html): 
   text = r_tag.sub('', html).strip()
   text = text.replace('\n', ' ')
   text = text.replace('\r', '')
   text = text.replace('(intransitive', '(intr.')
   text = text.replace('(transitive', '(trans.')
   return text

def wiktionary(word): 
   bytes = web.get(uri % web.urllib.quote(word.encode('utf-8')))
   bytes = r_ul.sub('', bytes)

   mode = None
   etymology = None
   definitions = {}
   for line in bytes.splitlines(): 
      if 'id="Etymology"' in line: 
         mode = 'etymology'
      elif 'id="Noun"' in line: 
         mode = 'noun'
      elif 'id="Verb"' in line: 
         mode = 'verb'
      elif 'id="Adjective"' in line: 
         mode = 'adjective'
      elif 'id="Adverb"' in line: 
         mode = 'adverb'
      elif 'id="Interjection"' in line: 
         mode = 'interjection'
      elif 'id="Particle"' in line: 
         mode = 'particle'
      elif 'id="Preposition"' in line: 
         mode = 'preposition'
      elif 'id="' in line: 
         mode = None

      elif (mode == 'etmyology') and ('<p>' in line): 
         etymology = text(line)
      elif (mode is not None) and ('<li>' in line): 
         definitions.setdefault(mode, []).append(text(line))

      if '<hr' in line: 
         break
   return etymology, definitions

parts = ('preposition', 'particle', 'noun', 'verb', 
   'adjective', 'adverb', 'interjection')

def format(word, definitions, number=2): 
   result = '%s' % word.encode('utf-8')
   for part in parts: 
      if definitions.has_key(part): 
         defs = definitions[part][:number]
         result += u' \u2014 '.encode('utf-8') + ('%s: ' % part)
         n = ['%s. %s' % (i + 1, e.strip(' .')) for i, e in enumerate(defs)]
         result += ', '.join(n)
   return result.strip(' .,')

def w(phenny, input): 
   word = input.group(2)
   etymology, definitions = wiktionary(word)
   if not definitions: 
      phenny.say("Couldn't get any definitions for %s." % word)
      return

   result = format(word, definitions)
   if len(result) < 150: 
      result = format(word, definitions, 3)
   if len(result) < 150: 
      result = format(word, definitions, 5)

   if len(result) > 300: 
      result = result[:295] + '[...]'
   phenny.say(result)
w.commands = ['w']
w.example = '.w bailiwick'

if __name__ == '__main__': 
   print __doc__.strip()
