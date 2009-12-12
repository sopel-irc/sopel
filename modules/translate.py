#!/usr/bin/env python
# coding=utf-8
"""
translate.py - Phenny Translation Module
Copyright 2008, Sean B. Palmer, inamidst.com
Licensed under the Eiffel Forum License 2.

http://inamidst.com/phenny/
"""

import re, urllib
import web

r_json = re.compile(r'^[,:{}\[\]0-9.\-+Eaeflnr-u \n\r\t]+$')
r_string = re.compile(r'("(\\.|[^"\\])*")')
env = {'__builtins__': None, 'null': None, 
       'true': True, 'false': False}

def json(text): 
   """Evaluate JSON text safely (we hope)."""
   if r_json.match(r_string.sub('', text)): 
      text = r_string.sub(lambda m: 'u' + m.group(1), text)
      return eval(text.strip(' \t\r\n'), env, {})
   raise ValueError('Input must be serialised JSON.')

def detect(text): 
   uri = 'http://ajax.googleapis.com/ajax/services/language/detect'
   q = urllib.quote(text)
   bytes = web.get(uri + '?q=' + q + '&v=1.0')
   result = json(bytes)
   try: return result['responseData']['language']
   except Exception: return None

def translate(text, input, output): 
   uri = 'http://ajax.googleapis.com/ajax/services/language/translate'
   q = urllib.quote(text)
   pair = input + '%7C' + output
   bytes = web.get(uri + '?q=' + q + '&v=1.0&langpair=' + pair)
   result = json(bytes)
   try: return result['responseData']['translatedText'].encode('cp1252')
   except Exception: return None

def tr(phenny, context): 
   """Translates a phrase, with an optional language hint."""
   input, output, phrase = context.groups()

   phrase = phrase.encode('utf-8')

   if (len(phrase) > 350) and (not context.admin): 
      return phenny.reply('Phrase must be under 350 characters.')

   input = input or detect(phrase)
   if not input: 
      err = 'Unable to guess your crazy moon language, sorry.'
      return phenny.reply(err)
   input = input.encode('utf-8')
   output = (output or 'en').encode('utf-8')

   if input != output: 
      msg = translate(phrase, input, output)
      if msg: 
         msg = msg.replace('&#39;', "'")
         msg = '"%s" (%s to %s, translate.google.com)' % (msg, input, output)
      else: msg = 'The %s to %s translation failed, sorry!' % (input, output)

      phenny.reply(msg)
   else: phenny.reply('Language guessing failed, so try suggesting one!')

tr.rule = ('$nick', ur'(?:([a-z]{2}) +)?(?:([a-z]{2}) +)?["“](.+?)["”]\? *$')
tr.example = '$nickname: "mon chien"? or $nickname: fr "mon chien"?'
tr.priority = 'low'

def mangle(phenny, input): 
   phrase = input.group(2).encode('utf-8')
   for lang in ['fr', 'de', 'es', 'it', 'ja']: 
      backup = phrase
      phrase = translate(phrase, 'en', lang)
      if not phrase: 
         phrase = backup
         break
      __import__('time').sleep(0.5)

      backup = phrase
      phrase = translate(phrase, lang, 'en')
      if not phrase: 
         phrase = backup
         break
      __import__('time').sleep(0.5)

   phenny.reply(phrase or 'ERRORS SRY')
mangle.commands = ['mangle']

if __name__ == '__main__': 
   print __doc__.strip()
