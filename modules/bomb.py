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
fuse = 30#seconds
bombs = dict()

def meter(jenni, input):
    jenni.say('\x02[\x02'+word+'\x02]\x02 '+nick+' is '+randint(1,100)+'%'+word)
meter.rule = '\.(\S)meter (\S)'

def start(jenni, input):
    global bombs
    global sch
    target = input.group(2).rstrip(' ')
    if target in bombs:
        jenni.say('I can\'t fit another bomb in '+target+'\'s pants!')
        return
    message = 'Hey, '+target+'! '+target+' has stuffed a bomb in your pants. You have 2 minutes  to attempt to defuse the bomb by cutting the wire. There are 5 wires. Red, Yellow, Blue, White, Black. Choose a wire by typing: .cutwire color'
    
    jenni.say(message)
    color = choice(colors)
    jenni.msg(target, 'The correct color is '+color)
    code=sch.enter(fuse, 1, explode, (jenni, input))
    bombs[target] = (color, code)
    sch.run()
start.commands = ['bomb']

def cutwire(jenni, input):
    global bombs
    if input.nick not in bombs: return
    color, code = bombs.pop(input.nick)
    c = color.lower()
    sch.cancel(code)
    if input.group(2).lower() == c:
        jenni.say(input.nick+
                  ' has cut the '+c+' wire and successfully defuses the bomb!')
    else:
        jenni.say('No! No, that\'s the wrong one. Aww, you\'ve gone and killed yourself. Oh, that\'s... that\'s not good. No good at all, really. Wow. Sorry.')
cutwire.commands = ['cutwire']

def explode(jenni, input):
    target = input.group(2)
    jenni.say('Um, listen, '+target+'. Minor problem. Bit embarrassing. I, uh. I haven\'t quite finished the banning part yet so... if you could just pop out on your own for a bit, that\'d be great. Just for a second. Just... pop out, and come right back in. Can you do that? Thanks.')
    bombs.pop(target)

