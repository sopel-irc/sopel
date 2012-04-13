"""
reddit.py - jenni reddit module
Author: Edward Powell, embolalia.net
About: http://inamidst.com/phenny

This module provides special tools for reddit, namely showing detailed info about reddit posts
"""

import reddit

def reddit_info(jenni, input):
    r = reddit.Reddit(user_agent='asdf')
    s = r.get_submission(url=input.group(1))
    
    message = '[REDDIT] '+s.title
    if s.is_self: message = message + '(self.' + subreddit + ')'
    else: message = message + '(' + s.url + ')'
    message = message +' to r/'+s.subreddit+' | '+(s.ups-s.downs)+'points (08'\
                      +s.ups+'|12'+s.downs+') | '+s.num_comments+' comments | '\
                      +s.created+' by '+s.author.name
    jenni.say(message)
reddit_info.rule = '.*(http(?:s)?://(www\.)?reddit\.com/r/.*?/comments/[\w-]+).*'
