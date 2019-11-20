# coding=utf-8
"""
reddit.py - Sopel Reddit Module
Copyright 2012, Elsie Powell, embolalia.com
Copyright 2019, dgw, technobabbl.es
Licensed under the Eiffel Forum License 2.

https://sopel.chat
"""
from __future__ import unicode_literals, absolute_import, print_function, division

import datetime as dt
import re
import sys
import textwrap

import praw
import prawcore
import requests

from sopel.formatting import bold, color, colors
from sopel.module import commands, example, require_chanmsg, url, NOLIMIT, OP
from sopel.tools import time
from sopel.tools.web import USER_AGENT

# clean up all of this when dropping py2/old py3 versions
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


domain = r'https?://(?:www\.|old\.|pay\.|ssl\.|[a-z]{2}\.)?reddit\.com'
post_url = r'%s/r/.*?/comments/([\w-]+)/?$' % domain
short_post_url = r'https?://redd.it/([\w-]+)'
user_url = r'%s/u(ser)?/([\w-]+)' % domain
comment_url = r'%s/r/.*?/comments/.*?/.*?/([\w-]+)' % domain
image_url = r'https?://i.redd.it/\S+'
video_url = r'https?://v.redd.it/([\w-]+)'


def setup(bot):
    if 'reddit_praw' not in bot.memory:
        # Create a PRAW instance just once, at load time
        bot.memory['reddit_praw'] = praw.Reddit(
            user_agent=USER_AGENT,
            client_id='6EiphT6SSQq7FQ',
            client_secret=None,
        )


def shutdown(bot):
    # Clean up shared PRAW instance
    bot.memory.pop('reddit_praw', None)


@url(image_url)
def image_info(bot, trigger, match):
    url = match.group(0)
    results = list(
        bot.memory['reddit_praw']
        .subreddit('all')
        .search('url:{}'.format(url), sort='new')
    )
    oldest = results[-1]
    return say_post_info(bot, trigger, oldest.id)


@url(video_url)
def video_info(bot, trigger, match):
    # Get the video URL with a cheeky hack
    url = requests.head(
        'https://www.reddit.com/video/{}'.format(match.group(1)),
        timeout=(10.0, 4.0)).headers['Location']
    return say_post_info(bot, trigger, re.match(post_url, url).group(1))


@url(post_url)
@url(short_post_url)
def rpost_info(bot, trigger, match):
    match = match or trigger
    return say_post_info(bot, trigger, match.group(1))


def say_post_info(bot, trigger, id_):
    try:
        s = bot.memory['reddit_praw'].submission(id=id_)

        message = ('[REDDIT] {title} {link}{nsfw} | {points} points ({percent}) | '
                   '{comments} comments | Posted by {author} | '
                   'Created at {created}')

        subreddit = s.subreddit.display_name
        if s.is_self:
            link = '(self.{})'.format(subreddit)
        else:
            link = '({}) to r/{}'.format(s.url, subreddit)

        nsfw = ''
        if s.over_18:
            nsfw += ' ' + bold(color('[NSFW]', colors.RED))

            sfw = bot.db.get_channel_value(trigger.sender, 'sfw')
            if sfw:
                link = '(link hidden)'
                bot.kick(
                    trigger.nick, trigger.sender,
                    'Linking to NSFW content in a SFW channel.'
                )
        if s.spoiler:
            nsfw += ' ' + bold(color('[SPOILER]', colors.GRAY))

            spoiler_free = bot.db.get_channel_value(trigger.sender, 'spoiler_free')
            if spoiler_free:
                link = '(link hidden)'
                bot.kick(
                    trigger.nick, trigger.sender,
                    'Linking to spoiler content in a spoiler-free channel.'
                )

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
    except prawcore.exceptions.NotFound:
        bot.say('No such post.')
        return NOLIMIT


@url(comment_url)
def comment_info(bot, trigger, match):
    """Shows information about the linked comment"""
    try:
        c = bot.memory['reddit_praw'].comment(match.group(1))
    except prawcore.exceptions.NotFound:
        bot.say('No such comment.')
        return NOLIMIT

    message = ('[REDDIT] Comment by {author} | {points} points | '
               'Posted at {posted} | {comment}')

    if c.author:
        author = c.author.name
    else:
        author = '[deleted]'

    tz = time.get_timezone(bot.db, bot.config, None, trigger.nick,
                           trigger.sender)
    time_posted = dt.datetime.utcfromtimestamp(c.created_utc)
    posted = time.format_time(bot.db, bot.config, tz, trigger.nick,
                              trigger.sender, time_posted)

    # stolen from the function I (dgw) wrote for our github plugin
    lines = [line for line in c.body.splitlines() if line and line[0] != '>']
    short = textwrap.wrap(lines[0], 250)[0]
    if len(lines) > 1 or short != lines[0]:
        short += ' […]'

    message = message.format(
        author=author, points=c.score, posted=posted, comment=short)

    bot.say(message)


