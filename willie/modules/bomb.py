"""
bomb.py - Simple Willie bomb prank game
Copyright 2012, Edward Powell http://embolalia.net
Licensed under the Eiffel Forum License 2.

http://willie.dfbta.net
"""
from random import choice, randint
from re import search
import sched, time

colors = ['Red', 'Yellow', 'Blue', 'White', 'Black']
sch = sched.scheduler(time.time, time.sleep)
fuse = 120#seconds
bombs = dict()

def start(willie, trigger):
    """
    Put a bomb in the specified user's pants. They will be kicked if they
    don't guess the right wire fast enough.
    """
    if not trigger.group(2):return
    
    if not trigger.sender.startswith('#') or \
       (trigger.nick not in willie.ops[trigger.sender] and
       trigger.nick not in willie.halfplus[trigger.sender]):
        return
    global bombs
    global sch
    target = trigger.group(2).split(' ')[0]
    if target in willie.config.other_bots or target == willie.nick: return
    if target in bombs:
        willie.say('I can\'t fit another bomb in '+target+'\'s pants!')
        return
    message = 'Hey, '+target+'! Don\'t look but, I think there\'s a bomb in your pants. 2 minute timer, 5 wires: Red, Yellow, Blue, White and Black. Which wire should I cut? Don\'t worry, I know what I\'m doing! (respond with .cutwire color)'
    willie.say(message)
    color = choice(colors)
    willie.msg(trigger.nick, 'Hey, don\'t tell '+target+', but the '+color+' wire? Yeah, that\'s the one. But shh! Don\'t say anything!')
    code=sch.enter(fuse, 1, explode, (willie, trigger))
    bombs[target.lower()] = (color, code)
    sch.run()
start.commands = ['bomb']

def cutwire(willie, trigger):
    """
    Tells willie to cut a wire when you've been bombed.
    """
    global bombs, colors
    target = trigger.nick
    if target.lower() != willie.nick.lower() and target.lower() not in bombs: return
    color, code = bombs.pop(target.lower()) #remove target from bomb list
    wirecut = trigger.group(2).rstrip(' ')
    if wirecut.lower() in ('all', 'all!'):
	sch.cancel(code) #defuse timer, execute premature detonation
	kmsg = 'KICK '+trigger.sender+' '+target+' : Cutting ALL the wires! *boom* (You should\'ve picked the '+color+' wire.)'
	willie.write([kmsg])
    elif wirecut.capitalize() not in colors:
        willie.say('I can\'t seem to find that wire, '+target+'! You sure you\'re picking the right one? It\'s not here!')
        bombs[target.lower()] = (color, code) #Add the target back onto the bomb list,
    elif wirecut.capitalize() == color:
        willie.say('You did it, '+target+'! I\'ll be honest, I thought you were dead. But nope, you did it. You picked the right one. Well done.')
        sch.cancel(code) #defuse bomb
    else:
        sch.cancel(code) #defuse timer, execute premature detonation
        kmsg = 'KICK '+trigger.sender+' '+target+\
               ' : No! No, that\'s the wrong one. Aww, you\'ve gone and killed yourself. Oh, that\'s... that\'s not good. No good at all, really. Wow. Sorry. (You should\'ve picked the '+color+' wire.)'
        willie.write([kmsg])
cutwire.commands = ['cutwire']

def explode(willie, trigger):
    target = trigger.group(1)
    kmsg = 'KICK '+trigger.sender+' '+target+\
           ' : Oh, come on, '+target+'! You could\'ve at least picked one! Now you\'re dead. Guts, all over the place. You see that? Guts, all over YourPants. (You should\'ve picked the '+bombs[target.lower()][0]+' wire.)'
    willie.write([kmsg])
    bombs.pop(target.lower())

