#!/usr/bin/env python
"""
search.py - Jenni Web Search Module
Copyright 2008-9, Sean B. Palmer, inamidst.com
Licensed under the Eiffel Forum License 2.

http://inamidst.com/phenny/
"""

import re
import web

def search(query): 
    """Search using AjaxSearch, and return its JSON."""
    uri = 'http://ajax.googleapis.com/ajax/services/search/web'
    args = '?v=1.0&safe=off&q=' + web.urllib.quote(query.encode('utf-8'))
    bytes = web.get(uri + args)
    return web.json(bytes)

def result(query): 
    results = search(query)
    try: return results['responseData']['results'][0]['unescapedUrl']
    except IndexError: return None

def count(query): 
    results = search(query)
    if not results.has_key('responseData'): return '0'
    if not results['responseData'].has_key('cursor'): return '0'
    if not results['responseData']['cursor'].has_key('estimatedResultCount'): 
        return '0'
    return results['responseData']['cursor']['estimatedResultCount']

def formatnumber(n): 
    """Format a number with beautiful commas."""
    parts = list(str(n))
    for i in range((len(parts) - 3), 0, -3):
        parts.insert(i, ',')
    return ''.join(parts)

def g(jenni, input): 
    """Queries Google for the specified input."""
    query = input.group(2)
    if not query: 
        return jenni.reply('.g what?')
    uri = result(query)
    if uri: 
        jenni.reply(uri)
        if not hasattr(jenni.bot, 'last_seen_uri'):
            jenni.bot.last_seen_uri = {}
        jenni.bot.last_seen_uri[input.sender] = uri
    else: jenni.reply("No results found for '%s'." % query)
g.commands = ['g']
g.priority = 'high'
g.example = '.g swhack'

def gc(jenni, input): 
    """Returns the number of Google results for the specified input."""
    query = input.group(2)
    if not query: 
        return jenni.reply('.gc what?')
    num = formatnumber(count(query))
    jenni.say(query + ': ' + num)
gc.commands = ['gc']
gc.priority = 'high'
gc.example = '.gc extrapolate'

r_query = re.compile(
    r'\+?"[^"\\]*(?:\\.[^"\\]*)*"|\[[^]\\]*(?:\\.[^]\\]*)*\]|\S+'
)

def gcs(jenni, input): 
    queries = r_query.findall(input.group(2))
    if len(queries) > 6: 
        return jenni.reply('Sorry, can only compare up to six things.')

    results = []
    for i, query in enumerate(queries): 
        query = query.strip('[]')
        n = int((formatnumber(count(query)) or '0').replace(',', ''))
        results.append((n, query))
        if i >= 2: __import__('time').sleep(0.25)
        if i >= 4: __import__('time').sleep(0.25)

    results = [(term, n) for (n, term) in reversed(sorted(results))]
    reply = ', '.join('%s (%s)' % (t, formatnumber(n)) for (t, n) in results)
    jenni.say(reply)
gcs.commands = ['gcs', 'comp']

if __name__ == '__main__': 
    print __doc__.strip()
