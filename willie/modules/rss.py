# -*- coding: utf-8 -*-
"""
rss.py - Willie RSS Module
Copyright 2012, Michael Yanovich, yanovich.net
Licensed under the Eiffel Forum License 2.

http://willie.dfbta.net
"""

from datetime import datetime
import time
import re
import socket

import feedparser

from willie.module import commands, interval, priority
from willie.config import ConfigurationError

socket.setdefaulttimeout(10)

INTERVAL = 60 * 5  # seconds between checking for new updates
DEBUG = False  # display debug messages

first_run = True
STOP = False

channels_with_feeds = []

# This is reset in setup().
SUB = '%s'


class RSSFeed:
    """Represent a single row in the feed table."""

    def __init__(self, row):
        """Initialize with values from the feed table."""
        columns = ('channel',
                   'name',
                   'url',
                   'fg',
                   'bg',
                   'enabled',
                   'title',
                   'link',
                   'published',
                   'etag',
                   'modified',
                   )
        for i, column in enumerate(columns):
            setattr(self, column, row[i])


def setup(bot):
    if not bot.db:
        raise ConfigurationError("Database not set up, or unavailable.")
    conn = bot.db.connect()
    c = conn.cursor()

    global SUB
    SUB = bot.db.substitution

    # if new table doesn't exist, create it and try importing from old tables
    # The rss_feeds table was added on 2013-07-17.
    try:
        c.execute('SELECT * FROM rss_feeds')
    except StandardError:
        create_table(bot, c)
        migrate_from_old_tables(c)

        # These tables are no longer used, but lets not delete them right away.
        # c.execute('DROP TABLE IF EXISTS rss')
        # c.execute('DROP TABLE IF EXISTS recent')
        conn.commit()

    # The modified column was added on 2013-07-21.
    try:
        c.execute('SELECT modified FROM rss_feeds')
    except StandardError:
        c.execute('ALTER TABLE rss_feeds ADD modified TEXT')
        conn.commit()

    conn.close()


def create_table(bot, c):
    # MySQL needs to only compare on the first n characters of a TEXT field
    # but SQLite won't accept the syntax needed to make it do it.
    if bot.db.type == 'mysql':
        primary_key = '(channel(254), feed_name(254))'
    else:
        primary_key = '(channel, feed_name)'

    c.execute('''CREATE TABLE IF NOT EXISTS rss_feeds (
        channel TEXT,
        feed_name TEXT,
        feed_url TEXT,
        fg TINYINT,
        bg TINYINT,
        enabled BOOL DEFAULT 1,
        article_title TEXT,
        article_url TEXT,
        published TEXT,
        etag TEXT,
        modified TEXT,
        PRIMARY KEY {0}
        )'''.format(primary_key))


def migrate_from_old_tables(c):
    try:
        c.execute('SELECT * FROM rss')
        oldfeeds = c.fetchall()
    except StandardError:
        oldfeeds = []

    for feed in oldfeeds:
        channel, site_name, site_url, fg, bg = feed

        # get recent article if possible
        try:
            c.execute('''
                SELECT article_title, article_url FROM recent
                WHERE channel = {0} AND site_name = {0}
                '''.format(SUB), (channel, site_name))
            article_title, article_url = c.fetchone()
        except (StandardError, TypeError):
            article_title = article_url = None

        # add feed to new table
        if article_url:
            c.execute('''
                INSERT INTO rss_feeds (channel, feed_name, feed_url, fg, bg, article_title, article_url)
                VALUES ({0}, {0}, {0}, {0}, {0}, {0}, {0})
                '''.format(SUB), (channel, site_name, site_url, fg, bg, article_title, article_url))
        else:
            c.execute('''
                INSERT INTO rss_feeds (channel, feed_name, feed_url, fg, bg)
                VALUES ({0}, {0}, {0}, {0}, {0})
                '''.format(SUB), (channel, site_name, site_url, fg, bg))


def colour_text(text, fg, bg=''):
    """Given some text and fore/back colours, return a coloured text string."""
    if not fg:
        return text
    else:
        colour = '{0},{1}'.format(fg, bg) if bg != '' else fg
        return "\x03{0}{1}\x03".format(colour, text)


