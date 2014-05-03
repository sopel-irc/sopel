# coding=utf8
"""
search.py - Willie Web Search Module
Copyright 2008-9, Sean B. Palmer, inamidst.com
Copyright 2012, Edward Powell, embolalia.net
Licensed under the Eiffel Forum License 2.

http://willie.dftba.net
"""
from __future__ import unicode_literals

import re
from willie import web
from willie.module import commands, example
import json
import sys
import time


def google_ajax(query):
    """Search using AjaxSearch, and return its JSON."""
    uri = 'http://ajax.googleapis.com/ajax/services/search/web'
    args = '?v=1.0&safe=off&q=' + query
    bytes = web.get(uri + args)
    return json.loads(bytes)


def google_search(query):
    results = google_ajax(query)
    try:
        return results['responseData']['results'][0]['unescapedUrl']
    except IndexError:
        return None
    except TypeError:
        return False


def google_count(query):
    results = google_ajax(query)
    if not 'responseData' in results:
        return '0'
    if not 'cursor' in results['responseData']:
        return '0'
    if not 'estimatedResultCount' in results['responseData']['cursor']:
        return '0'
    return results['responseData']['cursor']['estimatedResultCount']


def formatnumber(n):
    """Format a number with beautiful commas."""
    parts = list(str(n))
    for i in range((len(parts) - 3), 0, -3):
        parts.insert(i, ',')
    return ''.join(parts)


@commands('g', 'google')
@example('.g swhack')
def g(bot, trigger):
    """Queries Google for the specified input."""
    query = trigger.group(2)
    if not query:
        return bot.reply('.g what?')
    uri = google_search(query)
    if uri:
        bot.reply(uri)
        bot.memory['last_seen_url'][trigger.sender] = uri
    elif uri is False:
        bot.reply("Problem getting data from Google.")
    else:
        bot.reply("No results found for '%s'." % query)


@commands('gc')
@example('.gc extrapolate')
def gc(bot, trigger):
    """Returns the number of Google results for the specified input."""
    query = trigger.group(2)
    if not query:
        return bot.reply('.gc what?')
    num = formatnumber(google_count(query))
    bot.say(query + ': ' + num)

r_query = re.compile(
    r'\+?"[^"\\]*(?:\\.[^"\\]*)*"|\[[^]\\]*(?:\\.[^]\\]*)*\]|\S+'
)


@commands('gcs', 'comp')
@example('.gcs foo bar')
def gcs(bot, trigger):
    """Compare the number of Google search results"""
    if not trigger.group(2):
        return bot.reply("Nothing to compare.")
    queries = r_query.findall(trigger.group(2))
    if len(queries) > 6:
        return bot.reply('Sorry, can only compare up to six things.')

    results = []
    for i, query in enumerate(queries):
        query = query.strip('[]')
        n = int((formatnumber(google_count(query)) or '0').replace(',', ''))
        results.append((n, query))
        if i >= 2:
            time.sleep(0.25)
        if i >= 4:
            time.sleep(0.25)

    results = [(term, n) for (n, term) in reversed(sorted(results))]
    reply = ', '.join('%s (%s)' % (t, formatnumber(n)) for (t, n) in results)
    bot.say(reply)

r_bing = re.compile(r'<h3><a href="([^"]+)"')


def bing_search(query, lang='en-GB'):
    base = 'http://www.bing.com/search?mkt=%s&q=' % lang
    bytes = web.get(base + query)
    m = r_bing.search(bytes)
    if m:
        return m.group(1)

r_duck = re.compile(r'nofollow" class="[^"]+" href="(.*?)">')


def duck_search(query):
    query = query.replace('!', '')
    uri = 'http://duckduckgo.com/html/?q=%s&kl=uk-en' % query
    bytes = web.get(uri)
    m = r_duck.search(bytes)
    if m:
        return web.decode(m.group(1))


def duck_api(query):
    if '!bang' in query.lower():
        return 'https://duckduckgo.com/bang.html'

    uri = 'http://api.duckduckgo.com/?q=%s&format=json&no_html=1&no_redirect=1' % query
    results = json.loads(web.get(uri))
    if results['Redirect']:
        return results['Redirect']
    else:
        return None


@commands('duck', 'ddg')
@example('.duck privacy or .duck !mcwiki obsidian')
def duck(bot, trigger):
    """Queries Duck Duck Go for the specified input."""
    query = trigger.group(2)
    if not query:
        return bot.reply('.ddg what?')

    #If the API gives us something, say it and stop
    result = duck_api(query)
    if result:
        bot.reply(result)
        return

    #Otherwise, look it up on the HTMl version
    uri = duck_search(query)

    if uri:
        bot.reply(uri)
        bot.memory['last_seen_url'][trigger.sender] = uri
    else:
        bot.reply("No results found for '%s'." % query)


@commands('search')
@example('.search nerdfighter')
def search(bot, trigger):
    """Searches Google, Bing, and Duck Duck Go."""
    if not trigger.group(2):
        return bot.reply('.search for what?')
    query = trigger.group(2)
    gu = google_search(query) or '-'
    bu = bing_search(query) or '-'
    du = duck_search(query) or '-'

    if (gu == bu) and (bu == du):
        result = '%s (g, b, d)' % gu
    elif (gu == bu):
        result = '%s (g, b), %s (d)' % (gu, du)
    elif (bu == du):
        result = '%s (b, d), %s (g)' % (bu, gu)
    elif (gu == du):
        result = '%s (g, d), %s (b)' % (gu, bu)
    else:
        if len(gu) > 250:
            gu = '(extremely long link)'
        if len(bu) > 150:
            bu = '(extremely long link)'
        if len(du) > 150:
            du = '(extremely long link)'
        result = '%s (g), %s (b), %s (d)' % (gu, bu, du)

    bot.reply(result)


@commands('suggest')
def suggest(bot, trigger):
    """Suggest terms starting with given input"""
    if not trigger.group(2):
        return bot.reply("No query term.")
    query = trigger.group(2)
    uri = 'http://websitedev.de/temp-bin/suggest.pl?q='
    answer = web.get(uri+query.replace('+', '%2B'))
    if answer:
        bot.say(answer)
    else:
        bot.reply('Sorry, no result.')
