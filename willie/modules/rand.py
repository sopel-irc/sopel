"""
rand.py - Rand Module
Copyright 2010, Michael Yanovich, yanovich.net
Licensed under the Eiffel Forum License 2.

http://willie.dftba.net
"""

from willie.module import commands, example
import random
import re


@commands('rand')
@example('.rand 1 100')
def rand(bot, trigger):
    """Generates a random integer between <arg1> and <arg2>."""
    if not trigger.group(2):
        bot.say("I'm sorry, " + str(trigger.nick) + ", but you must enter at least one number.")
    else:
        random.seed()
        li_integers = trigger.group(2)
        li_integers_str = li_integers.split()
        if len(li_integers_str) == 1:
            li_integers_str = re.sub(r'\D', '', str(li_integers_str))
            if int(li_integers_str[0]) <= 1:
                a = li_integers_str
                a = int(a)
                randinte = random.randint(a, 0)
            else:
                a = li_integers_str
                a = int(a)
                randinte = random.randint(0, a)
            bot.say(str(trigger.nick) + ": your random integer is: " + str(randinte))
        else:
            a, b = li_integers.split()
            a = re.sub(r'\D', '', str(a))
            b = re.sub(r'\D', '', str(b))
            a = int(a)
            b = int(b)
            if a <= b:
                randinte = random.randint(a, b)
            else:
                randinte = random.randint(b, a)
            bot.say(str(trigger.nick) + ": your random integer is: " + str(randinte))
