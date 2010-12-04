#!/usr/bin/env python
"""
roulette.py
"""
import random

lastRouletter = None
rouletteBAM = None
def roulette (phenny, input):
    global lastRouletter, rouletteBAM
    if lastRouletter == input.nick:
        return
    lastRouletter = input.nick
    if rouletteBAM is None:
        rouletteBAM = random.randint(0,6)
        phenny.say('*TICK*')
        return  # can't lose on round 1 >_>
    if rouletteBAM == random.randint(0,6):
        phenny.write(['KICK', '%s %s :%s' % (input.sender, input.nick, '*SNIPED! YOU LOSE!*')])
        lastRouletter = None
        rouletteBAM = None
    else:
        phenny.say('*TICK*')
roulette.commands = ['roulette']
roulette.priority = 'low'

if __name__ == '__main__': 
	print __doc__.strip()
