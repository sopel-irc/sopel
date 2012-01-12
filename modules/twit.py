#!/usr/bin/env python
"""
twitter.py - jenni Twitter Module
Copyright 2008-10, Michael Yanovich, opensource.osu.edu/~yanovich/wiki/
Tweetwatch features copyright 2011, Edward Powell, embolalia.net
Licensed under the Eiffel Forum License 2.

http://inamidst.com/phenny/

For this module to work, you need to create 2 variables in your config file ( ~/.jenni/default.py ). The first one "twitter_username" with the username you have registered on twitter, and "twitter_password" with the password for that twitter account.
"""
import simplejson
import twitter
import sched, time

api = twitter.Api()

twitter_watch = ['hankgreen', 'realjohngreen', 'NerdfighterIRC']
watch_wait = 75
watch = False
lasts = dict()
sch = sched.scheduler(time.time, time.sleep)

def gettweet(jenni, input):
	try:
		twituser = input.group(2)
		twituser = str(twituser)
		statuses = api.GetUserTimeline(twituser)
		recent = [s.text for s in statuses][0]
		#jenni.say("<" + twituser + "> " + unicode(recent))
		if twituser[0] != '@': twituser = '@' + twituser
		jenni.say(twituser + ": " + unicode(recent))
	except:
		jenni.reply("You have inputted an invalid user.")
gettweet.commands = ['twit']
gettweet.priority = 'medium'
gettweet.example = '.twit aplusk'

def f_info(jenni, input):
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
		jenni.reply("<" + str(twituser) + "> " + str(name) + ". " + "ID: " + str(id) + ". Friend Count: " + str(friendcount) + ". Followers: " + str(followers) + ". Favourites: " + str(favourites) + ". Location: " + str(location) + ". Description: " + str(description))
	except:
		jenni.reply("You have inputted an invalid user.")
f_info.commands = ['twitinfo']
f_info.priority = 'medium'
f_info.example = '.twitinfo aplsuk'

def f_update(jenni, input):
	try:
		api2 = twitter.Api(username=str(input.twitter_username), password=str(input.twitter_password))
		update = str(input.group(2)) + " ^" + input.nick
		if len(update) <= 140:
			api2.PostUpdates(update)
			jenni.reply("Successfully posted to twitter.com/jenni_osu")
		else:
			toofar = len(update) - 140
			jenni.reply("Please shorten the length of your message by: " + str(toofar) + " characters.")
	except:
		jenni.reply("There was a problem posting to jenni's Twitter page.")
f_update.commands = ['tweet']
f_update.priority = 'medium'
f_update.example = '.twitup Hello World!'

def f_reply(jenni, input):
	api3 = twitter.Api(username=str(input.twitter_username), password=str(input.twitter_password))
	incoming = str(input.group(2))
	incoming = incoming.split()
	statusid = incoming[0]
	if statusid.isdigit():
		update = incoming[1:]
		if len(update) <= 140:
			statusid = int(statusid)
			api3.PostUpdate(str(" ".join(update)), in_reply_to_status_id=10503164300)
			jenni.reply("Successfully posted to twitter.com/jenni_osu")
		else:
			toofar = len(update) - 140
			jenni.reply("Please shorten the length of your message by: " + str(toofar) + " characters.")
	else:
		jenni.reply("Please provide a status ID.")
#f_reply.commands = ['reply']
f_reply.priority = 'medium'
f_reply.example = '.reply 892379487 I like that idea!'

def twat(jenni,input):
    f_info(jenni,input)
twat.commands = ['twatinfo']


#Tweetwatch functions
def saylast(jenni, input):
   global lasts
   global watch
   global sch

   if watch:
      for twituser in twitter_watch:
         try:
            statuses = api.GetUserTimeline(twituser)
            recent = unicode([s.text for s in statuses][0])
            if twituser not in lasts or lasts[twituser] != recent:
               jenni.say("TWEETWATCH: @" + twituser + ": " + recent)
               lasts[twituser] = recent
         except Exception as inst:
            #RuntimeError: maximum recursion depth exceeded while calling a Python object

            #commenting the exception from the live channel, to be moved to the devchan.
            #jenni.reply("An exception was raised for user: " + twituser)
            #jenni.reply("Is this user valid?")

            jenni.msg(input.devchan,"[DEVMSG]Exception in saylast(), twit.py (line 100).")
            jenni.msg(input.devchan,"[Exception]"+str(type(inst))+": "+str(inst.args)+", "+str(inst)+".") #this is also put in the logfile.
            jenni.msg(input.devchan,"[Vardump]lasts: "+str(lasts)+", recent: "+str(recent)+", statuses: "+str(statuses)+", twituser: "+str(twituser)+".")
            print type(inst)
            print inst.args
            print inst
      sch.enter(watch_wait, 1, saylast, (jenni, input))
      sch.run()

def tweetwatcher(jenni, input):
   global watch
   global sch #are we using this variable? I'm pretty sure we're not.
   if input.admin:
      if input.group(2) == 'off':
         watch = False
         jenni.say("Tweetwatcher is now off.")
      elif input.group(2) == 'on':
         watch = True
         saylast(jenni, input)
         jenni.say("I will now watch for new tweets.")
tweetwatcher.commands = ['tweetwatcher']

if __name__ == '__main__':
	print __doc__.strip()
