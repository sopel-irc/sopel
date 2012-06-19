#!/usr/bin/env python
"""
resp.py - Jenni Response Module
Copyright 2009-2011, Michael Yanovich, yanovich.net
Licensed under the Eiffel Forum License 2.

More info:
 * Jenni: https://github.com/myano/jenni/
 * Phenny: http://inamidst.com/phenny/

This module tries to make jenni appear more "affection."
"""

import random, time
# By increasing the variable 'limit' you are also increasing how annoying jenni will be.
limit = 0.01

def f_whoa(jenni, input):
    randnum = random.random()
    if 0 < randnum < limit:
        respond = ['what?', 'huh?', 'please explain...', 'I\'m confused.']
        randtime = random.uniform(10,45)
        time.sleep(randtime)
        jenni.say(random.choice(respond))
#f_whoa.rule = '(whoa.*)$'
#f_whoa.priority = 'high'

def f_lol(jenni, input):
    randnum = random.random()
    if 0 < randnum < limit:
        respond = ['haha', 'lol', 'rofl']
        randtime = random.uniform(0,9)
        time.sleep(randtime)
        jenni.say(random.choice(respond))
f_lol.rule = '(haha!?|lol!?)$'
f_lol.priority = 'high'

def f_bye(jenni, input):
    respond = ['bye!', 'bye', 'see ya', 'see ya!']
    jenni.say(random.choice(respond))
f_bye.rule = '(g2g!?|bye!?)$'
f_bye.priority = 'high'
f_bye.rate = 30

def f_argh(jenni, input):
    randnum = random.random()
    if 0 < randnum < limit:
        respond = ['I feel your frustration.', 'I\'m sorry.']
        randtime = random.uniform(10,45)
        time.sleep(randtime)
        jenni.say(random.choice(respond))
#f_argh.rule = '(argh.*)$'
#f_argh.priority = 'high'

def f_heh(jenni, input):
    randnum = random.random()
    if 0 < randnum < limit:
        respond = ['hm']
        randtime = random.uniform(0,7)
        time.sleep(randtime)
        jenni.say(random.choice(respond))
f_heh.rule = '(heh!?)$'
f_heh.priority = 'high'

def f_awesomeness(jenni, input):
    randnum = random.random()
    if 0 < randnum < limit:
        respond = ['cool', 'awesome', 'sweet', 'neat']
        randtime = random.uniform(0,9)
        time.sleep(randtime)
        jenni.say(random.choice(respond))
#f_awesomeness.rule = '(cool!?|awesome!?|sweet!?)$'
#f_awesomeness.priority = 'high'

def f_confusion(jenni, input):
    randnum = random.random()
    if 0 < randnum < limit:
        respond = ['I don\'t get it either.', 'I don\'t get it.', 'Could you elaborate?']
        randtime = random.uniform(10,45)
        time.sleep(randtime)
        jenni.say(random.choice(respond))
#f_confusion.rule = '(huh.*)$'
#f_confusion.priority = 'high'

def f_really(jenni, input):
    randtime = random.uniform(10,45)
    time.sleep(randtime)
    jenni.say(str(input.nick) + ": " + "Yes, really.")
f_really.rule = r'(?i)$nickname\:\s+(really!?)'
f_really.priority = 'high'

def wb(jenni, input):
    jenni.reply("Thank you!")
wb.rule = '^(wb|welcome\sback).*$nickname\s'

def bru (jenni, input):
    #if input.sender != "osu_osc":
    #    return
    text = input.group()
    words = { "color" : "colour", "favor" : "favour", "behavior" : "behaviour", "flavor" : "flavour", "favorite" : "favourite", "honor" : "honour", "neighbor" : "neighbour", "rumor" : "rumour", "labor" : "labour"}
    reply = ""
    for k in words:
        if k in text:
            reply += (words[k] + "! ")
    jenni.reply(reply)

#bru.rule = '.*(color|favor|behavior|flavor|honor|labor|rumor|neighbor|favorite).*'

if __name__ == '__main__':
    print __doc__.strip()
