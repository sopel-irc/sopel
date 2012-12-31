"""
ping.py - Willie Ping Module
Author: Sean B. Palmer, inamidst.com
About: http://willie.dftba.net
"""

import random

def hello(willie, trigger): 
   if trigger.owner: 
      greeting = random.choice(('Fuck off,', 'Screw you,', 'Go away'))
   else: greeting = random.choice(('Hi', 'Hey', 'Hello'))
   punctuation = random.choice(('', '!'))
   willie.say(greeting + ' ' + trigger.nick + punctuation)
hello.rule = r'(?i)(hi|hello|hey) $nickname[ \t]*$'

def rude(willie, trigger):
   willie.say('Watch your mouth, ' + trigger.nick + ', or I\'ll tell your mother!')
rude.rule = r'(?i)(Fuck|Screw) you, $nickname[ \t]*$'

def interjection(willie, trigger): 
   willie.say(trigger.nick + '!')
interjection.rule = r'$nickname!'
interjection.priority = 'high'
interjection.thread = False

if __name__ == '__main__': 
   print __doc__.strip()
