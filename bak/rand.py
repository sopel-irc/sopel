#!/usr/bin/env python
"""
scores.py - Rand Module
Author: Michael S. Yanovich http://opensource.cse.ohio-state.edu/
Phenny (About): http://inamidst.com/phenny/
"""

#
#       rand.py
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

import random

def rand(phenny, input):
    """.rand <arg1> <arg2> - Generates a random integer between <arg1> and <arg2>."""
    li_integers = input.group(2)
    a,b = li_integers.split()
    a = int(a)
    b = int(b)
    randinte = random.randint(a, b)
    phenny.say(str(input.nick) + ": your random integer is: " + str(randinte))
rand.commands = ['rand']
rand.priority = 'medium'

if __name__ == '__main__': 
   print __doc__.strip()
