#!/usr/bin/env python
"""
bomb.py - Simple bomb prank game
Copyright 2012, Edward Powell http://embolalia.net
Licensed under the Eiffel Forum License 2.

More info:
 * Jenni: https://github.com/myano/jenni/
 * Phenny: http://inamidst.com/phenny/
"""
from random import choice
import sched, time

colors = ['Red', 'Yellow', 'Blue', 'White', 'Black']
sch = sched.scheduler(time.time, time.sleep)
fuse = 120#seconds

def meter(jenni, input):
    jenni.say('\x02[\x02'+word+'\x02]\x02 '+nick+' is '+randint(1,100)+'%'+word)
meter.rule = '\.(\S)meter (\S)'

def start(jenni, input):
    global bombs
    global sch
    target = input.group(2)
    if target in bombs:
        jenni.say('I can\'t fit another bomb in '+target+'\'s pants!')
        return
    message = 'Hey, '+target+'! '+input.nick+' has  stuffed a bomb in your pants. You have 2 minutes  to attempt to defuse the bomb by cutting the wire. There are 5 wires. Red, Yellow, Blue, White, Black. Choose a wire by typing: .cutwire color'
    
    color = choice(colors)
    bombs[target] = color
    sch.enter(fuse, 1, explode, (jenni, input))
    sch.run()
start.commands = ['bomb']

def cutwire(jenni, input):
    global bombs
    if input.nick not in bombs: return
    if lower(input.group(2)) == bombs[input.nick]:
        jenni.say(input.nick+
                  'has cut the blue wire and successfully defuses the bomb!')
    else:
        jenni.say('No! No, that\'s the wrong one. Aww, you\'ve gone and killed yourself. Oh, that\'s... that\'s not good. No good at all, really. Wow. Sorry.')
        jenni.say('(Did I sound a bit like Wheatley there?)')
    bombs.pop(input.nick)
cutwire.commands = ['cutwire']

def explode(jenni, input):
    jenni.say('Um, listen. Minor problem. Bit embarrassing. I, uh. I haven\'t quite finished the banning part yet so... if you could just pop out on your own for a bit, that\'d be great. Just for a second. Just... pop out, and come right back in. Can you do that? Thanks.')
    bombs.pop(input.group(2), None)#event should be canceled by cutwire

