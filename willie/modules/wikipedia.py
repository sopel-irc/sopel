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


def mw_search(server, query, num=1):
    """
    Searches the specified MediaWiki server for the given query, and returns
    the specified number of results.
    """
    search_url = ('http://{0}/w/api.php?format=json&action=query'
                  '&list=search&srlimit={1}&srprop=timestamp&srwhat=text&srsearch={2}'
                  ).format(server, num, web.quote(query.encode('utf-8')))
    result = json.loads(web.get(search_url))

    if 'query' in result:
        return [r['title'] for r in result['query']['search']]


def mw_snippet(server, query, length=300):
    """
    Retrives a snippet of the specified length from the given page on the given
    server.
    """
    snippet_url = ('https://{0}/w/api.php?format=json&action=query'
                   '&prop=extracts&exintro&explaintext&exchars={1}&redirects&titles={2}'
                   ).format(server, length, web.quote(query.encode('utf-8')))
    result = json.loads(web.get(snippet_url))

    if 'query' in result:
        pages = result['query']['pages']
        # For some reason, the API gives the page *number* as the key, so we just
        # grab the first page number in the results.
        return pages[pages.keys()[0]]['extract']


@commands('w', 'wiki', 'wik')
@example('.w San Francisco')
def wikipedia(bot, trigger):
    # Set the global default lang, or 'en' if not defined
    lang = ('en' if not bot.config.has_option('wikipedia', 'default_lang')
            else bot.config.wikipedia.default_lang)

    # Change lang if channel has custom language set
    if (trigger.sender and trigger.sender.startswith('#') and
        bot.config.has_option('wikipedia', 'lang_per_channel')
        ):
        customlang = re.search('({0}):(\w+)'.format(trigger.sender),
                               bot.config.wikipedia.lang_per_channel)
        if customlang is not None:
            lang = customlang.group(2)

    query = trigger.group(2)
    if query:
        args = re.search(r'^-([a-z]{2,12})\s(.*)', query)
        if args is not None:
            lang = args.group(1)
            query = args.group(2)

    if not query:
        bot.reply("What do you want me to look up?")
        return NOLIMIT

    server = lang + '.wikipedia.org'

    title = mw_search(server, query)
    if not title:
        bot.reply("I can't find any results for that.")
        return NOLIMIT

    snippet = mw_snippet(server, title[0])
    title = title[0].replace(' ', '_')
    bot.say('"{0}" | http://{1}.wikipedia.org/wiki/{2}'.format(snippet, lang, query))
