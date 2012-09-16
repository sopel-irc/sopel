#!/usr/bin/env python
"""
qask.py - Ask Module
Copyright 2011, Michael Yanovich, yanovich.net
Licensed under the Eiffel Forum License 2.

http://willie.dftba.net
"""

import random, time


def ask(willie, trigger):
    """.ask <item1> or <item2> or <item3> - Randomly picks from a set of items seperated by ' or '."""

    choices = trigger.group(2)
    random.seed()

    if choices == None:
        willie.reply("There is no spoon! Please try a valid question.")
    elif choices.lower() == "what is the answer to life, the universe, and everything?":
        willie.reply("42")
    else:
        list_choices = choices.split(" or ")
        if len(list_choices) == 1:
            willie.reply(random.choice(['yes', 'no']))
        else:
            willie.reply((random.choice(list_choices)).encode('utf-8'))
ask.commands = ['ask']
ask.priority = 'low'
ask.example = '.ask today or tomorrow or next week'
ask.rate = 20

if __name__ == '__main__':
    print __doc__.strip()
