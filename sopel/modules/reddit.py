# coding=utf-8
"""
reddit-info.py - Sopel Reddit module
Author: Edward Powell, embolalia.net
About: http://sopel.chat

This module provides special tools for reddit, namely showing detailed
info about reddit posts
"""
from __future__ import unicode_literals, absolute_import, print_function, division

from sopel.module import commands, rule, example, NOLIMIT, OP
from sopel.formatting import bold, color, colors
from sopel.web import USER_AGENT
from sopel.tools import SopelMemory, time
import datetime as dt
import praw
import re
import sys
if sys.version_info.major >= 3:
    unicode = str
    if sys.version_info.minor >= 4:
        from html import unescape
    else:
        from html.parser import HTMLParser
        unescape = HTMLParser().unescape
else:
    from HTMLParser import HTMLParser
    unescape = HTMLParser().unescape


domain = r'https?://(?:www\.|np\.)?reddit\.com'
post_url = '(%s/r/.*?/comments/[\w-]+)' % domain
user_url = '%s/u(ser)?/([\w-]+)' % domain
post_regex = re.compile(post_url)
user_regex = re.compile(user_url)


def setup(bot):
    if not bot.memory.contains('url_callbacks'):
        bot.memory['url_callbacks'] = SopelMemory()
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
               '{comments} comments | Posted by {author} | '
               'Created at {created}')

    if s.is_self:
        link = '(self.{})'.format(s.subreddit.display_name)
    else:
        link = '({}) to r/{}'.format(s.url, s.subreddit.display_name)

    if s.over_18:
        nsfw = bold(color(' [NSFW]', colors.RED))
        sfw = bot.db.get_channel_value(trigger.sender, 'sfw')
        if sfw:
            link = '(link hidden)'
            bot.write(['KICK', trigger.sender, trigger.nick,
                       'Linking to NSFW content in a SFW channel.'])
    else:
        nsfw = ''

    if s.author:
        author = s.author.name
    else:
        author = '[deleted]'

    tz = time.get_timezone(bot.db, bot.config, None, trigger.nick,
                           trigger.sender)
    time_created = dt.datetime.utcfromtimestamp(s.created_utc)
    created = time.format_time(bot.db, bot.config, tz, trigger.nick,
                               trigger.sender, time_created)

    if s.score > 0:
        point_color = colors.GREEN
    else:
        point_color = colors.RED

    percent = color(unicode(s.upvote_ratio * 100) + '%', point_color)

    title = unescape(s.title)
    message = message.format(
        title=title, link=link, nsfw=nsfw, points=s.score, percent=percent,
        comments=s.num_comments, author=author, created=created)

    bot.say(message)


# If you change this, you'll have to change some other things...
@commands('redditor')
@example('.redditor poem_for_your_sprog')
def redditor_info(bot, trigger, match=None):
    """Show information about the given Redditor"""
    commanded = re.match(bot.config.core.prefix + 'redditor', trigger)
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
        # Fail silently if it wasn't an explicit command.

    message = '[REDDITOR] ' + u.name
    now = dt.datetime.utcnow()
    cakeday_start = dt.datetime.utcfromtimestamp(u.created_utc)
    cakeday_start = cakeday_start.replace(year=now.year)
    day = dt.timedelta(days=1)
    year_div_by_400 = now.year % 400 == 0
    year_div_by_100 = now.year % 100 == 0
    year_div_by_4 = now.year % 4 == 0
    is_leap = year_div_by_400 or ((not year_div_by_100) and year_div_by_4)
    if (not is_leap) and ((cakeday_start.month, cakeday_start.day) == (2, 29)):
        # If cake day is 2/29 and it's not a leap year, cake day is 1/3.
        # Cake day begins at exact account creation time.
        is_cakeday = cakeday_start + day <= now <= cakeday_start + (2 * day)
    else:
        is_cakeday = cakeday_start <= now <= cakeday_start + day

    if is_cakeday:
        message = message + ' | 13Cake day'
    if commanded:
        message = message + ' | http://reddit.com/u/' + u.name
    if u.is_gold:
        message = message + ' | 08Gold'
    if u.is_mod:
        message = message + ' | 05Mod'
    message = message + (' | Link: ' + str(u.link_karma) + ' | Comment: '
                         + str(u.comment_karma))

    bot.say(message)


# If you change the groups here, you'll have to change some things above.
@rule('.*%s.*' % user_url)
def auto_redditor_info(bot, trigger):
    redditor_info(bot, trigger)


@commands('setsafeforwork', 'setsfw')
@example('.setsfw true')
@example('.setsfw false')
def update_channel(bot, trigger):
    """
    Sets the Safe for Work status (true or false) for the current
    channel. Defaults to false.
    """
    if bot.privileges[trigger.sender][trigger.nick] < OP:
        return
    else:
        sfw = trigger.group(3).strip().lower() == 'true'
        bot.db.set_channel_value(trigger.sender, 'sfw', sfw)
        if sfw:
            bot.reply('Got it. %s is now flagged as SFW.' % trigger.sender)
        else:
            bot.reply('Got it. %s is now flagged as NSFW.' % trigger.sender)


@commands('getsafeforwork', 'getsfw')
@example('.getsfw [channel]')
def get_channel_sfw(bot, trigger):
    """
    Gets the preferred channel's Safe for Work status, or the current
    channel's status if no channel given.
    """
    channel = trigger.group(2)
    if not channel:
        channel = trigger.sender

    channel = channel.strip()

    sfw = bot.db.get_channel_value(channel, 'sfw')
    if sfw:
        bot.say('%s is flagged as SFW' % channel)
    else:
        bot.say('%s is flagged as NSFW' % channel)
