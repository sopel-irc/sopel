"""
dice.py - Dice Module
Copyright 2010-2013, Dimitri "Tyrope" Molenaars, TyRope.nl
Licensed under the Eiffel Forum License 2.

http://willie.dftba.net/
"""

from random import randint, seed, choice
from willie.modules.calc import calculate
import willie.module
import re

seed()


@willie.module.command("roll")
@willie.module.command("dice")
@willie.module.command("d")
@willie.module.priority("medium")
def dice(willie, trigger):
    """
    .dice <formula> - Rolls dice using the XdY format, also does basic math and
    drop lowest (XdYvZ).
    """
    no_dice = True
    if not trigger.group(2):
        return willie.reply('You have to specify the dice you wanna roll.')
    arr = trigger.group(2).lower().replace(' ','')
    arr = arr.replace('-', ' - ').replace('+', ' + ').replace('/', ' / ')
    arr = arr.replace('*', ' * ').replace('(', ' ( ').replace(')', ' ) ')
    arr = arr.replace('^', ' ^ ').replace('()', '').split(' ')
    full_string, calc_string = '', ''

    for segment in arr:
        #check for dice
        result = re.search("([0-9]+m)?([0-9]*d[0-9]+)(v[0-9]+)?", segment)
        if result:
            #detect droplowest
            if result.group(3) is not None:
                #check for invalid droplowest
                dropLowest = int(result.group(3)[1:])
                if(dropLowest >= int(result.group(2).split('d')[0] or 1)):
                    willie.reply('You\'re trying to drop too many dice.')
                    return
            else:
                dropLowest = 0
            #dicerolling
            value, drops = '(', ''
            dice = rollDice(result.group(2))
            for i in range(0, len(dice)):
                if i < dropLowest:
                    if drops == '':
                        drops = '[+'
                    drops += str(dice[i])
                    if i < dropLowest - 1:
                        drops += '+'
                    else:
                        drops += ']'
                else:
                    value += str(dice[i])
                    if i != len(dice) - 1:
                        value += '+'
            no_dice = False
            value += drops + ')'
        else:
            value = segment
        full_string += value
    #repeat next segment

    #we're replacing, splitting and joining to exclude []'s from the math.
    result = calculate(''.join(
                full_string.replace('[', '#').replace(']', '#').split('#')[::2]))
    if result == 'Sorry, no result.':
        willie.reply('Calculation failed, did you try something weird?')
    elif(no_dice):
        willie.reply('For pure math, you can use .c '
                     + trigger.group(2) + ' = ' + result)
    else:
        willie.reply('You roll ' + trigger.group(2) + ': ' + full_string + ' = '
                     + result)


def rollDice(diceroll):
    rolls = int(diceroll.split('d')[0] or 1)
    size = int(diceroll.split('d')[1])
    result = []  # dice results.
    
    for i in range(1, rolls + 1):
        #roll 10 dice, pick a random dice to use, add string to result.
        result.append((randint(1, size), randint(1, size), randint(1, size),
                       randint(1, size), randint(1, size), randint(1, size),
                       randint(1, size), randint(1, size), randint(1, size),
                       randint(1, size))[randint(0, 9)])
    return sorted(result)  # returns a set of integers.


@willie.module.command("choice")
@willie.module.command("ch")
@willie.module.command("choose")
@willie.module.priority("medium")
def choose(willie, trigger):
    """
    .choice option1|option2|option3 - Makes a difficult choice easy.
    """
    if not trigger.group(2):
        return willie.reply('I\'d choose an option, but you didn\'t give me any.')
    choices = re.split('[\|\\\\\/]', trigger.group(2))
    pick = choice(choices)
    return willie.reply('Your options: %s. My choice: %s' % (', '.join(choices), pick))


if __name__ == '__main__':
    print __doc__.strip()

