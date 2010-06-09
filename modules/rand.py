#!/usr/bin/env python
"""
rand.py - Rand Module
Author: Michael S. Yanovich http://opensource.cse.ohio-state.edu/
Phenny (About): http://inamidst.com/phenny/
"""

import random

def rand(phenny, input):
	""".rand <arg1> <arg2> - Generates a random integer between <arg1> and <arg2>."""
	if input.group(2) == " " or input.group(2) == "" or str(input.group(2)) == None or str(input.group(2)) == "" or input.group(2) == None:
		phenny.say("I'm sorry, " + str(input.nick) + ", but you must enter at least one number.")
	else:
		li_integers = input.group(2)
		li_integers_str = li_integers.split()
		if len(li_integers_str) == 1:
			if int(li_integers_str[0]) <= 1:
				a = li_integers_str[0]
				a = int(a)
				randinte = random.randint(a, 0)
			else:
				a = li_integers_str[0]
				a = int(a)
				randinte = random.randint(0, a)
			phenny.say(str(input.nick) + ": your random integer is: " + str(randinte))
		else:
			a,b = li_integers.split()
			a = int(a)
			b = int(b)
			if a <= b:
				randinte = random.randint(a, b)
			else:
				randinte = random.randint(b, a)
			phenny.say(str(input.nick) + ": your random integer is: " + str(randinte))

rand.commands = ['rand']
rand.priority = 'medium'

if __name__ == '__main__': 
	print __doc__.strip()
