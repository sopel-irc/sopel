#!/usr/bin/env python
"""
ping.py - jenni Ping Module
Author: Sean B. Palmer, inamidst.com
About: http://inamidst.com/phenny/
"""

import random

def hello(jenni, input): 
   if input.owner: 
      greeting = random.choice(('Fuck off,', 'Screw you,', 'Go away'))
   else: greeting = random.choice(('Hi', 'Hey', 'Hello'))
   punctuation = random.choice(('', '!'))
   jenni.say(greeting + ' ' + input.nick + punctuation)
hello.rule = r'(?i)(hi|hello|hey) $nickname[ \t]*$'

def rude(jenni, input):
   jenni.say('Watch your mouth, ' + input.nick + ', or I\'ll tell your mother!')
rude.rule = r'(?i)(Fuck|Screw) you, $nickname[ \t]*$'

def interjection(jenni, input): 
   jenni.say(input.nick + '!')
interjection.rule = r'$nickname!'
interjection.priority = 'high'
interjection.thread = False
interjection.rate = 30

if __name__ == '__main__': 
   print __doc__.strip()
