#!/usr/bin/env python
"""
ping.py - Phenny Ping Module
Author: Sean B. Palmer, inamidst.com
About: http://inamidst.com/phenny/
"""

import random

def hello(phenny, input): 
	greeting = random.choice(('Hi', 'Hey', 'Hello', 'Hej', 'Hallo', 'Hei', 'Ciao'))
	punctuation = random.choice(('!'))
	phenny.say(greeting + ' ' + input.nick + punctuation + " To see what all I can do type .commands")
hello.rule = r'(?i)(hi|hello|hey|howdy|hej|hallo|hei|merhaba) $nickname\b'

def hellof(phenny, input):
	hello(phenny,input)
hellof.rule = r'(?i)$nickname\:\s+(hi|hello|hey|howdy|hej|hallo|hei|merhaba)'

def goodbye(phenny, input):
	byemsg = random.choice(('Bye', 'Goodbye', 'Seeya', 'Auf Wiedersehen', 'Au revoir', 'Ttyl'))
	punctuation = random.choice(('!'))
	phenny.say(byemsg + ' ' + input.nick + punctuation)
goodbye.rule = r'(?i).*\s(bye|goodbye|seeya|cya|ttyl|g2g|gnight|goodnight)\s.*'

def wb(phenny, input):
	phenny.say("Thank you " + input.nick + ".")
wb.rule = r'(?i)(welcome back|welcomeback|wb) $nickname\b'

def interjection(phenny, input): 
	phenny.say(input.nick + '!')
interjection.rule = r'$nickname!'
interjection.priority = 'high'
interjection.thread = False

#def whyf(phenny, input):

#def sendmsg(phenny, input):
#	if input.sender.startswith('#'): return
#	if input.admin:
#		phenny.say("

if __name__ == '__main__': 
	print __doc__.strip()