@commands('rss')
@priority('low')
def manage_rss(bot, trigger):
    """Manage RSS feeds. Usage: .rss <add|del|toggle|list>  (Use .startrss to start fetching feeds.)"""
    if not trigger.admin:
        bot.reply("Sorry, you need to be an admin to modify the RSS feeds.")
        return

    text = trigger.group().split()
    if (len(text) < 2 or text[1] not in ('add', 'del', 'toggle', 'list')):
        bot.reply("Please specify an operation: add del toggle list")
        return

    conn = bot.db.connect()
    c = conn.cursor()

    if text[1] == 'add':
        # .rss add <#channel> <Feed_Name> <URL> [fg] [bg]
        pattern = r'''
            ^\.rss\s+add
            \s+([&#+!][^\s,]+)   # channel
            \s+("[^"]+"|\w+)     # name, which can contain anything but quotes if quoted
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

        c.execute('SELECT * FROM rss_feeds WHERE channel = {0} AND feed_name = {0}'.format(SUB),
                  (channel, feed_name))
        if not c.fetchone():
            c.execute('''
                INSERT INTO rss_feeds (channel, feed_name, feed_url, fg, bg)
                VALUES ({0}, {0}, {0}, {0}, {0})
                '''.format(SUB), (channel, feed_name, feed_url, fg, bg))
            bot.reply("Successfully added the feed to the channel.")
        else:
            c.execute('''
                UPDATE rss_feeds SET feed_url = {0}, fg = {0}, bg = {0}
                WHERE channel = {0} AND feed_name = {0}
                '''.format(SUB), (feed_url, fg, bg, channel, feed_name))
            bot.reply("Successfully modified the feed.")

        conn.commit()

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

        c.execute('DELETE FROM rss_feeds WHERE channel = {0}'.format(SUB), (match.group(1),))
        bot.reply("Successfully cleared all feeds from the given channel.")

        conn.commit()

    elif text[1] == 'del':
        # .rss del [#channel] [Feed_Name]
        pattern = r"""
            ^\.rss\s+del
            (?:\s+([&#+!][^\s,]+))? # channel (optional)
            (?:\s+("[^"]+"|\w+))? # name (optional)
            """
        match = re.match(pattern, trigger.group(), re.IGNORECASE | re.VERBOSE)
        if match is None or (not match.group(1) and not match.group(2)):
            bot.reply("Remove one or all feeds from one or all channels. Usage: .rss del [#channel] [Feed_Name]")
            return

        channel = match.group(1)
        feed_name = match.group(2).strip('"') if match.group(2) else None
        args = [arg for arg in (channel, feed_name) if arg]

        c.execute(('DELETE FROM rss_feeds WHERE '
                   + ('channel = {0} AND ' if channel else '')
                   + ('feed_name = {0}' if feed_name else '')
                   ).rstrip(' AND ').format(SUB), args)

        if c.rowcount:
            noun = 'feeds' if c.rowcount != 1 else 'feed'
            bot.reply("Successfully removed {0} {1}.".format(c.rowcount, noun))
        else:
            bot.reply("No feeds matched the command.")

        conn.commit()

    elif text[1] == 'toggle':
        # .rss toggle [#channel] [Feed_Name]
        pattern = r"""
            ^\.rss\s+toggle
            (?:\s+([&#+!][^\s,]+))? # channel (optional)
            (?:\s+("[^"]+"|\w+))? # name (optional)
            """
        match = re.match(pattern, trigger.group(), re.IGNORECASE | re.VERBOSE)
        if match is None or (not match.group(1) and not match.group(2)):
            bot.reply("Enable or disable a feed or feeds. Usage: .rss toggle [#channel] [Feed_Name]")
            return

        channel = match.group(1)
        feed_name = match.group(2).strip('"') if match.group(2) else None
        args = [arg for arg in (channel, feed_name) if arg]

        c.execute(('UPDATE rss_feeds SET enabled = 1 - enabled WHERE '
                   + ('channel = {0} AND ' if channel else '')
                   + ('feed_name = {0}' if feed_name else '')
                   ).rstrip(' AND ').format(SUB), args)

        if c.rowcount:
            noun = 'feeds' if c.rowcount != 1 else 'feed'
            bot.reply("Successfully toggled {0} {1}.".format(c.rowcount, noun))
        else:
            bot.reply("No feeds matched the command.")

        conn.commit()

    elif text[1] == 'list':
        # .rss list
        c.execute('SELECT * FROM rss_feeds')
        feeds = c.fetchall()

        if not feeds:
            bot.reply("No RSS feeds in the database.")
        else:
            noun = 'feeds' if len(feeds) != 1 else 'feed'
            bot.say("{0} RSS {1} in the database:".format(len(feeds), noun))
        for feed_row in feeds:
            feed = RSSFeed(feed_row)
            bot.say("{0} {1} {2}{3} {4} {5}".format(
                    feed.channel,
                    colour_text(feed.name, feed.fg, feed.bg),
                    feed.url,
                    " (disabled)" if not feed.enabled else '',
                    feed.fg, feed.bg))

    c.close()
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
    c.execute('SELECT * FROM rss_feeds')
    feeds = c.fetchall()

    if not feeds:
        return

    if DEBUG:
        noun = 'feeds' if len(feeds) != 1 else 'feed'
        bot.debug(__file__, "Checking {0} RSS {1}...".format(len(feeds), noun),
                  'always')

    for feed_row in feeds:
        feed = RSSFeed(feed_row)

        if not feed.enabled:
            continue

        try:
            fp = feedparser.parse(feed.url, etag=feed.etag, modified=feed.modified)
        except IOError, E:
            bot.debug(__file__, "Can't parse, " + str(E), 'always')

        if DEBUG:
            bot.msg(feed.channel, "{0}: status = {1}, version = {2}, items = {3}".format(
                feed.name, fp.status, fp.version, len(fp.entries)))

            # throw a debug message if feed is not well-formed XML
            if fp.bozo:
                bot.msg(feed.channel, 'Malformed feed: ' + fp.bozo_exception.getMessage())

        if fp.status == 301:  # MOVED_PERMANENTLY
            # Set the new location as the feed url.
            c.execute('''
                UPDATE rss_feeds SET feed_url = {0}
                WHERE channel = {0} AND feed_name = {0}
                '''.format(SUB), (fp.href, feed.channel, feed.name))
            conn.commit()
        elif fp.status == 410:  # GONE
            # Disable the feed.
            c.execute('''
                UPDATE rss_feeds SET enabled = {0}
                WHERE channel = {0} AND feed_name = {0}
                '''.format(SUB), (0, feed.channel, feed.name))
            conn.commit()

        if not fp.entries:
            continue
        entry = fp.entries[0]

        entry_dt = (datetime.fromtimestamp(time.mktime(entry.published_parsed))
                    if "published" in entry else None)

        feed_etag = fp.etag if hasattr(fp, 'etag') else None
        feed_modified = fp.modified if hasattr(fp, 'modified') else None

        # check if article is new, and skip otherwise
        if (feed.title == entry.title and feed.link == entry.link
            and feed.etag == feed_etag and feed.modified == feed_modified):
            if DEBUG:
                bot.msg(feed.channel, u"Skipping previously read entry: [{0}] {1}".format(feed.name, entry.title))
            continue

        c.execute('''
            UPDATE rss_feeds
            SET article_title = {0}, article_url = {0}, published = {0}, etag = {0}, modified = {0}
            WHERE channel = {0} AND feed_name = {0}
            '''.format(SUB), (entry.title, entry.link, entry_dt, feed_etag, feed_modified,
                              feed.channel, feed.name))
        conn.commit()

        if feed.published and entry_dt:
            published_dt = datetime.strptime(feed.published, "%Y-%m-%d %H:%M:%S")

            if published_dt >= entry_dt:
                # This will make more sense once iterating over the feed is
                # implemented. Once that happens, deleting or modifying the
                # latest item would result in the whole feed getting re-msg'd.
                # This will prevent that from happening.
                if DEBUG:
                    debug_msg = u"Skipping older entry: [{0}] {1}, because {2} >= {3}".format(
                        feed.name, entry.title, published_dt, entry_dt)
                    bot.msg(feed.channel, debug_msg)
                continue

        # print new entry
        message = u"[\x02{0}\x02] \x02{1}\x02 {2}".format(
            colour_text(feed.name, feed.fg, feed.bg), entry.title, entry.link)
        if entry.updated:
            message += " - " + entry.updated
        bot.msg(feed.channel, message)

    c.close()
    conn.close()
