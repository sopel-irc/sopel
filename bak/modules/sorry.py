#!/usr/bin/env python
"""
scores.py - Sorry Module
Author: Michael S. Yanovich http://opensource.cse.ohio-state.edu/
Phenny (About): http://inamidst.com/phenny/
"""

#
#       sorry.py
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
#       MA 02110-1301, USA..phen

def assf(phenny, input):
    phenny.say("Sorry, " + str(input.nick) + ". That is not appropriate!")
assf.commands = ['ass']
assf.priority = 'medium'

def cuntf(phenny, input):
    phenny.say("Sorry, " + str(input.nick) + ". That is not appropriate!")
cuntf.commands = ['cunt']
cuntf.priority = 'medium'

def dickf(phenny, input):
    phenny.say("Sorry, " + str(input.nick) + ". That is not appropriate!")
dickf.commands = ['dick']
dickf.priority = 'medium'

def penisf(phenny, input):
    phenny.say("Sorry, " + str(input.nick) + ". That is not appropriate!")
penisf.commands = ['penis']
penisf.priority = 'medium'

def suckf(phenny, input):
    phenny.say("Sorry, " + str(input.nick) + ". That is not appropriate!")
suckf.commands = ['suck']
suckf.priority = 'medium'

if __name__ == '__main__': 
   print __doc__.strip()
