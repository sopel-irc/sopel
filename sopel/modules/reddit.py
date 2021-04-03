# coding=utf-8
"""
reddit.py - Sopel Reddit Plugin
Copyright 2012, Elsie Powell, embolalia.com
Copyright 2019, dgw, technobabbl.es
Copyright 2019, deathbybandaid, deathbybandaid.net
Licensed under the Eiffel Forum License 2.

https://sopel.chat
"""
from __future__ import absolute_import, division, print_function, unicode_literals

import datetime as dt
import re
import sys

import praw
import prawcore
import requests

from sopel import plugin
from sopel.formatting import bold, color, colors
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

PLUGIN_OUTPUT_PREFIX = '[reddit] '

domain = r'https?://(?:www\.|old\.|pay\.|ssl\.|[a-z]{2}\.)?reddit\.com'
subreddit_url = r'%s/r/([\w-]+)/?$' % domain
post_url = r'%s/r/\S+?/comments/([\w-]+)(?:/[\w%%]+)?/?$' % domain
short_post_url = r'https?://redd\.it/([\w-]+)'
user_url = r'%s/u(?:ser)?/([\w-]+)' % domain
comment_url = r'%s/r/\S+?/comments/\S+?/\S+?/([\w-]+)' % domain
image_url = r'https?://i\.redd\.it/\S+'
video_url = r'https?://v\.redd\.it/([\w-]+)'
gallery_url = r'https?://(?:www\.)?reddit\.com/gallery/([\w-]+)'


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


def get_time_created(bot, trigger, entrytime):
    tz = time.get_timezone(
        bot.db, bot.config, None, trigger.nick, trigger.sender)
    time_created = dt.datetime.utcfromtimestamp(entrytime)
    created = time.format_time(bot.db,
                               bot.config, tz,
                               trigger.nick, trigger.sender,
                               time_created)
    return created


def get_is_cakeday(entrytime):
    now = dt.datetime.utcnow()
    cakeday_start = dt.datetime.utcfromtimestamp(entrytime)
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
    return is_cakeday


@plugin.url(image_url)
@plugin.output_prefix(PLUGIN_OUTPUT_PREFIX)
def image_info(bot, trigger, match):
    url = match.group(0)
    results = list(
        bot.memory['reddit_praw']
        .subreddit('all')
        .search('url:{}'.format(url), sort='new', params={'include_over_18': 'on'})
    )
    try:
        oldest = results[-1]
    except IndexError:
        # Fail silently if the image link can't be mapped to a submission
        return plugin.NOLIMIT
    return say_post_info(bot, trigger, oldest.id, False, True)


@plugin.url(video_url)
@plugin.output_prefix(PLUGIN_OUTPUT_PREFIX)
def video_info(bot, trigger, match):
    # Get the video URL with a cheeky hack
    url = requests.head(
        'https://www.reddit.com/video/{}'.format(match.group(1)),
        timeout=(10.0, 4.0)).headers['Location']
    try:
        return say_post_info(
            bot, trigger, re.match(post_url, url).group(1), False, True)
    except AttributeError:
        # Fail silently if we can't map the video link to a submission
        return plugin.NOLIMIT


@plugin.url(post_url)
@plugin.url(short_post_url)
@plugin.output_prefix(PLUGIN_OUTPUT_PREFIX)
def rpost_info(bot, trigger, match):
    match = match or trigger
    return say_post_info(bot, trigger, match.group(1))


@plugin.url(gallery_url)
@plugin.output_prefix(PLUGIN_OUTPUT_PREFIX)
def rgallery_info(bot, trigger, match):
    match = match or trigger
    return say_post_info(bot, trigger, match.group(1), False)


def say_post_info(bot, trigger, id_, show_link=True, show_comments_link=False):
    try:
        s = bot.memory['reddit_praw'].submission(id=id_)

        message = (
            '{title} {link}{nsfw} | {points} {points_text} ({percent}) | '
            '{comments} {comments_text} | Posted by {author} | '
            'Created at {created}{comments_link}')

        subreddit = s.subreddit.display_name
        if not show_link:
            link = 'to r/{}'.format(subreddit)
        elif s.is_self:
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

        created = get_time_created(bot, trigger, s.created_utc)

        if s.score > 0:
            point_color = colors.GREEN
        else:
            point_color = colors.RED

        points_text = 'point' if s.score == 1 else 'points'

        percent = color('{:.1%}'.format(s.upvote_ratio), point_color)

        comments_text = 'comment' if s.num_comments == 1 else 'comments'

        comments_link = ''
        if show_comments_link:
            try:
                comments_link = ' | ' + s.shortlink
            except AttributeError:
                # the value assigned earlier will be used
                pass

        title = unescape(s.title)
        message = message.format(
            title=title, link=link, nsfw=nsfw, points=s.score, points_text=points_text,
            percent=percent, comments=s.num_comments, comments_text=comments_text,
            author=author, created=created, comments_link=comments_link)

        bot.say(message)
    except prawcore.exceptions.NotFound:
        bot.reply('No such post.')
        return plugin.NOLIMIT


