#!/usr/bin/env python
"""
twitter.py - jenni Twitter Module
Copyright 2008-10, Michael Yanovich, opensource.osu.edu/~yanovich/wiki/
Tweetwatch features copyright 2011, Edward Powell, embolalia.net
Licensed under the Eiffel Forum License 2.

http://inamidst.com/phenny/

For this module to work, you must register the application with Twitter, and
create the variables consumer_key, consumer_secret, access_token, and
access_token_secret in your config file (~/.jenni/default.py).

#For this module to work, you need to create 2 variables in your config file ( ~/.jenni/default.py ). The first one 
#"twitter_username" with the username you have registered on twitter, and "twitter_password" with the password for that twitter 
#account.
"""
import simplejson
import tweepy
import sched, time
import re

twitter_watch = ['hankgreen', 'realjohngreen', 'NerdfighterIRC']
watch_wait = 75
watch = False
lasts = dict()
sch = sched.scheduler(time.time, time.sleep)

def format_thousands(integer):
    """Returns string of integer, with thousands separated by ','"""
    return re.sub(r'(\d{3})(?=\d)', r'\1,', str(integer)[::-1])[::-1]

def gettweet(jenni, input):
    try:
        auth = tweepy.OAuthHandler(jenni.config.consumer_key, jenni.config.consumer_secret)
        auth.set_access_token(jenni.config.access_token, jenni.config.access_token_secret)
        api = tweepy.API(auth)
        
        twituser = input.group(2)
        twituser = str(twituser)

        statuses = api.user_timeline(twituser)
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
        auth = tweepy.OAuthHandler(jenni.config.consumer_key, jenni.config.consumer_secret)
        auth.set_access_token(jenni.config.access_token, jenni.config.access_token_secret)
        api = tweepy.API(auth)
        
        twituser = input.group(2)
        twituser = str(twituser)

        info = api.get_user(twituser)
        friendcount = format_thousands(info.friends_count)
        name = info.name
        id = info.id
        favourites = info.favourites_count
        followers = format_thousands(info.followers_count)
        location = info.location
        description = info.description
        jenni.reply("@" + str(twituser) + ": " + str(name) + ". " + "ID: " + str(id) + ". Friend Count: " + friendcount + ". Followers: " + followers + ". Favourites: " + str(favourites) + ". Location: " + str(location) + ". Description: " + str(description))
    except:
        jenni.reply("You have inputted an invalid user.")
f_info.commands = ['twitinfo']
f_info.priority = 'medium'
f_info.example = '.twitinfo aplsuk'

def f_update(jenni, input):
    if input.admin:
        auth = tweepy.OAuthHandler(jenni.config.consumer_key, jenni.config.consumer_secret)
        auth.set_access_token(jenni.config.access_token, jenni.config.access_token_secret)
        api = tweepy.API(auth)
        
        print api.me().name
        
        update = str(input.group(2)) + " ^" + input.nick
        if len(update) <= 140:
            api.update_status(update)
            jenni.reply("Successfully posted to my twitter account.")
        else:
            toofar = len(update) - 140
            jenni.reply("Please shorten the length of your message by: " + str(toofar) + " characters.")
f_update.commands = ['tweet']
f_update.priority = 'medium'
f_update.example = '.twitup Hello World!'

def f_reply(jenni, input):
    auth = tweepy.OAuthHandler(jenni.config.consumer_key, jenni.config.consumer_secret)
    auth.set_access_token(access_token, access_token_secret)
    api = tweepy.API(auth)
    
    incoming = str(input.group(2))
    incoming = incoming.split()
    statusid = incoming[0]
    if statusid.isdigit():
        update = incoming[1:]
        if len(update) <= 140:
            statusid = int(statusid)
            #api3.PostUpdate(str(" ".join(update)), in_reply_to_status_id=10503164300)
            jenni.reply("Successfully posted to my twitter account.")
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
   
   auth = tweepy.OAuthHandler(jenni.config.consumer_key, jenni.config.consumer_secret)
   auth.set_access_token(jenni.config.access_token, jenni.config.access_token_secret)
   api = tweepy.API(auth)

   while watch:
      for twituser in twitter_watch:
         try:
            statuses = api.user_timeline(twituser)
            recent = unicode([s.text for s in statuses][0])
            if twituser not in lasts or lasts[twituser] != recent:
               jenni.say("TWEETWATCH: @" + twituser + ": " + recent)
               lasts[twituser] = recent
         except Exception as inst:
            if str(inst) = "status code = 503":
                jenni.msg(input.devchan,"[DEVMSG] Twitter returned HTTP code 503: Service Unavailable."
            else:
                jenni.msg(input.devchan,"[DEVMSG]Exception in saylast(), twit.py (line 100).")
                jenni.msg(input.devchan,"[Exception]"+str(type(inst))+": "+str(inst.args)+", "+str(inst)+".") #this is also put in the logfile.
                jenni.msg(input.devchan,"[Vardump]twituser: "+str(twituser)+"recent: "+str(recent)+", Lasts:")
                for last in lasts:
                    jenni.msg(input.devchan,"    "+str(last))
                print type(inst)
                print inst.args
                print inst
      time.sleep(watch_wait)
      #sch.enter(watch_wait, 1, saylast, (jenni, input))
      #sch.run()

def tweetwatcher(jenni, input):
   global watch
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
