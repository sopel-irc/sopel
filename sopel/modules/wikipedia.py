# coding=utf-8
# Copyright 2013 Elsie Powell - embolalia.com
# Licensed under the Eiffel Forum License 2.
from __future__ import unicode_literals, absolute_import, print_function, division

from sopel import tools
from sopel.config.types import StaticSection, ValidatedAttribute
from sopel.module import NOLIMIT, commands, example, rule
from requests import get
import re

import sys
if sys.version_info.major < 3:
    from urllib import quote as _quote
    from urlparse import unquote as _unquote
    quote = lambda s: _quote(s.encode('utf-8')).decode('utf-8')
    unquote = lambda s: _unquote(s.encode('utf-8')).decode('utf-8')
else:
    from urllib.parse import quote, unquote

REDIRECT = re.compile(r'^REDIRECT (.*)')


class WikipediaSection(StaticSection):
    default_lang = ValidatedAttribute('default_lang', default='en')
    """The default language to find articles from."""
    lang_per_channel = ValidatedAttribute('lang_per_channel')


def setup(bot):
    bot.config.define_section('wikipedia', WikipediaSection)

    regex = re.compile('([a-z]+).(wikipedia.org/wiki/)([^ ]+)')
    if not bot.memory.contains('url_callbacks'):
        bot.memory['url_callbacks'] = tools.SopelMemory()
    bot.memory['url_callbacks'][regex] = mw_info


def configure(config):
    """
    | name | example | purpose |
    | ---- | ------- | ------- |
    | default\\_lang | en | The default language to find articles from (same as Wikipedia language subdomain) |
    | lang\\_per\\_channel | #YourPants:en,#TusPantalones:es | List of #channel:langcode pairs to define Wikipedia language per channel |
    """
    config.define_section('wikipedia', WikipediaSection)
    config.wikipedia.configure_setting(
        'default_lang',
        "Enter the default language to find articles from."
    )


def mw_search(server, query, num):
    """
    Searches the specified MediaWiki server for the given query, and returns
    the specified number of results.
    """
    search_url = ('https://%s/w/api.php?format=json&action=query'
                  '&list=search&srlimit=%d&srprop=timestamp&srwhat=text'
                  '&srsearch=') % (server, num)
    search_url += query
    query = get(search_url).json()
    if 'query' in query:
        query = query['query']['search']
        return [r['title'] for r in query]
    else:
        return None


def say_snippet(bot, trigger, server, query, show_url=True):
    page_name = query.replace('_', ' ')
    query = quote(query.replace(' ', '_'))
    try:
        snippet = mw_snippet(server, query)
    except KeyError:
        if show_url:
            bot.say("[WIKIPEDIA] Error fetching snippet for \"{}\".".format(page_name))
        return
    msg = '[WIKIPEDIA] {} | "{}"'.format(page_name, snippet)
    msg_url = msg + ' | https://{}/wiki/{}'.format(server, query)
    if msg_url == trigger:  # prevents triggering on another instance of Sopel
        return
    if show_url:
        msg = msg_url
    bot.say(msg)


def mw_snippet(server, query):
    """
    Retrives a snippet of the specified length from the given page on the given
    server.
    """
    snippet_url = ('https://' + server + '/w/api.php?format=json'
                   '&action=query&prop=extracts&exintro&explaintext'
                   '&exchars=300&redirects&titles=')
    snippet_url += query
    snippet = get(snippet_url).json()
    snippet = snippet['query']['pages']

    # For some reason, the API gives the page *number* as the key, so we just
    # grab the first page number in the results.
    snippet = snippet[list(snippet.keys())[0]]

    return snippet['extract']


@rule(r'.*\/([a-z]+\.wikipedia\.org)\/wiki\/((?!File\:)[^ ]+).*')
def mw_info(bot, trigger, found_match=None):
    """
    Retrives a snippet of the specified length from the given page on the given
    server.
    """
    match = found_match or trigger
    say_snippet(bot, trigger, match.group(1), unquote(match.group(2)), show_url=False)


@commands('w', 'wiki', 'wik')
@example('.w San Francisco')
def wikipedia(bot, trigger):
    lang = bot.config.wikipedia.default_lang

    # change lang if channel has custom language set
    if (trigger.sender and not trigger.sender.is_nick() and
            bot.config.wikipedia.lang_per_channel):
        customlang = re.search('(' + trigger.sender + r'):(\w+)',
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
    say_snippet(bot, trigger, server, query)
