#!/usr/bin/env python
"""
bomb.py - Simple bomb prank game
Copyright 2012, Edward Powell http://embolalia.net
Licensed under the Eiffel Forum License 2.

More info:
 * Jenni: https://github.com/myano/jenni/
 * Phenny: http://inamidst.com/phenny/
"""
from random import choice, randint
import sched, time

colors = ['Red', 'Yellow', 'Blue', 'White', 'Black']
sch = sched.scheduler(time.time, time.sleep)
fuse = 120#seconds
bombs = dict()

def meter(jenni, input):
    word = input.group(1)
    nick = input.group(2)
    percent = randint(1,100)
    jenni.say('\x02[\x02'+word+'\x02]\x02 '+nick+' is '+str(percent)+'% '+word)
meter.rule = '\.(\S+)meter (\S+)'

def start(jenni, input):
    global bombs
    global sch
    target = input.group(1)
    if target in input.otherbots or target == jenni.nick: return
    if target in bombs:
        jenni.say('I can\'t fit another bomb in '+target+'\'s pants!')
        return
    message = 'Hey, '+target+'! Don\'t look but, I think there\'s a bomb in your pants. 2 minute timer, 5 wires: Red, Yellow, Blue, White and Black. Which wire should I cut? Don\'t worry, I know what I\'m doing! (respond with .cutwire color)'
    jenni.say(message)
    color = choice(colors)
    jenni.msg(input.nick, 'Hey, don\'t tell '+target+', but the '+color+' wire? Yeah, that\'s the one. But shh! Don\'t say anything!')
    code=sch.enter(fuse, 1, explode, (jenni, input))
    bombs[target] = (color, code)
    sch.run()
start.rule = '.bomb (\S+).*?'

def cutwire(jenni, input):
    global bombs
    target = input.nick
    if target != jenni.nick and target not in bombs: return
    color, code = bombs.pop(target)
    c = color.lower()
    sch.cancel(code)
    if input.group(2).lower().rstrip(' ') == c:
        jenni.say('You did it, '+target+'! I\'ll be honest, I thought you were dead. But nope, you did it. You picked the right one. Well done.')
    else:
        kmsg = 'KICK '+input.sender+' '+target+\
               ' You should\'ve picked the '+color+' wire.'
        jenni.say('No! No, that\'s the wrong one. Aww, you\'ve gone and killed yourself. Oh, that\'s... that\'s not good. No good at all, really. Wow. Sorry.')
        jenni.write([kmsg])
cutwire.commands = ['cutwire']

def explode(jenni, input):
    target = input.group(1)
    cmsg = 'Oh, come on, '+target+'! You could\'ve at least picked one! Now you\'re dead. Guts, all over the place. You see that? Guts, all over YourPants.'
    kmsg = 'KICK '+input.sender+' '+target+\
           ' : You should\'ve picked the '+bombs[target][0]+' wire.'
    jenni.say(cmsg)
    jenni.write([kmsg])
    bombs.pop(target)

