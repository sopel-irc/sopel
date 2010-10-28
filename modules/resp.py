#!/usr/bin/env python
"""
resp.py - Phenny Response Module
Author: Michael S. Yanovich, http://opensource.osu.edu/
About: http://inamidst.com/phenny/

This module tries to make phenny appear more "affection."
"""

import random, time
greeting = ['Hi', 'Hey', 'Hello', 'Hallo', 'Welcome']
# By increasing the variable 'limit' you are also increasing how annoying phenny will be.
limit = 0.05

def f_whoa(phenny, input):
	randnum = random.random()
	if 0 < randnum < limit:
		respond = ['what?', 'huh?', 'please explain...', 'I\'m confused.']
		randtime = random.uniform(10,45)
		time.sleep(randtime)
		phenny.say(random.choice(respond))
#f_whoa.rule = '(whoa.*)$'
#f_whoa.priority = 'high'

def f_lol(phenny, input):
	randnum = random.random()
	if 0 < randnum < limit:
		respond = ['haha', 'lol', 'rofl']
		randtime = random.uniform(0,9)
		time.sleep(randtime)
		phenny.say(random.choice(respond))
f_lol.rule = '(haha!?|lol!?)$'
f_lol.priority = 'high'

def f_bye(phenny, input):
	respond = ['bye!', 'bye', 'see ya', 'see ya!']
	phenny.say(random.choice(respond))
f_bye.rule = '(g2g!?|bye!?)$'
f_bye.priority = 'high'

def f_argh(phenny, input):
	randnum = random.random()
	if 0 < randnum < limit:
		respond = ['I feel your frustration.', 'I\'m sorry.']
		randtime = random.uniform(10,45)
		time.sleep(randtime)
		phenny.say(random.choice(respond))
#f_argh.rule = '(argh.*)$'
#f_argh.priority = 'high'

def f_heh(phenny, input):
	randnum = random.random()
	if 0 < randnum < limit:
		respond = ['hm']
		randtime = random.uniform(0,7)
		time.sleep(randtime)
		phenny.say(random.choice(respond))
f_heh.rule = '(heh!?)$'
f_heh.priority = 'high'

def f_awesomeness(phenny, input):
	randnum = random.random()
	if 0 < randnum < limit:
		respond = ['cool', 'awesome', 'sweet', 'neat']
		randtime = random.uniform(0,9)
		time.sleep(randtime)
		phenny.say(random.choice(respond))
#f_awesomeness.rule = '(cool!?|awesome!?|sweet!?)$'
#f_awesomeness.priority = 'high'

def f_confusion(phenny, input):
	randnum = random.random()
	if 0 < randnum < limit:
		respond = ['I don\'t get it either.', 'I don\'t get it.', 'Could you elaborate?']
		randtime = random.uniform(10,45)
		time.sleep(randtime)
		phenny.say(random.choice(respond))
#f_confusion.rule = '(huh.*)$'
#f_confusion.priority = 'high'

def f_really(phenny, input):
	randtime = random.uniform(10,45)
	time.sleep(randtime)
	phenny.say(str(input.nick) + ": " + "Yes, really.")
f_really.rule = r'(?i)$nickname\:\s+(really!?)'
f_really.priority = 'high'

def wb(phenny, input):
	phenny.reply("Thank you!")
wb.rule = '(wb).*(phenny|phenny_osu)$'

def bru (phenny, input):
    if input.sender != "#osu_osc":
        return
    text = input.group()
    words = { "color" : "colour", "favor" : "favour", "behavior" : "behaviour", "flavor" : "flavour", "favorite" : "favourite", "honor" : "honour", "neighbor" : "neighbour", "rumor" : "rumour", "labor" : "labour"}
    reply = ""
    for k in words:
        if k in text:
            reply += (words[k] + " ")
    phenny.reply(reply)

bru.rule = '.*(color|favor|behavior|flavor).*'

if __name__ == '__main__': 
	print __doc__.strip()
