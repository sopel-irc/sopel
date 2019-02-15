# coding=utf-8
# Copyright 2008-9, Sean B. Palmer, inamidst.com
# Copyright 2012, Elsie Powell, embolalia.com
# Licensed under the Eiffel Forum License 2.
from __future__ import unicode_literals, absolute_import, print_function, division

import re
import sys

if sys.version_info.major < 3:
    from urllib import unquote as _unquote
    unquote = lambda s: _unquote(s.encode('utf-8')).decode('utf-8')
else:
    from urllib.parse import unquote

import requests
import xmltodict

from sopel import web
from sopel.module import commands, example


def formatnumber(n):
    """Format a number with beautiful commas."""
    parts = list(str(n))
    for i in range((len(parts) - 3), 0, -3):
        parts.insert(i, ',')
    return ''.join(parts)


r_bing = re.compile(r'<h2(?: class=" b_topTitle")?><a href="([^"]+)"')


def bing_search(query, lang='en-US'):
    base = 'https://www.bing.com/search'
    parameters = {
        'mkt': lang,
        'q': query,
    }
    response = requests.get(base, parameters)
    m = r_bing.search(response.text)
    if m:
        return m.group(1)


r_duck = re.compile(r'nofollow" class="[^"]+" href="(?!(?:https?:\/\/r\.search\.yahoo)|(?:https?:\/\/duckduckgo\.com\/y\.js)(?:\/l\/\?kh=-1&amp;uddg=))(.*?)">')


def duck_search(query):
    query = query.replace('!', '')
    base = 'https://duckduckgo.com/html/'
    parameters = {
        'kl': 'us-en',
        'q': query,
    }
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36'
    }
    bytes = requests.get(base, parameters, headers=headers).text
    if 'web-result' in bytes:  # filter out the adds on top of the page
        bytes = bytes.split('web-result')[1]
    m = r_duck.search(bytes)
    if m:
        unquoted_m = unquote(m.group(1))
        return web.decode(unquoted_m)


# Alias google_search to duck_search
google_search = duck_search


def duck_api(query):
    if '!bang' in query.lower():
        return 'https://duckduckgo.com/bang.html'

    base = 'https://api.duckduckgo.com/'
    parameters = {
        'format': 'json',
        'no_html': '1',
        'no_redirect': '1',
        'q': query,
    }
    try:
        results = requests.get(base, parameters).json()
    except ValueError:
        return None
    if results['Redirect']:
        return results['Redirect']
    else:
        return None


@commands('duck', 'ddg', 'g')
# test for bad Unicode handling in py2
@example('.duck grandorder.wiki chulainn alter', 'https://grandorder.wiki/Cú_Chulainn_(Alter)')
# the last example is what .help displays
@example('.duck sopel irc bot', r'https?:\/\/sopel\.chat\/?', re=True)
def duck(bot, trigger):
    """Queries Duck Duck Go for the specified input."""
    query = trigger.group(2)
    if not query:
        return bot.reply('.ddg what?')

    # If the API gives us something, say it and stop
    result = duck_api(query)
    if result:
        bot.reply(result)
        return

    # Otherwise, look it up on the HTMl version
    uri = duck_search(query)

    if uri:
        bot.reply(uri)
        if 'last_seen_url' in bot.memory:
            bot.memory['last_seen_url'][trigger.sender] = uri
    else:
        msg = "No results found for '%s'." % query
        if query.count('site:') >= 2:
            # This check exists because of issue #1415. The git.io link will take the user there.
            # (Better a sopel.chat link, but it's not set up to do that. This is shorter anyway.)
            msg += " Try again with at most one 'site:' operator. See https://git.io/fpKtP for why."
        bot.reply(msg)


@commands('bing')
@example('.bing sopel irc bot')
def bing(bot, trigger):
    """Queries Bing for the specified input."""
    if not trigger.group(2):
        return bot.reply('.bing what?')
    query = trigger.group(2)
    result = bing_search(query)
    if result:
        bot.say(result)
    else:
        bot.reply("No results found for '%s'." % query)


@commands('search')
@example('.search sopel irc bot')
def search(bot, trigger):
    """Searches Bing and Duck Duck Go."""
    if not trigger.group(2):
        return bot.reply('.search for what?')
    query = trigger.group(2)
    bu = bing_search(query) or '-'
    du = duck_search(query) or '-'

    if bu == du:
        result = '%s (b, d)' % bu
    else:
        if len(bu) > 150:
            bu = '(extremely long link)'
        if len(du) > 150:
            du = '(extremely long link)'
        result = '%s (b), %s (d)' % (bu, du)

    bot.reply(result)


@commands('suggest')
@example('.suggest wikip', 'wikipedia')
@example('.suggest ', 'No query term.')
@example('.suggest lkashdfiauwgeaef', 'Sorry, no result.')
def suggest(bot, trigger):
    """Suggest terms starting with given input"""
    if not trigger.group(2):
        return bot.reply("No query term.")
    query = trigger.group(2)
    # Using Google isn't necessarily ideal, but at most they'll be able to build
    # a composite profile of all users on a given instance, not a profile of any
    # single user. This can be switched out as soon as someone finds (or builds)
    # an alternative suggestion API.
    base = 'https://suggestqueries.google.com/complete/search'
    parameters = {
        'output': 'toolbar',
        'hl': 'en',
        'q': query,
    }
    response = requests.get(base, parameters)
    answer = xmltodict.parse(response.text)['toplevel']
    try:
        answer = answer['CompleteSuggestion'][0]['suggestion']['@data']
    except TypeError:
        answer = None
    if answer:
        bot.say(answer)
    else:
        bot.reply('Sorry, no result.')
