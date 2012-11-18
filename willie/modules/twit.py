"""
twitter.py - Willie Twitter Module
Copyright 2008-10, Michael Yanovich, opensource.osu.edu/~yanovich/wiki/
Copyright 2011, Edward Powell, embolalia.net
Licensed under the Eiffel Forum License 2.

http://willie.dftba.net
"""
import tweepy
import time
import re

def configure(config):
    """
    These values are all found by signing up your bot at 
    [api.twitter.com](http://api.twitter.com).
    
    | [twitter] | example | purpose |
    | --------- | ------- | ------- |
    | consumer_key | 09d8c7b0987cAQc7fge09 | OAuth consumer key |
    | consumer_secret | LIaso6873jI8Yasdlfi76awer76yhasdfi75h6TFJgf | OAuth consumer secret |
    | access_token | 564018348-Alldf7s6598d76tgsadfo9asdf56uUf65aVgdsf6 | OAuth access token |
    | access_token_secret | asdfl7698596KIKJVGvJDcfcvcsfdy85hfddlku67 | OAuth access token secret |
    """
    
    if config.option('Configure Twitter? (You will need to register on http://api.twitter.com)', False):
        config.interactive_add('twitter', 'consumer_key', 'Consumer key')
        config.interactive_add('twitter', 'consumer_secret', 'Consumer secret')
        config.interactive_add('twitter', 'access_token', 'Access token')
        config.interactive_add('twitter', 'access_token_secret', 'Access token secret')

def format_thousands(integer):
    """Returns string of integer, with thousands separated by ','"""
    return re.sub(r'(\d{3})(?=\d)', r'\1,', str(integer)[::-1])[::-1]

def gettweet(willie, trigger):
    """Show the last tweet by the given user"""
    try:
        auth = tweepy.OAuthHandler(willie.config.twitter.consumer_key, willie.twitter.config.consumer_secret)
        auth.set_access_token(willie.config.twitter.access_token, willie.config.twitter.access_token_secret)
        api = tweepy.API(auth)
        
        twituser = trigger.group(2)
        twituser = str(twituser)

        statuses = api.user_timeline(twituser)
        recent = [s.text for s in statuses][0]
        #willie.say("<" + twituser + "> " + unicode(recent))
        if twituser[0] != '@': twituser = '@' + twituser
        willie.say(twituser + ": " + unicode(recent))
    except:
        willie.reply("You have inputted an invalid user.")
gettweet.commands = ['twit']
gettweet.priority = 'medium'
gettweet.example = '.twit aplusk'

def f_info(willie, trigger):
    """Show information about the given Twitter account"""
    try:
        auth = tweepy.OAuthHandler(willie.config.twitter.consumer_key, willie.config.twitter.consumer_secret)
        auth.set_access_token(willie.config.twitter.access_token, willie.config.twitter.access_token_secret)
        api = tweepy.API(auth)
        
        twituser = trigger.group(2)
        twituser = str(twituser)

        info = api.get_user(twituser)
        friendcount = format_thousands(info.friends_count)
        name = info.name
        id = info.id
        favourites = info.favourites_count
        followers = format_thousands(info.followers_count)
        location = info.location
        description = info.description
        willie.reply("@" + str(twituser) + ": " + str(name) + ". " + "ID: " + str(id) + ". Friend Count: " + friendcount + ". Followers: " + followers + ". Favourites: " + str(favourites) + ". Location: " + str(location) + ". Description: " + str(description))
    except:
        willie.reply("You have inputted an invalid user.")
f_info.commands = ['twitinfo']
f_info.priority = 'medium'
f_info.example = '.twitinfo aplsuk'

def f_update(willie, trigger):
    """Tweet with Willie's account. Admin-only."""
    if trigger.admin:
        auth = tweepy.OAuthHandler(willie.config.twitter.consumer_key, willie.config.twitter.consumer_secret)
        auth.set_access_token(willie.config.twitter.access_token, willie.config.twitter.access_token_secret)
        api = tweepy.API(auth)
        
        print api.me().name
        
        update = str(trigger.group(2)) + " ^" + trigger.nick
        if len(update) <= 140:
            api.update_status(update)
            willie.reply("Successfully posted to my twitter account.")
        else:
            toofar = len(update) - 140
            willie.reply("Please shorten the length of your message by: " + str(toofar) + " characters.")
f_update.commands = ['tweet']
f_update.priority = 'medium'
f_update.example = '.tweet Hello World!'

def f_reply(willie, trigger):
    auth = tweepy.OAuthHandler(willie.config.twitter.consumer_key, willie.config.twitter.consumer_secret)
    auth.set_access_token(access_token, access_token_secret)
    api = tweepy.API(auth)
    
    incoming = str(trigger.group(2))
    incoming = incoming.split()
    statusid = incoming[0]
    if statusid.isdigit():
        update = incoming[1:]
        if len(update) <= 140:
            statusid = int(statusid)
            #api3.PostUpdate(str(" ".join(update)), in_reply_to_status_id=10503164300)
            willie.reply("Successfully posted to my twitter account.")
        else:
            toofar = len(update) - 140
            willie.reply("Please shorten the length of your message by: " + str(toofar) + " characters.")
    else:
        willie.reply("Please provide a status ID.")
#f_reply.commands = ['reply']
f_reply.priority = 'medium'
f_reply.example = '.reply 892379487 I like that idea!'

if __name__ == '__main__':
    print __doc__.strip()
