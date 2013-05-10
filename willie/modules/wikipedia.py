"""
wikipedia.py - Willie Wikipedia Module
Copyright 2013 Edward Powell - embolalia.net
Licensed under the Eiffel Forum License 2.

http://willie.dftba.net
"""
import willie.web as web
import json
import re

REDIRECT = re.compile(r'^REDIRECT (.*)')

def mw_search(server, query, num):
    """
    Searches the specified MediaWiki server for the given query, and returns
    the specified number of results.
    """
    search_url = ('http://%s/w/api.php?format=json&action=query'
                  '&list=search&srlimit=%d&srprop=timestamp&srwhat=text'
                  '&srsearch=') % (server, num)
    search_url += web.quote(query.encode('utf-8'))
    query = json.loads(web.get(search_url))
    query = query['query']['search']
    return [r['title'] for r in query]


def mw_snippet(server, query):
    """
    Retrives a snippet of the specified length from the given page on the given
    server.
    """
    snippet_url = ('https://en.wikipedia.org/w/api.php?format=json'
                   '&action=query&prop=extracts&exintro&explaintext'
                   '&exchars=300&redirects&titles=')
    snippet_url += web.quote(query.encode('utf-8'))
    snippet = json.loads(web.get(snippet_url))
    snippet = snippet['query']['pages']

    # For some reason, the API gives the page *number* as the key, so we just
    # grab the first page number in the results.
    snippet = snippet[snippet.keys()[0]]

    return snippet['extract']


def wikipedia(willie, trigger):
    query = trigger.group(2)
    if not query:
        willie.reply('What do you want me to look up?')
        return willie.NOLIMIT
    server = 'en.wikipedia.org'
    query = mw_search(server, query, 1)
    if not query:
        willie.reply("I can't find any results for that.")
        return willie.NOLIMIT
    else:
        query = query[0]
    snippet = mw_snippet(server, query)

    query = query.replace(' ', '_')
    willie.say('"%s" - http://en.wikipedia.org/wiki/%s' % (snippet, query))
wikipedia.commands = ['w', 'wiki', 'wik']
wikipedia.example = '.w San Francisco'