# If you change this, you'll have to change some other things...
@commands('redditor')
@example('.redditor poem_for_your_sprog')
def redditor_info(bot, trigger, match=None):
    """Shows information about the given Redditor"""
    commanded = re.match(bot.config.core.prefix + 'redditor', trigger)
    match = match or trigger
    try:
        u = bot.memory['reddit_praw'].redditor(match.group(2))
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
            # If cake day is 2/29 and it's not a leap year, cake day is 3/1.
            # Cake day begins at exact account creation time.
            is_cakeday = cakeday_start + day <= now <= cakeday_start + (2 * day)
        else:
            is_cakeday = cakeday_start <= now <= cakeday_start + day

        if is_cakeday:
            message = message + ' | ' + bold(color('Cake day', colors.LIGHT_PURPLE))
        if commanded:
            message = message + ' | https://reddit.com/u/' + u.name
        if u.is_gold:
            message = message + ' | ' + bold(color('Gold', colors.YELLOW))
        if u.is_mod:
            message = message + ' | ' + bold(color('Mod', colors.GREEN))
        message = message + (' | Link: ' + str(u.link_karma) +
                             ' | Comment: ' + str(u.comment_karma))

        bot.say(message)
    except prawcore.exceptions.NotFound:
        if commanded:
            bot.say('No such Redditor.')
        # Fail silently if it wasn't an explicit command.
        return NOLIMIT


# If you change the groups here, you'll have to change some things above.
@url(user_url)
def auto_redditor_info(bot, trigger, match):
    redditor_info(bot, trigger, match)


@require_chanmsg('.setsfw is only permitted in channels')
@commands('setsafeforwork', 'setsfw')
@example('.setsfw true')
@example('.setsfw false')
def set_channel_sfw(bot, trigger):
    """
    Sets the Safe for Work status (true or false) for the current
    channel. Defaults to false.
    """
    if bot.channels[trigger.sender].privileges[trigger.nick] < OP:
        return
    else:
        param = 'true'
        if trigger.group(2) and trigger.group(3):
            param = trigger.group(3).strip().lower()
        sfw = param == 'true'
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
        if channel.is_nick():
            return bot.say('{}getsfw with no channel param is only permitted in '
                           'channels'.format(bot.config.core.help_prefix))

    channel = channel.strip()

    sfw = bot.db.get_channel_value(channel, 'sfw')
    if sfw:
        bot.say('%s is flagged as SFW' % channel)
    else:
        bot.say('%s is flagged as NSFW' % channel)


@require_chanmsg('.setspoilfree is only permitted in channels')
@commands('setspoilerfree', 'setspoilfree')
@example('.setspoilfree true')
@example('.setspoilfree false')
def set_channel_spoiler_free(bot, trigger):
    """
    Sets the Spoiler-Free status (true or false) for the current channel.
    Defaults to false.
    """
    if bot.channels[trigger.sender].privileges[trigger.nick] < OP:
        return
    else:
        param = 'true'
        if trigger.group(2) and trigger.group(3):
            param = trigger.group(3).strip().lower()
        spoiler_free = param == 'true'
        bot.db.set_channel_value(trigger.sender, 'spoiler_free', spoiler_free)
        if spoiler_free:
            bot.reply('Got it. %s is now flagged as spoiler-free.' % trigger.sender)
        else:
            bot.reply('Got it. %s is now flagged as spoilers-allowed.' % trigger.sender)


@commands('getspoilerfree', 'getspoilfree')
@example('.getspoilfree [channel]')
def get_channel_spoiler_free(bot, trigger):
    """
    Gets the channel's Spoiler-Free status, or the current channel's
    status if no channel given.
    """
    channel = trigger.group(2)
    if not channel:
        channel = trigger.sender
        if channel.is_nick():
            return bot.say('{}getspoilfree with no channel param is only permitted '
                           'in channels'.format(bot.config.core.help_prefix))

    channel = channel.strip()

    spoiler_free = bot.db.get_channel_value(channel, 'spoiler_free')
    if spoiler_free:
        bot.say('%s is flagged as spoiler-free' % channel)
    else:
        bot.say('%s is flagged as spoilers-allowed' % channel)
