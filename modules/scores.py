#!/usr/bin/env python
"""
scores.py - Score Module
Author: Michael S. Yanovich and Matt Meinwald, http://opensource.cse.ohio-state.edu/
Phenny (About): http://inamidst.com/phenny/
"""

import pickle

try:
	scores_file = open("scores.txt","r")
except IOError:
	scores_dict = dict()
else:
	scores_dict = pickle.load(scores_file)

#Adds Points to the scores.txt file
def addpoint(phenny, input):
	""".addpoint <nick> - Adds 1 point to the score system for <nick>."""
	
	global scores_dict
	if input.group(2) == " " or input.group(2) == "" or str(input.group(2)) == None or str(input.group(2)) == "" or input.group(2) == None:
		phenny.reply("I'm sorry, but I'm afraid I can't add that user!")
	else:
		nick_addpoint = input.group(2)

		if input.nick == nick_addpoint:
			phenny.reply("I'm sorry, but I'm afraid I can't do that!")
		else:
			nick_addpoint = nick_addpoint.lower()
			if nick_addpoint in scores_dict:
				scores_dict[nick_addpoint] += 1
			else:
				scores_dict[nick_addpoint] = 1
			scores_file = open("scores.txt", "w")
			pickle.dump(scores_dict, scores_file)
			phenny.say(nick_addpoint + ": " + str(scores_dict[nick_addpoint]))
			scores_file.close()
addpoint.commands = ['addpoint']
addpoint.priority = 'high'

#Removes Points to the scores.txt file
def rmpoint(phenny, input):
	""".rmpoint <nick> - Removes 1 point to the score system for <nick>."""
	
	global scores_dict
	
	if input.group(2) == " " or input.group(2) == "" or str(input.group(2)) == None or str(input.group(2)) == "" or input.group(2) == None:
		phenny.reply("I'm sorry, but I'm afraid I can't add that user!")
	else:
		nick_addpoint = input.group(2)

		if input.nick == nick_addpoint:
			phenny.reply("I'm sorry, but I'm afraid I can't do that!")
		else:
			nick_addpoint = nick_addpoint.lower()
			if nick_addpoint in scores_dict:
				scores_dict[nick_addpoint] -= 1
				scores_file = open("scores.txt", "w")
				pickle.dump(scores_dict, scores_file)
				phenny.say(nick_addpoint + ": " + str(scores_dict[nick_addpoint]))
				scores_file.close()
			else:
				phenny.reply("I'm sorry, but I'm afraid I can't do that!")
rmpoint.commands = ['rmpoint']
rmpoint.priority = 'high'

#Lists the Scores in the scores.txt file
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

#Removes a user. Change "yano" to the admin user.
def rmuser(phenny, input):
	global scores_file
	global scores_dict
	if input.group(2) == " " or input.group(2) == "" or str(input.group(2)) == None or str(input.group(2)) == "" or input.group(2) == None:
		phenny.say("I'm sorry, " + str(input.nick) + ". I'm afraid I can't remove that user!")
	else:
		nick_addpoint = input.group(2)
		if nick_addpoint in scores_dict:
			if input.admin:
				scores_file = open("scores.txt", "w")
				del scores_dict[input.group(2)]
				phenny.say("User, " + str(input.group(2)) + ", has been removed.")
				pickle.dump(scores_dict, scores_file)
				scores_file.close()
			else:
				phenny.say("I'm sorry, " + str(input.nick) + ". I'm afraid I can't do that!")
		else:
			phenny.say("I'm sorry, " + str(input.nick) + ", but I can not remove a person that does not exist!")
rmuser.commands = ['rmuser']
rmuser.priority = 'medium'

def setpoint(phenny, input):
	""".setpoint <nick> - Sets points for given user."""
	global scores_dict
	
	if input.group(2) == " " or input.group(2) == "" or str(input.group(2)) == None or str(input.group(2)) == "" or input.group(2) == None:
		phenny.reply("I'm sorry, but I'm afraid I can't add that user!")
	else:
		stuff = input.group(2)
		stuff_split = stuff.split()
		if input.admin:
			if len(stuff_split) < 2:
				phenny.reply("I'm sorry, but I'm afraid I don't understand what you want me to do!")
			else:
				nick_addpoint = stuff_split[0]
				points = stuff_split[1]
				try:
					points = int(points)
					if input.nick == nick_addpoint:
						phenny.reply("I'm sorry, but I'm afraid I can't do that!")
					else:
						nick_addpoint = nick_addpoint.lower()
						if nick_addpoint in scores_dict:
							scores_dict[nick_addpoint] = points
							scores_file = open("scores.txt", "w")
							pickle.dump(scores_dict, scores_file)
							phenny.say(nick_addpoint + ": " + str(scores_dict[nick_addpoint]))
							scores_file.close()
						else:
							phenny.reply("I'm sorry, but I'm afraid I can't do that!")
				except ValueError:
					phenny.reply("I'm sorry but I refuse to do that!")
		else:
			phenny.reply("I'm sorry, but you are not one of my admins.")
setpoint.commands = ['setpoint']
setpoint.priority = 'medium'


if __name__ == '__main__': 
	print __doc__.strip()
