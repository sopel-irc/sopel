# coding=utf8
"""
reddit-info.py - Willie Reddit module
Author: Edward Powell, embolalia.net
About: http://willie.dftba.net

This module provides special tools for reddit, namely showing detailed info about reddit posts
"""
from __future__ import unicode_literals

from willie.module import commands, rule, example, NOLIMIT
from willie import tools
import praw
import re
domain = r'https?://(?:www\.|np\.)?reddit\.com'
post_url = '(%s/r/.*?/comments/[\w-]+)' % domain
user_url = '%s/u(ser)?/([\w-]+)' % domain


def setup(bot):
    post_regex = re.compile(post_url)
    user_regex = re.compile(user_url)
    if not bot.memory.contains('url_callbacks'):
        bot.memory['url_callbacks'] = tools.WillieMemory()
    bot.memory['url_callbacks'][post_regex] = rpost_info
    bot.memory['url_callbacks'][user_regex] = redditor_info


@rule('.*%s.*' % post_url)
def rpost_info(bot, trigger, match=None):
    r = praw.Reddit(user_agent='phenny / willie IRC bot - see dft.ba/-williesource for more')
    match = match or trigger
    s = r.get_submission(url=match.group(1))

    message = '[REDDIT] ' + s.title
    if s.is_self:
        message = message + ' (self.' + s.subreddit.display_name + ')'
    else:
        message = message + ' (' + s.url + ')' + ' to r/' + s.subreddit.display_name
    if s.over_18:
        message = message + ' 05[NSFW]'
        #TODO implement per-channel settings db, and make this able to kick
    if s.author:
        author = s.author.name
    else:
        author = '[deleted]'
    message = (message + ' | ' + str(s.ups - s.downs) + ' points (03'
               + str(s.ups) + '|05' + str(s.downs) + ') | ' +
               str(s.num_comments) + ' comments | Posted by ' + author)
    #TODO add creation time with s.created
    bot.say(message)


#If you change this, you'll have to change some other things...
@commands('redditor')
def redditor_info(bot, trigger, match=None):
    """Show information about the given Redditor"""
    commanded = re.match(bot.config.prefix + 'redditor', trigger)
    r = praw.Reddit(user_agent='phenny / willie IRC bot - see dft.ba/-williesource for more')
    match = match or trigger
    try:
        u = r.get_redditor(match.group(2))
    except:
        if commanded:
            bot.say('No such Redditor.')
            return NOLIMIT
        else:
            return
        #Fail silently if it wasn't an explicit command.

    message = '[REDDITOR] ' + u.name
    if commanded:
        message = message + ' | http://reddit.com/u/' + u.name
    if u.is_gold:
        message = message + ' | 08Gold'
    if u.is_mod:
        message = message + ' | 05Mod'
    message = message + ' | Link: ' + str(u.link_karma) + ' | Comment: ' + str(u.comment_karma)

    #TODO detect cake day with u.created
    bot.say(message)


#If you change the groups here, you'll have to change some things above.
@rule('.*%s.*' % user_url)
def auto_redditor_info(bot, trigger):
    redditor_info(bot, trigger)
