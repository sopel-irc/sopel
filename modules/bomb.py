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
meter.rule = '\.(\S+)meter (\S)'

def start(jenni, input):
    global bombs
    global sch
    target = input.group(2).rstrip(' ')
    if target in bombs:
        jenni.say('I can\'t fit another bomb in '+target+'\'s pants!')
        return
    message = 'Hey, '+target+'! Don\'t look but, I think there\'s a bomb in your pants. 2 minute timer, 5 wires: Red, Yelow, Blue, White and Black. Which wire should I cut? Don\'t worry, I know what I\'m doing! (respond with .cutwire color)'
    jenni.say(message)
    color = choice(colors)
    jenni.msg(input.nick, 'Hey, don\'t tell '+target+', but the '+color+' wire? Yeah, that\'s the one. But shh! Don\'t say anything!')
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
        jenni.say('You did it, '+input.nick+'! I\'ll be honest, I thought you were dead. But nope, you did it. You picked the right one. Well done.')
    else:
        jenni.say('No! No, that\'s the wrong one. Aww, you\'ve gone and killed yourself. Oh, that\'s... that\'s not good. No good at all, really. Wow. Sorry.')
cutwire.commands = ['cutwire']

def explode(jenni, input):
    target = input.group(2).rstrip(' ')
    jenni.say('Oh, come on, '+target+'! You could\'ve at least picked one! Now you\'re dead. Guts, all over the place. You see that? Guts, all over YourPants.')
    bombs.pop(target)

