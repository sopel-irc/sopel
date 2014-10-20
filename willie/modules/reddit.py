# coding=utf8
"""
reddit-info.py - Willie Reddit module
Author: Edward Powell, embolalia.net
About: http://willie.dftba.net

This module provides special tools for reddit, namely showing detailed info about reddit posts
"""
from __future__ import unicode_literals

from willie.module import commands, rule, example, NOLIMIT
from willie.formatting import bold, color, colors
from willie.web import USER_AGENT
from willie import tools
import praw
import re
import sys
if sys.version_info.major >= 3:
    unicode = str

domain = r'https?://(?:www\.|np\.)?reddit\.com'
post_url = '(%s/r/.*?/comments/[\w-]+)' % domain
user_url = '%s/u(ser)?/([\w-]+)' % domain
post_regex = re.compile(post_url)
user_regex = re.compile(user_url)


def setup(bot):
    if not bot.memory.contains('url_callbacks'):
        bot.memory['url_callbacks'] = tools.WillieMemory()
    bot.memory['url_callbacks'][post_regex] = rpost_info
    bot.memory['url_callbacks'][user_regex] = redditor_info


def shutdown(bot):
    del bot.memory['url_callbacks'][post_regex]
    del bot.memory['url_callbacks'][user_regex]


@rule('.*%s.*' % post_url)
def rpost_info(bot, trigger, match=None):
    r = praw.Reddit(user_agent=USER_AGENT)
    match = match or trigger
    s = r.get_submission(url=match.group(1))

    message = ('[REDDIT] {title} {link}{nsfw} | {points} points ({percent}) | '
               '{comments} comments | Posted by {author}')

    if s.is_self:
        link = '(self.{})'.format(s.subreddit.display_name)
    else:
        link = '({}) to r/{}'.format(s.url, s.subreddit.display_name)

    if s.over_18:
        nsfw = bold(color(' [NSFW]', colors.RED))
        #TODO implement per-channel settings db, and make this able to kick
    else:
        nsfw = ''

    if s.author:
        author = s.author.name
    else:
        author = '[deleted]'
    #TODO add creation time with s.created

    if s.score > 0:
        point_color = colors.GREEN
    else:
        point_color = colors.RED

    percent = color(unicode(s.upvote_ratio * 100) + '%', point_color)

    message = message.format(
        title=s.title, link=link, nsfw=nsfw, points=s.score, percent=percent,
        comments=s.num_comments, author=author)
    bot.say(message)


#If you change this, you'll have to change some other things...
@commands('redditor')
def redditor_info(bot, trigger, match=None):
    """Show information about the given Redditor"""
    commanded = re.match(bot.config.prefix + 'redditor', trigger)
    r = praw.Reddit(user_agent=USER_AGENT)
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
