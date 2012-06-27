#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
rss.py - Jenni RSS Module
Copyright 2012, Michael Yanovich, yanovich.net
Licensed under the Eiffel Forum License 2.

More info:
 * Jenni: https://github.com/myano/jenni/
 * Phenny: http://inamidst.com/phenny/
"""

import feedparser
import socket
import sqlite3
import sys
import time
from modules import url as url_module

DEBUG = False
socket.setdefaulttimeout(10)
INTERVAL = 10  # seconds between checking for new updates
STOP = False


def checkdb(cursor):
    cursor.execute("CREATE TABLE IF NOT EXISTS rss ( channel text, site_name text, site_url text, fg text, bg text)")


def manage_rss(jenni, input):
    """ .rss operation channel site_name url -- operation can be either 'add', 'del', or 'list' no further operators needed if 'list' used """
    if not input.admin:
        jenni.reply("Sorry, you need to be an admin to modify the RSS feeds.")
        return
    conn = sqlite3.connect('rss.db')
    c = conn.cursor()
    checkdb(c)
    conn.commit()

    text = input.group().split()
    if len(text) < 2:
        jenni.reply("Proper usage: '.rss add ##channel Site_Name URL', '.rss del ##channel Site_Name URL', '.rss del ##channel'")
    elif len(text) > 2:
        channel = text[2].lower()

    if len(text) > 4 and text[1] == 'add':
        fg_colour = str()
        bg_colour = str()
        temp = input.group().split('"')
        if len(temp) == 1:
            site_name = text[3]
            site_url = text[4]
            if len(text) >= 6:
                # .rss add ##yano ScienceDaily http://sciencedaily.com/ 03
                fg_colour = str(text[5])
            if len(text) == 7:
                # .rss add ##yano ScienceDaily http://sciencedaily.com/ 03 00
                bg_colour = str(text[6])
        elif temp[-1].split():
            site_name = temp[1]
            ending = temp[-1].split()
            site_url = ending[0]
            if len(ending) >= 2:
                fg_colour = ending[1]
            if len(ending) == 3:
                bg_colour = ending[2]
        else:
            jenni.reply("Not enough parameters specified.")
            return
        if fg_colour:
            fg_colour = fg_colour.zfill(2)
        if bg_colour:
            bg_colour = bg_colour.zfill(2)
        c.execute("INSERT INTO rss VALUES (?,?,?,?,?)", (channel, site_name,
            site_url, fg_colour, bg_colour))
        conn.commit()
        c.close()
        jenni.reply("Successfully added values to database.")
    elif len(text) == 3 and text[1] == 'del':
        # .rss del ##channel
        c.execute("DELETE FROM rss WHERE channel = ?", (channel,))
        conn.commit()
        c.close()
        jenni.reply("Successfully removed values from database.")
    elif len(text) >= 4 and text[1] == 'del':
        # .rss del ##channel Site_Name
        c.execute("DELETE FROM rss WHERE channel = ? and site_name = ?", (channel, " ".join(text[3:]),))
        conn.commit()
        c.close()
        jenni.reply("Successfully removed the site from the given channel.")
    elif len(text) == 2 and text[1] == 'list':
        c.execute("SELECT * FROM rss")
        k = 0
        for row in c:
            k += 1
            jenni.say("list: " + unicode(row))
        if k == 0:
            jenni.reply("No entries in database")
    else:
        jenni.reply("Incorrect parameters specified.")
    c.close()
manage_rss.commands = ['rss']
manage_rss.priority = 'low'


class Feed(object):
    modified = ''

first_run = True
restarted = False
feeds = dict()


def read_feeds(jenni):
    global restarted
    global STOP

    restarted = False
    conn = sqlite3.connect('rss.db')
    c = conn.cursor()
    checkdb(c)
    c.execute("SELECT * FROM rss")
    if not c.fetchall():
        STOP = True
        jenni.say("No RSS feeds found in database. Please add some rss feeds.")

    c.execute("SELECT * FROM rss")
    conn_recent = sqlite3.connect('recent_rss.db')
    cursor_recent = conn_recent.cursor()
    cursor_recent.execute("CREATE TABLE IF NOT EXISTS recent ( channel text, site_name text, article_title text, article_url text )")


    for row in c:
        feed_channel = row[0]
        feed_site_name = row[1]
        feed_url = row[2]
        feed_fg = row[3]
        feed_bg = row[4]
        try:
            fp = feedparser.parse(feed_url)
        except IOError, E:
            jenni.say("Can't parse, " + str(E))
        entry = fp.entries[0]

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
        sql_text = (feed_channel, feed_site_name, entry.title, article_url)
        cursor_recent.execute("SELECT * FROM recent WHERE channel = ? AND site_name = ? and article_title = ? AND article_url = ?", sql_text)
        if len(cursor_recent.fetchall()) < 1:
            short_url = url_module.short(article_url)

            if short_url:
                short_url = short_url[0][1][:-1]
            else:
                short_url = article_url

            response = site_name_effect + " %s \x02%s\x02" % (entry.title, short_url)
            if entry.updated:
                response += " - %s" % (entry.updated)

            jenni.msg(feed_channel, response)

            t = (feed_channel, feed_site_name, entry.title, article_url,)
            cursor_recent.execute("INSERT INTO recent VALUES (?, ?, ?, ?)", t)
            conn_recent.commit()
            cursor_recent.close()
            conn.commit()
            c.close()
        else:
            if DEBUG:
                jenni.msg(feed_channel, u"Skipping previously read entry: %s %s" % (site_name_effect, entry.title))
    cursor_recent.close()
    c.close()


def startrss(jenni, input):
    """ Begin reading RSS feeds """
    if not input.admin:
        jenni.reply("You must be an admin to start up the RSS feeds.")
        return
    global first_run, restarted, DEBUG, INTERVAL, STOP
    DEBUG = False

    query = input.group(2)
    if query == '-v':
        DEBUG = True
        STOP = False
        jenni.reply("Debugging enabled.")
    elif query == '-q':
        DEBUG = False
        STOP = False
        jenni.reply("Debugging disabled.")
    elif query == '-i':
        INTERVAL = input.group(3)
        jenni.reply("INTERVAL updated to: %s" % (str(INTERVAL)))
    elif query == '--stop':
        STOP = True
        jenni.reply("Stop parameter updated.")

    if first_run:
        if DEBUG:
            jenni.say("Okay, I'll start rss fetching...")
        first_run = False
    else:
        restarted = True
        if DEBUG:
            jenni.say("Okay, I'll re-start rss...")

    if not STOP:
        while True:
            if STOP:
                jenni.reply("STOPPED")
                first_run = False
                STOP = False
                break
            if DEBUG:
                jenni.say("Rechecking feeds")
            read_feeds(jenni)
            time.sleep(INTERVAL)

    if DEBUG:
        jenni.say("Stopped checking")
startrss.commands = ['startrss']
startrss.priority = 'high'

if __name__ == '__main__':
    print __doc__.strip()
