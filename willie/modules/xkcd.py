# coding=utf8
"""
xkcd.py - XKCD Module
Copyright 2010, Michael Yanovich (yanovich.net), and Morgan Goose
Copyright 2012, Lior Ramati
Copyright 2013, Edward Powell (embolalia.com)
Licensed under the Eiffel Forum License 2.

http://willie.dftba.net
"""
from __future__ import unicode_literals

import json
import random
import re
from willie import web
from willie.modules.search import google_search
from willie.module import commands

ignored_sites = [
    # For google searching
    'almamater.xkcd.com',
    'blog.xkcd.com',
    'blag.xkcd.com',
    'forums.xkcd.com',
    'fora.xkcd.com',
    'forums3.xkcd.com',
    'store.xkcd.com',
    'wiki.xkcd.com',
    'what-if.xkcd.com',
]
sites_query = ' site:xkcd.com -site:' + ' -site:'.join(ignored_sites)


def get_info(number=None):
    if number:
        url = 'http://xkcd.com/{}/info.0.json'.format(number)
    else:
        url = 'http://xkcd.com/info.0.json'
    data = web.get(url)
    data = json.loads(data)
    data['url'] = 'http://xkcd.com/' + str(data['num'])
    return data


def google(query):
    url = google_search(query + sites_query)
    match = re.match('(?:https?://)?xkcd.com/(\d+)/?', url)
    if match:
        return match.group(1)


@commands('xkcd')
def xkcd(bot, trigger):
    """
    .xkcd - Finds an xkcd comic strip. Takes one of 3 inputs:
    If no input is provided it will return a random comic
    If numeric input is provided it will return that comic, or the nth-latest
    comic if the number is non-positive
    If non-numeric input is provided it will return the first google result for those keywords on the xkcd.com site
    """
    # get latest comic for rand function and numeric input
    latest = get_info()
    max_int = latest['num']

    # if no input is given (pre - lior's edits code)
    if not trigger.group(2):  # get rand comic
        random.seed()
        requested = get_info(random.randint(0, max_int + 1))
    else:
        query = trigger.group(2).strip()

        # Positive or 0; get given number or latest
        if query.isdigit():
            query = int(query)
            if query > max_int:
                bot.say(("Sorry, comic #{} hasn't been posted yet. "
                         "The last comic was #{}").format(query, max_int))
                return
            elif query == 0:
                requested = latest
            else:
                requested = get_info(query)
        # Negative: go back that many from current
        elif query[0] == '-' and query[1:].isdigit():
            query = int(query[1:])
            requested = get_info(max_int - query)
        # Non-number: google.
        else:
            if (query.lower() == "latest" or query.lower() == "newest"):
                requested = latest
            else:
                number = google(query)
                if not number:
                    bot.say('Could not find any comics for that query.')
                    return
                requested = get_info(number)

    message = '{} [{}]'.format(requested['url'], requested['title'])
    bot.say(message)
