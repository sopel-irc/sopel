#!/usr/bin/env python
"""
rand.py - Rand Module
Copyright 2010, Michael Yanovich, yanovich.net
Licensed under the Eiffel Forum License 2.

More info:
 * Jenni: https://github.com/myano/jenni/
 * Phenny: http://inamidst.com/phenny/
"""

import random
import re

def rand(jenni, input):
    """.rand <arg1> <arg2> - Generates a random integer between <arg1> and <arg2>."""
    if input.group(2) == " " or input.group(2) == "" or str(input.group(2)) == None or str(input.group(2)) == "" or input.group(2) == None:
        jenni.say("I'm sorry, " + str(input.nick) + ", but you must enter at least one number.")
    else:
        random.seed()
        li_integers = input.group(2)
        li_integers_str = li_integers.split()
        if len(li_integers_str) == 1:
            li_integers_str = re.sub(r'\D', '', str(li_integers_str))
            if int(li_integers_str[0]) <= 1:
                a = li_integers_str[0]
                a = int(a)
                randinte = random.randint(a, 0)
            else:
                a = li_integers_str[0]
                a = int(a)
                randinte = random.randint(0, a)
            jenni.say(str(input.nick) + ": your random integer is: " + str(randinte))
        else:
            a,b = li_integers.split()
            a = re.sub(r'\D', '', str(a))
            b = re.sub(r'\D', '', str(b))
            a = int(a)
            b = int(b)
            if a <= b:
                randinte = random.randint(a, b)
            else:
                randinte = random.randint(b, a)
            jenni.say(str(input.nick) + ": your random integer is: " + str(randinte))

rand.commands = ['rand']
rand.priority = 'medium'

if __name__ == '__main__':
    print __doc__.strip()
