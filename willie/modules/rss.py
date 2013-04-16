# -*- coding: utf-8 -*-
"""
rss.py - Willie RSS Module
Copyright 2012, Michael Yanovich, yanovich.net
Licensed under the Eiffel Forum License 2.

http://willie.dfbta.net
"""

import feedparser
import socket
import sys
import time

DEBUG = False
socket.setdefaulttimeout(10) # seconds before giving up on the feed until next cycle
INTERVAL = 10                # seconds between checking for new updates
STOP = False
SUB = ('%s',)

def checkdb(cursor):
    cursor.execute("CREATE TABLE IF NOT EXISTS rss ( channel text, site_title text, site_url text, fg text, bg text)")

def setup(willie):
    global SUB
    SUB = (willie.db.substitution,)

def manage_rss(willie, trigger):
    """ .rss [list|add|edit|del|start] <#channel> <title> <url> - no arguments needed with list or start, no url needed with delete (title optional). """
    if not trigger.admin:
        willie.reply("Sorry, you need to be an admin to modify or start the RSS feed.")
        return
    text = trigger.group().split()
    if text[1] == 'start':
        global first_run, restarted, DEBUG, INTERVAL, STOP
        DEBUG = False
        query = trigger.group(3)
        if query == '-v':
            DEBUG = True
            STOP = False
            willie.reply("Debugging enabled.")
        elif query == '-q':
            DEBUG = False
            STOP = False
            willie.reply("Debugging disabled.")
        elif query == '-i':
            INTERVAL = trigger.group(4)
            willie.reply("INTERVAL updated to: %s" % (str(INTERVAL)))
        elif query == '--stop':
            STOP = True
            willie.reply("Stop parameter updated.")
        if first_run:
            if DEBUG:
                willie.say("Okay, I'll start rss fetching...")
            first_run = False
        else:
            restarted = True
            if DEBUG:
                willie.say("Okay, I'll re-start rss...")
        if not STOP:
            while True:
                if STOP:
                    willie.reply("STOPPED")
                    first_run = False
                    STOP = False
                    break
                if DEBUG:
                    willie.say("Rechecking feeds")
                read_feeds(willie)
                time.sleep(INTERVAL)
        if DEBUG:
            willie.say("Stopped checking")
    else:
        conn = willie.db.connect()
        c = conn.cursor()
        checkdb(c)
        conn.commit()
        if len(text) < 2:
            willie.reply("Proper usage: '.rss add #channel title url', '.rss del #channel title', '.rss del #channel'")
        elif len(text) > 2:
            channel = "#"+text[2].lower()
        if len(text) > 4 and text[1] == 'add':
            fg_colour = str()
            bg_colour = str()
            temp = trigger.group().split('"')
            if len(temp) == 1:
                site_title = text[3]
                site_url = text[4]
                if len(text) >= 6:
                    fg_colour = str(text[5])
                if len(text) == 7:
                    bg_colour = str(text[6])
            elif temp[-1].split():
                site_title = temp[1]
                ending = temp[-1].split()
                site_url = ending[0]
                if len(ending) >= 2:
                    fg_colour = ending[1]
                if len(ending) == 3:
                    bg_colour = ending[2]
            else:
                willie.reply("Not enough parameters specified.")
                return
            if fg_colour:
                fg_colour = fg_colour.zfill(2)
            if bg_colour:
                bg_colour = bg_colour.zfill(2)
            args = tuple([channel, site_title, site_url, fg_colour, bg_colour])
            c.execute('INSERT INTO rss VALUES ("%s","%s","%s","%s","%s")' % args)
            conn.commit()
            c.close()
            willie.reply("Successfully added values to database.")
        elif len(text) == 3 and text[1] == 'del':
            args = tuple([channel])
            c.execute('DELETE FROM rss WHERE channel = "%s"' % args)
            conn.commit()
            c.close()
            willie.reply("Successfully removed values from database.")
        elif len(text) >= 4 and text[1] == 'del':
            args = tuple([channel, " ".join(text[3:])])
            c.execute('DELETE FROM rss WHERE channel = "%s" and site_title = "%s"' % args)
            conn.commit()
            c.close()
            willie.reply("Successfully removed the site from the given channel.")
        elif len(text) == 2 and text[1] == 'list':
            c.execute("SELECT * FROM rss")
            k = 0
            for row in c:
                k += 1
                willie.say("list: " + unicode(row))
            if k == 0:
                willie.reply("No entries in database")
        else:
            willie.reply("Incorrect parameters specified.")
        conn.close()
manage_rss.commands = ['rss']
manage_rss.priority = 'low'

class Feed(object):
    modified = ''

first_run = True
restarted = False
feeds = dict()

def read_feeds(willie):
    global restarted
    global STOP
    restarted = False
    conn = willie.db.connect()
    cur = conn.cursor()
    checkdb(cur)
    cur.execute("SELECT * FROM rss")
    if not cur.fetchall():
        STOP = True
        willie.say("No RSS feeds found in database. Please add some rss feeds.")

    cur.execute("CREATE TABLE IF NOT EXISTS recent ( channel text, site_title text, article_title text, article_url text )")
    cur.execute("SELECT * FROM rss")
    for row in cur:
        feed_channel = row[0]
        feed_site_title = row[1]
        feed_url = row[2]
        feed_fg = row[3]
        feed_bg = row[4]
        try:
            fp = feedparser.parse(feed_url)
        except IOError, E:
            willie.say("Can't parse, " + str(E))
        entry = fp.entries[0]
        if not feed_fg and not feed_bg:
            site_title_effect = "[\x02%s\x02]" % (feed_site_title)
        elif feed_fg and not feed_bg:
            site_title_effect = "[\x02\x03%s%s\x03\x02]" % (feed_fg, feed_site_title)
        elif feed_fg and feed_bg:
            site_title_effect = "[\x02\x03%s,%s%s\x03\x02]" % (feed_fg, feed_bg, feed_site_title)

        if hasattr(entry, 'id'):
            article_url = entry.id
        elif hasattr(entry, 'feedburner_origlink'):
            article_url = entry.feedburner_origlink
        else:
            article_url = entry.links[0].href
        args = tuple([feed_channel, feed_site_title, entry.title, article_url])
        cur.execute('SELECT * FROM recent WHERE channel = "%s" AND site_title = "%s" and article_title = "%s" AND article_url = "%s"' % args)
        if len(cur.fetchall()) < 1:

            response = site_title_effect + " %s \x02%s\x02" % (entry.title, article_url)
            if entry.updated:
                response += " - %s" % (entry.updated)

            willie.msg(feed_channel, response)

            args = tuple([feed_channel, feed_site_title, entry.title, article_url])
            cur.execute('INSERT INTO recent VALUES ("%s", "%s", "%s", "%s")' % args)
            conn.commit()
        else:
            if DEBUG:
                willie.msg(feed_channel, u"Skipping previously read entry: %s %s" % (site_title_effect, entry.title))
    conn.close()

if __name__ == '__main__':
    print __doc__.strip()