@plugin.url(comment_url)
@plugin.output_prefix(PLUGIN_OUTPUT_PREFIX)
def comment_info(bot, trigger, match):
    """Shows information about the linked comment"""
    try:
        c = bot.memory['reddit_praw'].comment(match.group(1))
    except prawcore.exceptions.NotFound:
        bot.reply('No such comment.')
        return plugin.NOLIMIT

    message = ('Comment by {author} | {points} {points_text} | '
               'Posted at {posted} | {comment}')

    if c.author:
        author = c.author.name
    else:
        author = '[deleted]'

    points_text = 'point' if c.score == 1 else 'points'

    posted = get_time_created(bot, trigger, c.created_utc)

    # stolen from the function I (dgw) wrote for our github plugin
    lines = [line for line in c.body.splitlines() if line and line[0] != '>']

    message = message.format(
        author=author, points=c.score, points_text=points_text,
        posted=posted, comment=' '.join(lines))

    bot.say(message, truncation=' […]')


def subreddit_info(bot, trigger, match, commanded=False):
    """Shows information about the given subreddit"""
    match_lower = match.lower()
    if match_lower in ['all', 'popular']:
        message = '{link}{nsfw} | {public_description}'
        nsfw = ' ' + bold(color('[Possible NSFW]', colors.ORANGE))
        link = "https://reddit.com/r/" + match_lower
        public_description = ''
        if match_lower == 'all':
            public_description = ('Today\'s top content from hundreds of '
                                  'thousands of Reddit communities.')
        elif match_lower == 'popular':
            public_description = ('The top trending content from some of '
                                  'Reddit\'s most popular communities')
        message = message.format(
            link=link, nsfw=nsfw, public_description=public_description)
        bot.say(message)
        return plugin.NOLIMIT

    r = bot.memory['reddit_praw']
    try:
        r.subreddits.search_by_name(match, exact=True)
    except prawcore.exceptions.NotFound:
        if commanded:
            bot.reply('No such subreddit.')
        # Fail silently if it wasn't an explicit command.
        return plugin.NOLIMIT

    try:
        s = r.subreddit(match)
        s.subreddit_type
    except prawcore.exceptions.Forbidden:
        bot.reply("r/" + match + " appears to be a private subreddit!")
        return plugin.NOLIMIT
    except prawcore.exceptions.NotFound:
        bot.reply("r/" + match + " appears to be a banned subreddit!")
        return plugin.NOLIMIT

    link = "https://reddit.com/r/" + s.display_name

    created = get_time_created(bot, trigger, s.created_utc)

    message = ('{link}{nsfw} | {subscribers} subscribers | '
               'Created at {created} | {public_description}')

    nsfw = ''
    if s.over18:
        nsfw += ' ' + bold(color('[NSFW]', colors.RED))

        sfw = bot.db.get_channel_value(trigger.sender, 'sfw')
        if sfw:
            link = '(link hidden)'
            bot.kick(
                trigger.nick, trigger.sender,
                'Linking to NSFW content in a SFW channel.'
            )

    message = message.format(
        link=link, nsfw=nsfw, subscribers='{:,}'.format(s.subscribers),
        created=created, public_description=s.public_description)

    bot.say(message, truncation=' […]')


def redditor_info(bot, trigger, match, commanded=False):
    """Shows information about the given Redditor"""
    try:
        u = bot.memory['reddit_praw'].redditor(match)
        u.id  # shortcut to check if the user exists or not
    except prawcore.exceptions.NotFound:
        if commanded:
            bot.reply('No such Redditor.')
        # Fail silently if it wasn't an explicit command.
        return plugin.NOLIMIT

    message = u.name
    is_cakeday = get_is_cakeday(u.created_utc)

    if is_cakeday:
        message = message + ' | ' + bold(color('Cake day', colors.LIGHT_PURPLE))
    if commanded:
        message = message + ' | https://reddit.com/u/' + u.name
    if u.is_gold:
        message = message + ' | ' + bold(color('Gold', colors.YELLOW))
    if u.is_employee:
        message = message + ' | ' + bold(color('Employee', colors.RED))
    if u.is_mod:
        message = message + ' | ' + bold(color('Mod', colors.GREEN))
    message = message + (' | Link: ' + str(u.link_karma) +
                         ' | Comment: ' + str(u.comment_karma))

    bot.say(message)


@plugin.url(user_url)
@plugin.output_prefix(PLUGIN_OUTPUT_PREFIX)
def auto_redditor_info(bot, trigger, match):
    return redditor_info(bot, trigger, match.group(1))


@plugin.url(subreddit_url)
@plugin.output_prefix(PLUGIN_OUTPUT_PREFIX)
def auto_subreddit_info(bot, trigger, match):
    return subreddit_info(bot, trigger, match.group(1))


