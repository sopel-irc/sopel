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
from re import search
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
    print jenni.ops[input.sender]
    print input.sender
    if not input.sender.startswith('#') or \
       (input.nick not in jenni.ops[input.sender] and
       input.nick not in jenni.halfplus[input.sender]):
        return
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
    bombs[target.lower()] = (color, code)
    sch.run()
start.rule = '.bomb (\S+).*?'

def cutwire(jenni, input):
    global bombs, colors
    target = input.nick
    if target.lower() != jenni.nick.lower() and target.lower() not in bombs: return
    color, code = bombs.pop(target.lower()) #remove target from bomb list
    wirecut = input.group(2).rstrip(' ')
    if wirecut.lower() in ('all', 'all!'):
	sch.cancel(code) #defuse timer, execute premature detonation
	kmsg = 'KICK '+input.sender+' '+target+' : Cutting ALL the wires! *boom* (You should\'ve picked the '+color+' wire.)'
	jenni.write([kmsg])
    elif wirecut.capitalize() not in colors:
        jenni.say('I can\'t seem to find that wire, '+target+'! You sure you\'re picking the right one? It\'s not here!')
        bombs[target.lower()] = (color, code) #Add the target back onto the bomb list,
    elif wirecut.capitalize() == color:
        jenni.say('You did it, '+target+'! I\'ll be honest, I thought you were dead. But nope, you did it. You picked the right one. Well done.')
        sch.cancel(code) #defuse bomb
    else:
        sch.cancel(code) #defuse timer, execute premature detonation
        kmsg = 'KICK '+input.sender+' '+target+\
               ' : No! No, that\'s the wrong one. Aww, you\'ve gone and killed yourself. Oh, that\'s... that\'s not good. No good at all, really. Wow. Sorry. (You should\'ve picked the '+color+' wire.)'
        jenni.write([kmsg])
cutwire.commands = ['cutwire']

def explode(jenni, input):
    target = input.group(1)
    kmsg = 'KICK '+input.sender+' '+target+\
           ' : Oh, come on, '+target+'! You could\'ve at least picked one! Now you\'re dead. Guts, all over the place. You see that? Guts, all over YourPants. (You should\'ve picked the '+bombs[target.lower()][0]+' wire.)'
    jenni.write([kmsg])
    bombs.pop(target.lower())

