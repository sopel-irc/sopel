# -*- coding: utf-8 -*-
"""
rss.py - Willie RSS Module
Copyright 2012, Michael Yanovich, yanovich.net
Licensed under the Eiffel Forum License 2.

http://willie.dfbta.net
"""

import feedparser
import mechanize
import socket
import sys
import time


def manage_rss(willie, trigger):
    """ .rss [list|add|del|start|stop|auth] <#channel> <title> <url> """
    if not trigger.admin:
        return
    DEBUG = False
    INTERVAL = 10
    STOP = False
    COOKIE = ''
    text = trigger.group().split()
    if DEBUG:
        willie.reply(unicode(text))
    conn = willie.db.connect()
    db = conn.cursor()
    db.execute('CREATE TABLE IF NOT EXISTS feeds(channel text,title text,url text)')
    db.execute('CREATE TABLE IF NOT EXISTS entries(channel text,url text)')
    conn.commit()
    if text[1] == 'list':
        feeds = 0
        query = 'SELECT * FROM feeds'
        if DEBUG:
            willie.reply(query)
        db.execute(query)
        for row in db:
            feeds += 1
            willie.reply('Feed: ' + unicode(row))
        if feeds == 0:
            willie.reply('No feeds in database.')
    elif text[1] == 'add':
        query = 'INSERT INTO feeds VALUES("%s","%s","%s")' % (text[2], text[3], text[4])
        if DEBUG:
            willie.reply(query)
        db.execute(query)
        conn.commit()
        willie.reply('Successfully added feed to database.')
    elif text[1] == 'del':
        if len(text) == 3:
            query = 'DELETE FROM feeds WHERE channel="%s"' % (text[2])
            if DEBUG:
                willie.reply(query)
            db.execute(query)
            conn.commit()
            willie.reply('Successfully removed channel from database.')
        elif len(text) > 3:
            query = 'DELETE FROM feeds WHERE channel="%s" and title="%s"' % (text[2], text[3])
            if DEBUG:
                willie.reply(query)
            db.execute(query)
            conn.commit()
            willie.reply('Successfully removed the feed from the given channel.')
    elif text[1] == 'start':
        willie.reply('Started.')
        while True:
            rows = 0
            if STOP:
                STOP = False
                break
            if DEBUG:
                willie.reply('Sync...')
            db.execute('SELECT * FROM feeds')
            for row in db:
                rows += 1
                feed = {
                'channel': row[0],
                'title': row[1],
                'url': row[2]
                }
                try:
                    fp = feedparser.parse(feed['url'])
                    #extra_headers={'Cookie': COOKIE}
                except IOError, E:
                    willie.reply('Invalid entry: ' + str(E))
                entry = fp.entries[0]
                if hasattr(entry, 'id'):
                    entry_url = entry.id
                else:
                    entry_url = entry.links[0].href
                db.execute('SELECT * FROM entries WHERE channel="%s" AND url="%s"' % (feed['channel'], entry_url))
                if len(db.fetchall()) < 1:
                    message = '[\x02%s\x02] %s \x02%s\x02' % (feed['title'], entry.title, entry_url)
                    willie.msg(feed['channel'], message)
                    if DEBUG:
                        willie.reply('New entry: ' + message)
                    db.execute('INSERT INTO entries VALUES("%s","%s")' % (feed['channel'], entry_url))
                    conn.commit()
                else:
                    if DEBUG:
                        willie.reply('Old entry: ' + message)
            if rows == 0:
                STOP = True
                willie.reply('No feeds in database.')
            if DEBUG:
                willie.reply('Done.')
            time.sleep(INTERVAL)
        if DEBUG:
            willie.reply('Stopped.')
    elif text[1] == 'stop':
        STOP = True
        willie.reply('Stopping...')
    elif text[1] == 'auth':
        response = mechanize.urlopen(mechanize.Request('http://alphachat.net/forums'))
        forms = mechanize.ParseResponse(response, backwards_compat=False)
        response.close()
        forms[0]['login'] = 'tckibot'
        forms[0]['password'] = '******'
        response2 = mechanize.urlopen(forms[0].click())
        for name, value in response2.info().items():
            if DEBUG:
                willie.reply('%s: %s' % (name.title(), value))
            if name.title() == 'Set-Cookie':
                COOKIE = value
        if COOKIE != '':
            willie.reply('Authenticated successfully.')
        else:
            willie.reply('Failed to authenticate.')
        response2.close()
    else:
        willie.reply('Incorrect parameters.')
    db.close()
    conn.close()
manage_rss.commands = ['rss']
manage_rss.priority = 'low'

if __name__ == '__main__':
    print __doc__.strip()
