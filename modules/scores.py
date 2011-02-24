#!/usr/bin/env python
"""
scores.py - Score Module
Author: Michael S. Yanovich and Matt Meinwald, http://opensource.cse.ohio-state.edu/
Jenni (About): http://inamidst.com/phenny/
"""

import pickle

try:
    scores_file = open("scores.txt","r")
except IOError:
    scores_dict = dict()
else:
    scores_dict = pickle.load(scores_file)
    scores_file.close()

# Adds Points to the scores.txt file
def addpoint(jenni, input):
    """.addpoint <nick> - Adds 1 point to the score system for <nick>."""

    nick = input.group(2)
    if nick != None:
        nick = nick.lstrip().rstrip()

    global scores_dict
    if not nick:
        jenni.reply("I'm sorry, but I'm afraid I can't add that user!")
    else:
        if input.nick == nick:
            jenni.reply("I'm sorry, but I'm afraid I can't do that!")
        else:
            nick = nick.lower()
            if nick in scores_dict:
                scores_dict[nick][0] += 1
            else:
                scores_dict[nick] = [1, 0]
            scores_file = open("scores.txt", "w")
            pickle.dump(scores_dict, scores_file)
            msg = "%s: +%d/-%d, %d" % (nick, scores_dict[nick][0], scores_dict[nick][1], scores_dict[nick][0] - scores_dict[nick][1])
            jenni.say(msg)
            scores_file.close()
addpoint.commands = ['addpoint']
addpoint.priority = 'high'

# Removes Points to the scores.txt file
def rmpoint(jenni, input):
    """.rmpoint <nick> - Removes 1 point to the score system for <nick>."""
    
    nick = input.group(2)
    if nick != None:
        nick = nick.lstrip().rstrip()

    global scores_dict
    if not nick:
        jenni.reply("I'm sorry, but I'm afraid I can't add that user!")
    else:
        if input.nick == nick:
            jenni.reply("I'm sorry, but I'm afraid I can't do that!")
        else:
            nick = nick.lower()
            if nick in scores_dict:
                scores_dict[nick][1] += 1
                scores_file = open("scores.txt", "w")
                pickle.dump(scores_dict, scores_file)
                msg = "%s: +%d/-%d, %d" % (nick, scores_dict[nick][0], scores_dict[nick][1], scores_dict[nick][0] - scores_dict[nick][1])
                jenni.say(msg)
                scores_file.close()
            else:
                jenni.reply("I'm sorry, but I'm afraid I can't do that!")
rmpoint.commands = ['rmpoint']
rmpoint.priority = 'high'

# Lists the Scores in the scores.txt file
def scores(jenni, input):
    """.scores - Lists all users and their point values in the system."""
    
    global scores_dict
    if len(scores_dict) >= 1:
        nicks = [ ]
        for nick in scores_dict:
            nicks.append(nick)
        nicks = sorted(nicks) 
        str_say2 = "| "
        for nick in nicks:
            strscore = str(scores_dict[nick])
            str_say = "%s: +%d/-%d, %d | " % (nick, scores_dict[nick][0], scores_dict[nick][1], scores_dict[nick][0] - scores_dict[nick][1])
            str_say2 += str_say
        jenni.say(str_say2)
    else:
        jenni.say("There are currently no users with a score.")
scores.commands = ['scores']
scores.priority = 'medium'

# Removes a user.
def rmuser(jenni, input):
    """.rmuser - Removes a user from the scores system."""

    nick = input.group(2)
    if nick != None:
        nick = nick.lstrip().rstrip()

    global scores_dict
    if nick == "" or nick == None:        
        jenni.say("I'm sorry, " + str(input.nick) + ". I'm afraid I can't remove that user!")
    else:
        if nick in scores_dict:
            if input.admin:
                scores_file = open("scores.txt", "w")
                del scores_dict[nick]
                jenni.say("User, " + str(nick) + ", has been removed.")
                pickle.dump(scores_dict, scores_file)
                scores_file.close()
            else:
                jenni.say("I'm sorry, " + str(input.nick) + ". I'm afraid I can't do that!")
        else:
            jenni.say("I'm sorry, " + str(input.nick) + ", but I can not remove a person that does not exist!")
rmuser.commands = ['rmuser']
rmuser.priority = 'medium'

# Set a given number for both points
def setpoint(jenni, input):
    """.setpoint <nick> <number> <number> - Sets points for given user."""

    info = input.group(2)
    if info != None:
        info = info.lstrip().rstrip()

    global scores_dict
    if not info:
        jenni.reply("I'm sorry, but I'm afraid I can't add that user!")
    else:
        stuff = info
        stuff_split = stuff.split()
        if input.admin:
            if len(stuff_split) < 3:
                jenni.reply("I'm sorry, but I'm afraid I don't understand what you want me to do!")
            else:
                nick = stuff_split[0]
                try:
                    add = int(stuff_split[1])
                    sub = int(stuff_split[2])
                except:
                    jenni.say("I'm sorry, but I'm afraid I don't understand what you want me to do!")
                    return
                try:
                    if input.nick == nick:
                        jenni.reply("I'm sorry, but I'm afraid I can't do that!")
                    else:
                        nick = nick.lower()
                        if nick in scores_dict:
                            scores_dict[nick] = [add, sub]
                            scores_file = open("scores.txt", "w")
                            pickle.dump(scores_dict, scores_file)
                            msg = "%s: +%d/-%d, %d" % (nick, scores_dict[nick][0], scores_dict[nick][1], scores_dict[nick][0] - scores_dict[nick][1])
                            jenni.say(msg)
                            scores_file.close()
                        else:
                            jenni.reply("I'm sorry, but I'm afraid I can't do that!")
                except ValueError:
                    jenni.reply("I'm sorry but I refuse to do that!")
        else:
            jenni.reply("I'm sorry, but you are not one of my admins.")
setpoint.commands = ['setpoint']
setpoint.priority = 'medium'

if __name__ == '__main__': 
    print __doc__.strip()
