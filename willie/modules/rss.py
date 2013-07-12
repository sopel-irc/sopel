# -*- coding: utf-8 -*-
"""
rss.py - Willie RSS Module
Copyright 2012, Michael Yanovich, yanovich.net
Licensed under the Eiffel Forum License 2.

http://willie.dfbta.net
"""

from willie.module import commands, interval, priority
import feedparser
import re
import socket


socket.setdefaulttimeout(10)

INTERVAL = 20 # seconds between checking for new updates
DEBUG = False # display debug messages

first_run = True
STOP = True

# This is reset in setup().
SUB = ('%s',)


def checkdb(cursor):
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS rss_feeds
        (channel text, feed_name text, feed_url text, fg tinyint, bg tinyint,
        article_title text, article_url text,
        PRIMARY KEY (channel, feed_name))
        ''')


def setup(bot):
    global SUB
    SUB = (bot.db.substitution,)
    
    
def msg_all_channels(bot, msg):
    for channel in bot.channels:
        bot.msg(channel, msg)
        
        
def colour_text(text, fg, bg):
    if not fg:
        return text
    else:
        colour = '{0},{1}'.format(fg, bg) if bg != '' else fg
        return "\x03{0}{1}\x03".format(colour, text)


@commands('rss')
@priority('low')
def manage_rss(bot, trigger):
    """Manage RSS feeds. Usage: .rss <add|del|clear|list>  (Use .startrss to start fetching feeds.)"""
    if not trigger.admin:
        bot.reply("Sorry, you need to be an admin to modify the RSS feeds.")
        return

    text = trigger.group().split()
    if (len(text) < 2 or text[1] not in ('add', 'del', 'clear', 'list')):
        bot.reply("Please specify an operation: add del clear list")
        return

    conn = bot.db.connect()
    c = conn.cursor()
    checkdb(c)
    conn.commit()
    
    if text[1] == 'add':
        # .rss add <#channel> <Feed_Name> <URL> [fg] [bg]
        pattern = r'''
            ^\.rss\s+add
            \s+([&#+!][^\s,]+)   # channel
            \s+("[^"]+"|[^"\s]+) # name, which can contain spaces if quoted
            \s+(\S+)             # url
            (?:\s+(\d+))?        # foreground colour (optional)
            (?:\s+(\d+))?        # background colour (optional)
            '''
        match = re.match(pattern, trigger.group(), re.IGNORECASE | re.VERBOSE)
        if match is None:
            bot.reply("Add a feed to a channel, or modify an existing one. Usage: .rss add <#channel> <Feed_Name> <URL> [fg] [bg]")
            return
        
        channel = match.group(1)
        feed_name = match.group(2).strip('"')
        feed_url = match.group(3)
        fg = int(match.group(4)) % 16 if match.group(4) else ''
        bg = int(match.group(5)) % 16 if match.group(5) else ''
        
        c.execute('SELECT * FROM rss_feeds WHERE channel = %s AND feed_name = %s' % (SUB * 2),
                  (channel, feed_name))
        if not c.fetchone():
            c.execute('''
                INSERT INTO rss_feeds (channel, feed_name, feed_url, fg, bg)
                VALUES (%s, %s, %s, %s, %s)
                ''' % (SUB * 5), (channel, feed_name, feed_url, fg, bg))
            bot.reply("Successfully added the feed to the channel.")
        else:
            c.execute('''
                UPDATE rss_feeds SET feed_url = %s, fg = %s, bg = %s
                WHERE channel = %s AND feed_name = %s
                ''' % (SUB * 5), (feed_url, fg, bg, channel, feed_name))
            bot.reply("Successfully modified the feed.")
        conn.commit()
        c.close()
        
    elif text[1] == 'clear':
        # .rss clear <#channel>
        pattern = r"""
            ^\.rss\s+clear
            \s+([&#+!][^\s,]+) # channel
            """
        match = re.match(pattern, trigger.group(), re.IGNORECASE | re.VERBOSE)
        if match is None:
            bot.reply("Clear all feeds from a channel. Usage: .rss clear <#channel>")
            return
        
        c.execute('DELETE FROM rss_feeds WHERE channel = %s' % SUB, (match.group(1),))
        conn.commit()
        c.close()
        bot.reply("Successfully cleared all feeds from the given channel.")
        
    elif text[1] == 'del':
        # .rss del [#channel] <Feed_Name>
        pattern = r"""
            ^\.rss\s+del
            (?:\s+([&#+!][^\s,]+))? # channel (optional)
            \s+("[^"]+"|[^"\s]+)    # name, which can contain spaces if quoted
            """
        match = re.match(pattern, trigger.group(), re.IGNORECASE | re.VERBOSE)
        if match is None:
            bot.reply("Remove a feed from one or all channels. Usage: .rss del [#channel] <Feed_Name>")
            return
        
        channel = match.group(1)
        feed_name = match.group(2).strip('"')
        
        if match.group(1):
            c.execute('DELETE FROM rss_feeds WHERE channel = %s AND feed_name = %s' % (SUB * 2),
                      (channel, feed_name))
            bot.reply("Successfully removed the feed from the given channel.")
        else:
            c.execute('DELETE FROM rss_feeds WHERE feed_name = %s' % SUB, (feed_name,))
            bot.reply("Successfully removed the feed from all channels.")
        conn.commit()
        c.close()
        
    elif text[1] == 'list':
        # .rss list
        c.execute('SELECT * FROM rss_feeds')
        feeds = c.fetchall()
        
        if not feeds:
            bot.reply("No RSS feeds in the database.")
        else:
            noun = 'feeds' if len(feeds) != 1 else 'feed'
            bot.say("{0} RSS {1} in the database:".format(len(feeds), noun))
        for feed in feeds:
            feed_channel, feed_name, feed_url, fg, bg = feed[:5]
            bot.say("{0} {1} {2} {3} {4}".format(
                feed_channel, colour_text(feed_name, fg, bg), feed_url, fg, bg))

    conn.close()


@commands('startrss')
@priority('high')
def startrss(bot, trigger):
    """Begin reading RSS feeds. Usage: .startrss [-v :Verbose | -q :Quiet | --stop :Stop fetching]"""
    if not trigger.admin:
        bot.reply("You must be an admin to start fetching RSS feeds.")
        return
    
    global first_run, DEBUG, STOP
    
    flag = trigger.group(3)
    if flag == '-v':
        DEBUG = True
        bot.reply("Debugging enabled.")
    elif flag == '-q':
        DEBUG = False
        bot.reply("Debugging disabled.")
    elif flag == '-i':
        # changing the interval doesn't currently seem to work
        try:
            read_feeds.interval = [int(trigger.group(4))]
            bot.reply("Interval updated to {0} seconds".format(trigger.group(4)))
        except ValueError:
            pass
        
    if flag == '--stop':
        STOP = True
        bot.reply("Okay, I'll stop fetching RSS feeds.")
    else:
        STOP = False
        bot.reply("Okay, I'll start fetching RSS feeds..." if first_run else
                  "Continuing to fetch RSS feeds...")
    first_run = False
        
        
@interval(INTERVAL)
def read_feeds(bot):
    global STOP
    if STOP:
        return
    
    conn = bot.db.connect()
    c = conn.cursor()
    checkdb(c)
    c.execute('SELECT * FROM rss_feeds')
    feeds = c.fetchall()
    
    if not feeds:
        STOP = True
        msg_all_channels(bot, "No RSS feeds found in database; stopping.")
        return
    
    if DEBUG:
        noun = 'feeds' if len(feeds) != 1 else 'feed'
        msg_all_channels(bot, "Checking {0} RSS {1}...".format(len(feeds), noun))
    
    for feed in feeds:
        feed_channel, feed_name, feed_url, fg, bg, article_title, article_url = feed

        try:
            fp = feedparser.parse(feed_url)
        except IOError, E:
            msg_all_channels(bot, "Can't parse, " + str(E))

        if DEBUG:
            noun = 'entries' if len(fp.entries) != 1 else 'entry'
            bot.msg(feed_channel, "Found {0} {1} for {2}".format(len(fp.entries), noun, feed_name))
        
        try:
            entry = fp.entries[0]
        except IndexError:
            continue

        # check if new entry
        if article_title == entry.title and article_url == entry.link:
            if DEBUG:
                bot.msg(feed_channel, u"Skipping previously read entry: [{0}] {1}".format(feed_name, entry.title))
            continue

        # print new entry
        message = u"[\x02{0}\x02] \x02{1}\x02 {2}".format(
            colour_text(feed_name, fg, bg), entry.title, entry.link)
        if entry.updated:
            message += " - " + entry.updated
        bot.msg(feed_channel, message)
        
        # save into recent
        c.execute('''
            UPDATE rss_feeds SET article_title = %s, article_url = %s
            WHERE channel = %s AND feed_name = %s
            ''' % (SUB * 4), (entry.title, entry.link, feed_channel, feed_name))
        conn.commit()

    conn.close()

