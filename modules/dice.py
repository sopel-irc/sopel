#!/usr/bin/env python
"""
dice.py - Dice Module
Copyright 2010-2012, Dimitri "Tyrope" Molenaars, TyRope.nl
Licensed under the Eiffel Forum License 2.

More info:
 * Jenni: https://github.com/myano/jenni/
 * Phenny: http://inamidst.com/phenny/
"""

from random import randint, seed
from modules.calc import calculate
import re

seed()

def dice(willie, trigger):
    """.dice <formula> - Rolls dice using the XdY format, also does basic math."""
    no_dice = 1
    msg = ''
    try:
        msg = ' '.join(trigger.groups(2)[1:])
    except:
        return willie.reply('You have to specify the dice you wanna roll.')
    formula = msg
    formula = formula.replace("-", " - ").replace("+", " + ").replace("/", " / ").replace("*", " * ").replace("(", " ( ").replace(")", " ) ").replace("^", " ^ ")
    arr = formula.split(" ")

    full_string, calc_string = '', ''
    for segment in arr:
        if segment != '':
            display, value = '', ''
            result = re.search("([0-9]+m)?([0-9]*[dD][0-9]+)(v[0-9]+)?", segment)
            if result:
                display, value, drops = '(', '(', ''
                dice = rollDice(result.group(2).lower())
                if result.group(3) is not None:
                    dropLowest = int(result.group(3)[1:])
                for i in range(0,len(dice)):
                    if i < dropLowest:
                        if drops == '':
                            drops = '[+'
                        drops += str(dice[i])
                        if i < dropLowest-1:
                            drops += '+'
                        else:
                            drops += ']'
                    else:
                        display += str(dice[i])
                        value += str(dice[i])
                        if i != len(dice)-1:
                            display += '+'
                            value += '+'
                value = str(value)
                no_dice = 0
                display += drops+')'
                value += ')'
            else:
                value = segment
                display = segment
            calc_string += value
            full_string += display
    #repeat next segment

    willie.say(calc_string)
    result = calculate(calc_string)
    if result == 'Sorry, no result.':
        willie.reply('Calculation failed, did you try something weird?')
    elif(no_dice):
        willie.reply("For pure math, you can use .c! "+msg+" = "+result)
    else:
        willie.reply("You roll "+msg+" ("+full_string+"): "+result)
dice.commands = ['roll','dice','d']
dice.priority = 'medium'

def rollDice(diceroll):
    if(diceroll.startswith('d')):
        rolls = 1
        size = int(diceroll[1:])
    else:
        rolls = int(diceroll.split('d')[0])
        size = int(diceroll.split('d')[1])
    result = [] #dice results.

    for i in range(1,rolls+1):
        #roll 10 dice, pick a random dice to use, add string to result.
        result.append((randint(1,size),randint(1,size),randint(1,size),randint(1,size),randint(1,size),randint(1,size),randint(1,size),randint(1,size),randint(1,size),randint(1,size))[randint(0,9)])
    return sorted(result) #returns a set of integers.

if __name__ == '__main__':
    print __doc__.strip()