@plugin.require_chanmsg('Setting SFW status is only supported in a channel.')
@plugin.require_privilege(plugin.OP)
@plugin.command('setsafeforwork', 'setsfw')
@plugin.example('.setsfw true')
@plugin.example('.setsfw false')
@plugin.output_prefix(PLUGIN_OUTPUT_PREFIX)
def set_channel_sfw(bot, trigger):
    """
    Sets the Safe for Work status (true or false) for the current
    channel. Defaults to false.
    """
    param = 'true'
    if trigger.group(2) and trigger.group(3):
        param = trigger.group(3).strip().lower()
    sfw = param == 'true'
    bot.db.set_channel_value(trigger.sender, 'sfw', sfw)
    if sfw:
        bot.say('%s is now flagged as SFW.' % trigger.sender)
    else:
        bot.say('%s is now flagged as NSFW.' % trigger.sender)


@plugin.command('getsafeforwork', 'getsfw')
@plugin.example('.getsfw [channel]')
@plugin.output_prefix(PLUGIN_OUTPUT_PREFIX)
def get_channel_sfw(bot, trigger):
    """
    Gets the preferred channel's Safe for Work status, or the current
    channel's status if no channel given.
    """
    channel = trigger.group(2)
    if not channel:
        channel = trigger.sender
        if channel.is_nick():
            bot.reply('{}getsfw with no channel param is only permitted in '
                      'channels.'.format(bot.config.core.help_prefix))
            return

    channel = channel.strip()

    sfw = bot.db.get_channel_value(channel, 'sfw')
    if sfw:
        bot.say('%s is flagged as SFW' % channel)
    else:
        bot.say('%s is flagged as NSFW' % channel)


@plugin.require_chanmsg('Only channels can be marked as spoiler-free.')
@plugin.require_privilege(plugin.OP)
@plugin.command('setspoilerfree', 'setspoilfree')
@plugin.example('.setspoilfree true')
@plugin.example('.setspoilfree false')
@plugin.output_prefix(PLUGIN_OUTPUT_PREFIX)
def set_channel_spoiler_free(bot, trigger):
    """
    Sets the Spoiler-Free status (true or false) for the current channel.
    Defaults to false.
    """
    param = 'true'
    if trigger.group(2) and trigger.group(3):
        param = trigger.group(3).strip().lower()
    spoiler_free = param == 'true'
    bot.db.set_channel_value(trigger.sender, 'spoiler_free', spoiler_free)
    if spoiler_free:
        bot.say('%s is now flagged as spoiler-free.' % trigger.sender)
    else:
        bot.say('%s is now flagged as spoilers-allowed.' % trigger.sender)


@plugin.command('getspoilerfree', 'getspoilfree')
@plugin.example('.getspoilfree [channel]')
@plugin.output_prefix(PLUGIN_OUTPUT_PREFIX)
def get_channel_spoiler_free(bot, trigger):
    """
    Gets the channel's Spoiler-Free status, or the current channel's
    status if no channel given.
    """
    channel = trigger.group(2)
    if not channel:
        channel = trigger.sender
        if channel.is_nick():
            bot.reply('{}getspoilfree with no channel param is only permitted '
                      'in channels.'.format(bot.config.core.help_prefix))
            return

    channel = channel.strip()

    spoiler_free = bot.db.get_channel_value(channel, 'spoiler_free')
    if spoiler_free:
        bot.say('%s is flagged as spoiler-free' % channel)
    else:
        bot.say('%s is flagged as spoilers-allowed' % channel)


@plugin.find(r'(?<!\S)/?(?P<prefix>r|u)/(?P<id>[a-zA-Z0-9-_]+)\b')
@plugin.output_prefix(PLUGIN_OUTPUT_PREFIX)
def reddit_slash_info(bot, trigger):
    searchtype = trigger.group('prefix').lower()
    match = trigger.group('id')
    if searchtype == "r":
        return subreddit_info(bot, trigger, match, commanded=False)
    elif searchtype == "u":
        return redditor_info(bot, trigger, match, commanded=False)


@plugin.command('subreddit')
@plugin.example('.subreddit plex')
@plugin.output_prefix(PLUGIN_OUTPUT_PREFIX)
def subreddit_command(bot, trigger):
    # require input
    if not trigger.group(2):
        bot.reply('You must provide a subreddit name.')
        return

    # subreddit names do not contain spaces
    match = trigger.group(3)
    return subreddit_info(bot, trigger, match, commanded=True)


@plugin.command('redditor')
@plugin.example('.redditor poem_for_your_sprog')
@plugin.output_prefix(PLUGIN_OUTPUT_PREFIX)
def redditor_command(bot, trigger):
    # require input
    if not trigger.group(2):
        bot.reply('You must provide a Redditor name.')
        return

    # Redditor names do not contain spaces
    match = trigger.group(3)
    return redditor_info(bot, trigger, match, commanded=True)
