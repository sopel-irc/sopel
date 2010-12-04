#!/usr/bin/env python
""" roulette.py """
import random

random.seed()

# edit this setting for roulette counter. Larger, the number, the harder the game.
MAX_RANGE = 5

# edit this setting for text displays
ROULETTE_TICK = '*TICK*'
ROULETTE_KICK_REASON = '*SNIPED! YOU LOSE!*'

## do not edit below this line unless you know what you're doing

lastRouletter = None
rouletteBAM = None
def roulette (phenny, input):
    global lastRouletter, rouletteBAM, MAX_RANGE, ROULETTE_TICK, ROULETTE_KICK
    if lastRouletter == input.nick:
        return
    lastRouletter = input.nick
    if rouletteBAM is None:
        rouletteBAM = random.randint(0,MAX_RANGE)
        phenny.say(ROULETTE_TICK)
        return  # can't lose on round 1 >_>
    if rouletteBAM == random.randint(0,MAX_RANGE):
        phenny.write(['KICK', '%s %s :%s' % (input.sender, input.nick, ROULETTE_KICK_REASON)])
        lastRouletter = None
        rouletteBAM = None
    else:
        phenny.say(ROULETTE_TICK)
roulette.commands = ['roulette']
roulette.priority = 'low'

if __name__ == '__main__': 
	print __doc__.strip()
