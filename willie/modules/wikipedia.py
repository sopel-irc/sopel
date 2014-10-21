# coding=utf8
"""
wikipedia.py - Willie Wikipedia Module
Copyright 2013 Edward Powell - embolalia.net
Licensed under the Eiffel Forum License 2.

http://willie.dftba.net
"""
from __future__ import unicode_literals
from willie import web
from willie.module import NOLIMIT, commands, example
import json
import re

REDIRECT = re.compile(r'^REDIRECT (.*)')


def configure(config):
    """
    |  [wikipedia]  | example | purpose |
    | ------------- | ------- | ------- |
    | default_lang  | en      | Set the Global default wikipedia lang |
    """
    if config.option('Configure wikipedia module', False):
        config.add_section('wikipedia')
        config.interactive_add('wikipedia', 'default_lang', 'Wikipedia default language', 'en')

        if config.option('Would you like to configure individual default language per channel', False):
            c = 'Enter #channel:lang, one at time. When done, hit enter again.'
            config.add_list('wikipedia', 'lang_per_channel', c, 'Channel:')


def mw_search(server, query, num):
    """
    Searches the specified MediaWiki server for the given query, and returns
    the specified number of results.
    """
    search_url = ('http://%s/w/api.php?format=json&action=query'
                  '&list=search&srlimit=%d&srprop=timestamp&srwhat=text'
                  '&srsearch=') % (server, num)
    search_url += query
    query = json.loads(web.get(search_url))
    if 'query' in query:
        query = query['query']['search']
        return [r['title'] for r in query]
    else:
        return None


def mw_snippet(server, query):
    """
    Retrives a snippet of the specified length from the given page on the given
    server.
    """
    snippet_url = ('https://' + server + '/w/api.php?format=json'
                   '&action=query&prop=extracts&exintro&explaintext'
                   '&exchars=300&redirects&titles=')
    snippet_url += query
    snippet = json.loads(web.get(snippet_url))
    snippet = snippet['query']['pages']

    # For some reason, the API gives the page *number* as the key, so we just
    # grab the first page number in the results.
    snippet = snippet[list(snippet.keys())[0]]

    return snippet['extract']


@commands('w', 'wiki', 'wik')
@example('.w San Francisco')
def wikipedia(bot, trigger):

    #Set the global default lang. 'en' if not definded
    if not bot.config.has_option('wikipedia', 'default_lang'):
        lang = 'en'
    else:
        lang = bot.config.wikipedia.default_lang

    #change lang if channel has custom language set
    if (trigger.sender and not trigger.sender.is_nick() and
            bot.config.has_option('wikipedia', 'lang_per_channel')):
        customlang = re.search('(' + trigger.sender + '):(\w+)',
                               bot.config.wikipedia.lang_per_channel)
        if customlang is not None:
            lang = customlang.group(2)

    if trigger.group(2) is None:
        bot.reply("What do you want me to look up?")
        return NOLIMIT

    query = trigger.group(2)
    args = re.search(r'^-([a-z]{2,12})\s(.*)', query)
    if args is not None:
        lang = args.group(1)
        query = args.group(2)

    if not query:
        bot.reply('What do you want me to look up?')
        return NOLIMIT
    server = lang + '.wikipedia.org'
    query = mw_search(server, query, 1)
    if not query:
        bot.reply("I can't find any results for that.")
        return NOLIMIT
    else:
        query = query[0]
    snippet = mw_snippet(server, query)

    query = query.replace(' ', '_')
    bot.say('"%s" - http://%s.wikipedia.org/wiki/%s' % (snippet, lang, query))
