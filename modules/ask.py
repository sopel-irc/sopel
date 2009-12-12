#!/usr/bin/env python
"""
scores.py - Ask Module
Author: Michael S. Yanovich http://opensource.cse.ohio-state.edu/
Phenny (About): http://inamidst.com/phenny/
"""

#
#       ask.py
#       
#       Copyright 2009 Michael S. Yanovich
#       
#       This program is free software; you can redistribute it and/or modify
#       it under the terms of the GNU General Public License as published by
#       the Free Software Foundation; either version 3 of the License, or
#       (at your option) any later version.
#       
#       This program is distributed in the hope that it will be useful,
#       but WITHOUT ANY WARRANTY; without even the implied warranty of
#       MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#       GNU General Public License for more details.
#       
#       You should have received a copy of the GNU General Public License
#       along with this program; if not, write to the Free Software
#       Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#       MA 02110-1301, USA.

import random, string

def ask(phenny, input):
	""".ask <item1> or <item2> or <item3> - Randomly picks from a set of items seperated by ' or '."""
	choices = input.group(2)
	if choices == None:
		phenny.say("There is no spoon! Please try a valid question.")
	else:
		list_choices = choices.split(" or ")
		if len(list_choices) == 1:
			phenny.say(str(input.nick) + ": " + str(random.choice(('yes', 'no'))))
		else:
			phenny.say(str(input.nick) + ": " + str(random.choice(list_choices)))
ask.commands = ['ask']
ask.priority = 'medium'

if __name__ == '__main__': 
	print __doc__.strip()
