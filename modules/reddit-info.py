"""
reddit.py - jenni reddit module
Author: Edward Powell, embolalia.net
About: http://inamidst.com/phenny

This module provides special tools for reddit, namely showing detailed info about reddit posts
"""

import reddit

def rpost_info(jenni, input):
    r = reddit.Reddit(user_agent='phenny / jenni IRC bot - see dft.ba/-williesource for more')
    s = r.get_submission(url=input.group(1))
    
    message = '[REDDIT] '+s.title
    if s.is_self: message = message + ' (self.' + s.subreddit.display_name + ')'
    else: message = message + ' (' + s.url + ')' +' to r/'+s.subreddit.display_name
    if s.over_18:
        message = message + ' 05[NSFW]'
        #TODO implement per-channel settings db, and make this able to kick
    message = message +' | ' + str(s.ups-s.downs)+' points (03'\
                      +str(s.ups)+'|05'+str(s.downs)+') | '+str(s.num_comments)\
                      +' comments | Posted by '+s.author.name
    #TODO add creation time with s.created
    jenni.say(message)
rpost_info.rule = '.*(http(?:s)?://(www\.)?reddit\.com/r/.*?/comments/[\w-]+).*'

def redditor_info(jenni, input):
    print 'in'
    r = reddit.Reddit(user_agent='phenny / jenni IRC bot - see dft.ba/-williesource for more')
    u = r.get_redditor(input.group(2))#Handling auto-expansion and by command in the same function.
    
    message = '[REDDITOR] '+u.name
    if input.group(1) == '.redditor': message = message + ' | http://reddit.com/u/'+u.name
    if u.is_gold: message = message + ' | 08Gold'
    if u.is_mod: message = message + ' | 05Mod'
    message = message + ' | Link: '+str(u.link_karma)+ ' | Comment: '+str(u.comment_karma)
    
    #TODO detect cake day with u.created
    jenni.say(message)
#If you change this, you'll have to change some things above.
redditor_info.commands = ['redditor']

def auto_redditor_info(jenni, input):
    redditor_info(jenni, input)
#If you change the groups here, you'll have to change some things above.
auto_redditor_info.rule = '.*http(?:s)?://(?:www\.)?reddit\.com/u(ser)?/([\w-]+).*'
