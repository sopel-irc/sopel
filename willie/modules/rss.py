# -*- coding: utf-8 -*-
"""
rss.py - Willie RSS Module
Copyright 2012, Michael Yanovich, yanovich.net
Licensed under the Eiffel Forum License 2.

http://willie.dfbta.net
"""

from willie.module import commands, interval, priority
import feedparser
import socket

socket.setdefaulttimeout(10)

INTERVAL = 20 # seconds between checking for new updates
DEBUG = False # display debug messages

first_run = True
STOP = True

# This is reset in setup().
SUB = ('%s',)


def checkdb(cursor):
    cursor.execute("CREATE TABLE IF NOT EXISTS rss ( channel text, site_name text, site_url text, fg text, bg text)")


def setup(bot):
    global SUB
    SUB = (bot.db.substitution,)
    
    
def msg_all_channels(bot, msg):
    for channel in bot.channels:
        bot.msg(channel, msg)


@commands('rss')
@priority('low')
def manage_rss(bot, trigger):
    """ '.rss add #channel Feed_Name URL [fg] [bg]', '.rss del [#channel] Feed_Name', '.rss clear #channel, '.rss list'"""
    if not trigger.admin:
        bot.reply("Sorry, you need to be an admin to modify the RSS feeds.")
        return

    text = trigger.group().split()
    if (len(text) < 2 or
        text[1] not in ('add', 'del', 'clear', 'list') or
        (len(text) < 5 and text[1] == 'add') or
        (len(text) < 3 and text[1] in ('del', 'clear'))
        ):
        bot.reply("Proper usage: '.rss add #channel Feed_Name URL [fg] [bg]', '.rss del [#channel] Feed_Name', '.rss clear #channel', '.rss list'")
        return

    conn = bot.db.connect()
    c = conn.cursor()
    checkdb(c)
    conn.commit()
    
    if text[1] == 'add':
        # .rss add #channel Feed_Name URL fg bg
        channel = text[2]
        feed_name = text[3]
        feed_url = text[4]
        fg_colour = text[5].zfill(2) if len(text) >= 6 else '01'
        bg_colour = text[6].zfill(2) if len(text) >= 7 else '00'

        c.execute('INSERT INTO rss VALUES (%s,%s,%s,%s,%s)' % (SUB * 5),
                  (channel, feed_name, feed_url, fg_colour, bg_colour))
        conn.commit()
        c.close()
        bot.reply("Successfully added the feed to the channel.")
        
    elif text[1] == 'clear':
        # .rss clear #channel
        c.execute('DELETE FROM rss WHERE channel = %s' % SUB, (text[2],))
        conn.commit()
        c.close()
        bot.reply("Successfully cleared all feeds from the given channel.")
        
    elif text[1] == 'del':
        if len(text) > 3:
            # .rss del #channel Feed_Name
            c.execute('DELETE FROM rss WHERE channel = %s and site_name = %s' % (SUB * 2),
                      (text[2], text[3]))
            conn.commit()
            c.close()
            bot.reply("Successfully removed the feed from the given channel.")
        else:
            # .rss del Feed_Name
            c.execute('DELETE FROM rss WHERE site_name = %s' % SUB,
                      (text[2],))
            conn.commit()
            c.close()
            bot.reply("Successfully removed the feed from all channels.")
        
    elif text[1] == 'list':
        c.execute("SELECT * FROM rss")
        k = 0
        for row in c.fetchall():
            k += 1
            bot.say("{0} {1} ({2}) - {3} {4}".format(*row))
        if k == 0:
            bot.reply("No RSS feeds in database.")

    conn.close()


@interval(INTERVAL)
def read_feeds(bot):
    global STOP
    if STOP:
        return
    
    conn = bot.db.connect()
    c = conn.cursor()
    checkdb(c)
    c.execute("SELECT * FROM rss")
    feeds = c.fetchall()
    
    if not feeds:
        STOP = True
        msg_all_channels(bot, "No RSS feeds found in database; stopping.")
        return
    
    if DEBUG:
        s = 's' if len(feeds) != 1 else ''
        msg_all_channels(bot, "Checking {0} RSS feed{1}...".format(len(feeds), s))
    
    for feed in feeds:
        feed_channel = feed[0]
        feed_site_name = feed[1]
        feed_url = feed[2]
        feed_fg = feed[3]
        feed_bg = feed[4]
        try:
            fp = feedparser.parse(feed_url)
        except IOError, E:
            msg_all_channels(bot, "Can't parse, " + str(E))
        entry = fp.entries[0]
        
        if DEBUG:
            bot.msg(feed_channel, "Found an entry: " + entry.title)
        
        if not feed_fg and not feed_bg:
            site_name_effect = "[\x02%s\x02]" % (feed_site_name)
        elif feed_fg and not feed_bg:
            site_name_effect = "[\x02\x03%s%s\x03\x02]" % (feed_fg, feed_site_name)
        elif feed_fg and feed_bg:
            site_name_effect = "[\x02\x03%s,%s%s\x03\x02]" % (feed_fg, feed_bg, feed_site_name)

        if hasattr(entry, 'id'):
            article_url = entry.id
        elif hasattr(entry, 'feedburner_origlink'):
            article_url = entry.feedburner_origlink
        else:
            article_url = entry.links[0].href

        # only print if new entry
        c.execute("CREATE TABLE IF NOT EXISTS recent ( channel text, site_name text, article_title text, article_url text )")
        sql_text = (feed_channel, feed_site_name, entry.title, article_url)
        c.execute('SELECT * FROM recent WHERE channel = %s AND site_name = %s and article_title = %s AND article_url = %s' % (SUB * 4), sql_text)

        if not c.fetchall():
            response = site_name_effect + " %s \x02%s\x02" % (entry.title, article_url)
            if entry.updated:
                response += " - %s" % (entry.updated)

            bot.msg(feed_channel, response)

            t = (feed_channel, feed_site_name, entry.title, article_url,)
            c.execute('INSERT INTO recent VALUES (%s, %s, %s, %s)' % (SUB * 4), t)
            conn.commit()
        else:
            if DEBUG:
                bot.msg(feed_channel, u"Skipping previously read entry: %s %s" % (site_name_effect, entry.title))

    conn.close()


@commands('startrss')
@priority('high')
def startrss(bot, trigger):
    """Begin reading RSS feeds. [-v : Verbose | -q : Quiet | -i [seconds] : Set fetch interval | --stop : Stop fetching] """
    if not trigger.admin:
        bot.reply("You must be an admin to start up the RSS feeds.")
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
        bot.reply("Okay, I'll stop RSS fetching...")
    else:
        STOP = False
        bot.reply("Okay, I'll start RSS fetching..." if first_run else
                  "Okay, I'll restart RSS fetching...")
    first_run = False
        
        
