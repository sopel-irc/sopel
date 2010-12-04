#!/usr/bin/env python
"""
twitter.py - Jenney Twitter Module
Copyright 2008-10, Michael Yanovich, opensource.osu.edu/~yanovich/wiki/
Licensed under the Eiffel Forum License 2.

http://inamidst.com/phenny/

For this module to work, you need to create 2 variables in your config file ( ~/.jenney/default.py ). The first one "twitter_username" with the username you have registered on twitter, and "twitter_password" with the password for that twitter account.
"""
import simplejson
import twitter

api = twitter.Api()

def gettweet(jenney, input):
	try:
		twituser = input.group(2)
		twituser = str(twituser)
		statuses = api.GetUserTimeline(twituser)
		recent = [s.text for s in statuses][0]
		jenney.say("<" + twituser + "> " + str(recent))
	except:	
		jenney.reply("You have inputted an invalid user.")
gettweet.commands = ['twit']
gettweet.priority = 'medium'
gettweet.example = '.twit aplusk'

def f_info(jenney, input):
	try:
		twituser = input.group(2)
		twituser = str(twituser)
		info = api.GetUser(twituser)
		friendcount = info.friends_count
		name = info.name
		id = info.id
		favourites = info.favourites_count
		followers = info.followers_count
		location = info.location
		description = info.description
		jenney.reply("<" + str(twituser) + "> " + str(name) + ". " + "ID: " + str(id) + ". Friend Count: " + str(friendcount) + ". Followers: " + str(followers) + ". Favourites: " + str(favourites) + ". Location: " + str(location) + ". Description: " + str(description))
	except:
		jenney.reply("You have inputted an invalid user.")
f_info.commands = ['twitinfo']
f_info.priority = 'medium'
f_info.example = '.twitinfo aplsuk'

def f_update(jenney, input):
	try:
		api2 = twitter.Api(username=str(input.twitter_username), password=str(input.twitter_password))
		update = str(input.group(2)) + " ^" + input.nick
		if len(update) <= 140:
			api2.PostUpdates(update)
			jenney.reply("Successfully posted to twitter.com/" + input.twitter_username)
		else:
			toofar = len(update) - 140
			jenney.reply("Please shorten the length of your message by: " + str(toofar) + " characters.")
	except:
		jenney.reply("There was a problem posting to Jenney's Twitter page.")
f_update.commands = ['tweet']
f_update.priority = 'medium'
f_update.example = '.twitup Hello World!'

def f_reply(jenney, input):
	api3 = twitter.Api(username=str(input.twitter_username), password=str(input.twitter_password))
	incoming = str(input.group(2))
	incoming = incoming.split()
	statusid = incoming[0]
	if statusid.isdigit():
		update = incoming[1:]
		if len(update) <= 140:
			statusid = int(statusid)
			api3.PostUpdate(str(" ".join(update)), in_reply_to_status_id=10503164300)
			jenney.reply("Successfully posted to twitter.com/jenney_osu")
		else:
			toofar = len(update) - 140
			jenney.reply("Please shorten the length of your message by: " + str(toofar) + " characters.")
	else:
		jenney.reply("Please provide a status ID.")
#f_reply.commands = ['reply']
f_reply.priority = 'medium'
f_reply.example = '.reply 892379487 I like that idea!'

if __name__ == '__main__':
	print __doc__.strip()
