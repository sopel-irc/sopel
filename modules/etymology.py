#!/usr/bin/env python
"""
etymology.py - Phenny Etymology Module
Copyright 2007-9, Sean B. Palmer, inamidst.com
Licensed under the Eiffel Forum License 2.

http://inamidst.com/phenny/
"""

import re
import web
from tools import deprecated

etyuri = 'http://etymonline.com/?term=%s'
etysearch = 'http://etymonline.com/?search=%s'

r_definition = re.compile(r'(?ims)<dd[^>]*>.*?</dd>')
r_tag = re.compile(r'<(?!!)[^>]+>')
r_whitespace = re.compile(r'[\t\r\n ]+')

abbrs = [
   'cf', 'lit', 'etc', 'Ger', 'Du', 'Skt', 'Rus', 'Eng', 'Amer.Eng', 'Sp', 
   'Fr', 'N', 'E', 'S', 'W', 'L', 'Gen', 'J.C', 'dial', 'Gk', 
   '19c', '18c', '17c', '16c', 'St', 'Capt', 'obs', 'Jan', 'Feb', 'Mar', 
   'Apr', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec', 'c', 'tr', 'e', 'g'
]
t_sentence = r'^.*?(?<!%s)(?:\.(?= [A-Z0-9]|\Z)|\Z)'
r_sentence = re.compile(t_sentence % ')(?<!'.join(abbrs))

def unescape(s): 
   s = s.replace('&gt;', '>')
   s = s.replace('&lt;', '<')
   s = s.replace('&amp;', '&')
   return s

def text(html): 
   html = r_tag.sub('', html)
   html = r_whitespace.sub(' ', html)
   return unescape(html).strip()

def etymology(word): 
   # @@ <nsh> sbp, would it be possible to have a flag for .ety to get 2nd/etc
   # entries? - http://swhack.com/logs/2006-07-19#T15-05-29
   
   if len(word) > 25: 
      raise ValueError("Word too long: %s[...]" % word[:10])
   word = {'axe': 'ax/axe'}.get(word, word)

   bytes = web.get(etyuri % word)
   definitions = r_definition.findall(bytes)

   if not definitions: 
      return None

   defn = text(definitions[0])
   m = r_sentence.match(defn)
   if not m: 
      return None
   sentence = m.group(0)

   try: 
      sentence = unicode(sentence, 'iso-8859-1')
      sentence = sentence.encode('utf-8')
   except: pass

   maxlength = 275
   if len(sentence) > maxlength: 
      sentence = sentence[:maxlength]
      words = sentence[:-5].split(' ')
      words.pop()
      sentence = ' '.join(words) + ' [...]'

   sentence = '"' + sentence.replace('"', "'") + '"'
   return sentence + ' - ' + (etyuri % word)

@deprecated
def f_etymology(self, origin, match, args): 
   word = match.group(2)

   try: result = etymology(word.encode('utf-8'))
   except IOError: 
      msg = "Can't connect to etymonline.com (%s)" % (etyuri % word)
      self.msg(origin.sender, msg)
      return
   except AttributeError: 
      result = None

   if result is not None: 
      self.msg(origin.sender, result)
   else: 
      uri = etysearch % word
      msg = 'Can\'t find the etymology for "%s". Try %s' % (word, uri)
      self.msg(origin.sender, msg)
# @@ Cf. http://swhack.com/logs/2006-01-04#T01-50-22
f_etymology.rule = (['ety'], r"([A-Za-z0-9' .-]+)$")
f_etymology.thread = True
f_etymology.priority = 'high'

if __name__=="__main__": 
   import sys
   print etymology(sys.argv[1])
