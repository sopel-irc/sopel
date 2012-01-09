#!/usr/bin/env python
"""
wa.py - NationStates WA tools for Phenny
Copyright 2011, Edward D. Powell, embolalia.net
Licensed under the Eiffel Forum License 2.

http://inamidst.com/phenny/
"""

import MySQLdb, re

wa_db = 'WA'
wa_host = 'embolalia.net'
wa_user = '********'
wa_pass = '********'

db = MySQLdb.connect(host=wa_host, user=wa_user, passwd=wa_pass, db=wa_db)
cur = db.cursor()

def whats(phenny, input):
   """Looks up a NationStates-related abbreviation or WA resolution"""
   givenum = 1
   #Retrieve resolution number and council
   w, abbr = input.groups()
   resd = re.match('(GA|SC|UN)(#| )*(\d*)', abbr)
   if resd:
      givenum = 0
      result = [resd.group(1), resd.group(3), abbr, None]
      if result[0] == 'GA': result[0] = 'G'
      elif result[0] == 'SC': result[0] = 'S'
      else: result[0] = 'U'
   else:      
      cur.execute("SELECT * FROM ABBRS WHERE Abbr = \"" + abbr + "\"")
      result = cur.fetchone()
   
   if result is None:
      phenny.say("Your guess is as good as mine, mate.")
   elif result[3] is not None:
      phenny.say(abbr + ' is ' + result[3])
   elif result[0] is not 'G':
      phenny.say('Sorry, ' + input.nick + ', I don\'t have data on that council yet.')
   else:
      council, number = result[0], result[1]
      num = str(number)
   
      #Look up full resolution name
      select = "SELECT * FROM RESOLUTIONS WHERE Council = \'"
      cur.execute(select + council + "\' AND Number = " +  num)
      
      message = makemessage(abbr, council, num, cur.fetchone(), givenum)
      
      phenny.say(message)
      
whats.rule = ('$nick', ['whats', 'what\'s'], r'(.*)')
whats.example = '$nick, what\'s GA34\n$nick, whats CoCR?'

def makemessage(abbr, council, num, result, givenum):
   if not result:
      message = 'I don\'t have a result for that yet.'
   else:
      name = result[2]
      cat = result[3]
      arg = result[4]
      auth = result[5]
      coauth = result[6]
      active = 0
      if result[7] == None: active = 1
      print active
      
      if council == 'G': council = 'GA'
      elif council == 'S': council == 'SC'
      else: council = 'UN'
      
      message = abbr + ' is '
      if givenum: message = message + council + '#' + num + ', '
      message = message + name
      if not active: message = message + ', a repealed resolution'
      message = message + ' by ' + auth
      if coauth: message = message + ' and ' + coauth
   return message
   
def authored(phenny, input):
   """.authored nation - Checks the resolution DB for resolutions authored by
   nation (or nation with any number of characters after. e.g, .authored unibot
   returns results for Unibot and Unibotian WA Mission."""
   phenny.say("Let me check.")
   name = input.group(2)
   
   auth = 'SELECT COUNT(*) FROM RESOLUTIONS WHERE Author LIKE \''
   cur.execute(auth + name + '%\'')
   authored = cur.fetchone()[0]
   
   coauth = 'SELECT COUNT(*) FROM RESOLUTIONS WHERE Coauthor LIKE \''
   cur.execute(coauth + name + '%\'')
   coauthored = cur.fetchone()[0]
   
   message = 'I see ' + str(authored) + ' resolutions'
   if coauthored > 0:
      message = message + ', plus ' + str(coauthored) + ' coauthorships'
   phenny.say(message + ' by ' + name)
authored.commands = ['authored']
authored.example = '.authored Unibot'

def sc(phenny, input):
   """Returns a link for the requested SC resolution."""
   lnk = 'http://www.nationstates.net/page=WA_past_resolutions/council=2/start='
   phenny.say(lnk + str(int(input.group(2)) - 1))
sc.commands = ['sc']
sc.example = '.sc 3'

def ga(phenny, input):
   """Returns a link for the requested GA resolution."""
   lnk = 'http://www.nationstates.net/page=WA_past_resolutions/council=1/start='
   phenny.say(lnk + str(int(input.group(2)) - 1))
ga.commands = ['ga']
ga.example = '.ga 132'

def un(phenny, input):
   """Returns a link for the requested NSUN historical resolution."""
   lnk = 'http://www.nationstates.net/page=UN_past_resolutions/council=0/start='
   phenny.say(lnk + str(int(input.group(2)) - 1))
un.commands = ['un']
un.example = '.un 5'

def rlink(phenny, input):
    lnk = 'http://www.nationstates.net/region=' + input.group(2).rstrip(' ')
    phenny.reply(lnk)
rlink.commands = ['rlink']

def nation(phenny, input):
    lnk = 'http://www.nationstates.net/' + input.group(2).rstrip(' ')
    phenny.reply(lnk)
nation.commands = ['nation','n']

def uhoh(phenny, input):
    phenny.reply('Sorry, I\'m not FriarTuck. Eluvatar hasn\'t given me that code yet.')
uhoh.commands = ['after', 'approx']
