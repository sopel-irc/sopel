#!/usr/bin/env python
"""
scores.py - Score Module
Author: Michael S. Yanovich and Matt Meinwald, http://opensource.cse.ohio-state.edu/
Phenny (About): http://inamidst.com/phenny/
"""

#
#       scores.py
#       
#       Copyright 2009 Michael S. Yanovich and Matt Meinwald
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

import pickle

try:
    scores_file = open("scores.txt","r")
except IOError:
    scores_dict = dict()
else:
    scores_dict = pickle.load(scores_file)

#Adds Points
def addpoint(phenny, input):
    """.addpoint <nick> - Adds 1 point to the score system for <nick>."""
    global scores_dict
    nick_addpoint = input.group(2)
    if input.nick == nick_addpoint:
        phenny.say("I'm sorry, " + str(input.nick) + ". I'm afraid I can't do that!")
    else:
        if nick_addpoint in scores_dict:
            scores_dict[nick_addpoint] += 1
        else:
            scores_dict[nick_addpoint] = 1
        scores_file = open("scores.txt", "w")
        pickle.dump(scores_dict, scores_file)
        phenny.say(nick_addpoint + ": " + str(scores_dict[nick_addpoint]))
        scores_file.close()
addpoint.commands = ['addpoint']
addpoint.priority = 'medium'

#Removes Points
def rmpoint(phenny, input):
    """.rmpoint <nick> - Removes 1 point to the score system for <nick>."""
    global scores_dict
    nick_addpoint = input.group(2)
    if input.nick == nick_addpoint:
        phenny.say("I'm sorry, " + str(input.nick) + ". I'm afraid I can't do that!")
    else:
        if nick_addpoint in scores_dict:
            scores_dict[nick_addpoint] -= 1
            scores_file = open("scores.txt", "w")
            pickle.dump(scores_dict, scores_file)
            phenny.say(nick_addpoint + ": " + str(scores_dict[nick_addpoint]))
            scores_file.close()
        else:
            phenny.say("I'm sorry, " + str(input.nick) + ". I'm afraid I can't do that!")
rmpoint.commands = ['rmpoint']
rmpoint.priority = 'medium'

#Lists the Scores
def scores(phenny, input):
    """.scores - Lists all users and their point values in the system."""
    global scores_file
    global scores_dict
    for nick in scores_dict:
        strscore = str(scores_dict[nick])
        str_say = nick + ": " + strscore
        phenny.say(str_say)
scores.commands = ['scores']
scores.priority = 'medium'

def rmuser(phenny, input):
    global scores_file
    global scores_dict
    if input.nick == "yano":
        scores_file = open("scores.txt", "w")
        del scores_dict[input.group(2)]
        phenny.say("User, " + str(input.group(2)) + ", has been removed.")
        pickle.dump(scores_dict, scores_file)
        scores_file.close()
    else:
        phenny.say("I'm sorry, " + str(input.nick) + ". I'm afraid I can't do that!")
rmuser.commands = ['rmuser']
rmuser.priority = 'medium'

if __name__ == '__main__': 
    print __doc__.strip()
