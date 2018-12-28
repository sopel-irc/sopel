# coding=utf-8
# Copyright 2010, Michael Yanovich (yanovich.net), and Morgan Goose
# Copyright 2012, Lior Ramati
# Copyright 2013, Elsie Powell (embolalia.com)
# Licensed under the Eiffel Forum License 2.
from __future__ import unicode_literals, absolute_import, print_function, division

import random
import re
import requests
from sopel.modules.search import bing_search
from sopel.module import commands, url

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


def get_info(number=None, verify_ssl=True):
    if number:
        url = 'https://xkcd.com/{}/info.0.json'.format(number)
    else:
        url = 'https://xkcd.com/info.0.json'
    data = requests.get(url, verify=verify_ssl).json()
    data['url'] = 'https://xkcd.com/' + str(data['num'])
    return data


def google(query):
    url = bing_search(query + sites_query)
    if not url:
        return None
    match = re.match(r'(?:https?://)?xkcd.com/(\d+)/?', url)
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
    verify_ssl = bot.config.core.verify_ssl
    # get latest comic for rand function and numeric input
    latest = get_info(verify_ssl=verify_ssl)
    max_int = latest['num']

    # if no input is given (pre - lior's edits code)
    if not trigger.group(2):  # get rand comic
        random.seed()
        requested = get_info(random.randint(1, max_int + 1),
                             verify_ssl=verify_ssl)
    else:
        query = trigger.group(2).strip()

        numbered = re.match(r"^(#|\+|-)?(\d+)$", query)
        if numbered:
            query = int(numbered.group(2))
            if numbered.group(1) == "-":
                query = -query
            return numbered_result(bot, query, latest)
        else:
            # Non-number: google.
            if (query.lower() == "latest" or query.lower() == "newest"):
                requested = latest
            else:
                number = google(query)
                if not number:
                    bot.say('Could not find any comics for that query.')
                    return
                requested = get_info(number, verify_ssl=verify_ssl)

    say_result(bot, requested)


def numbered_result(bot, query, latest, verify_ssl=True):
    max_int = latest['num']
    if query > max_int:
        bot.say(("Sorry, comic #{} hasn't been posted yet. "
                    "The last comic was #{}").format(query, max_int))
        return
    elif query <= -max_int:
        bot.say(("Sorry, but there were only {} comics "
                    "released yet so far").format(max_int))
        return
    elif abs(query) == 0:
        requested = latest
    elif query == 404 or max_int + query == 404:
        bot.say("404 - Not Found")  # don't error on that one
        return
    elif query > 0:
        requested = get_info(query, verify_ssl=verify_ssl)
    else:
        # Negative: go back that many from current
        requested = get_info(max_int + query, verify_ssl=verify_ssl)

    say_result(bot, requested)


def say_result(bot, result):
    message = '{} | {} | Alt-text: {}'.format(result['url'], result['title'],
                                              result['alt'])
    bot.say(message)


@url(r'xkcd.com/(\d+)')
def get_url(bot, trigger, match):
    verify_ssl = bot.config.core.verify_ssl
    latest = get_info(verify_ssl=verify_ssl)
    numbered_result(bot, int(match.group(1)), latest)
