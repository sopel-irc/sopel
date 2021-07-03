# coding=utf-8
"""
wikipedia.py - Sopel Wikipedia Plugin
Copyright 2013 Elsie Powell - embolalia.com
Licensed under the Eiffel Forum License 2.

https://sopel.chat
"""
from __future__ import absolute_import, division, print_function, unicode_literals

import logging
import re

from requests import get

from sopel import plugin
from sopel.config import types
from sopel.tools.web import quote, unquote

try:  # TODO: Remove fallback when dropping py2
    from html.parser import HTMLParser
except ImportError:
    from HTMLParser import HTMLParser

LOGGER = logging.getLogger(__name__)
REDIRECT = re.compile(r'^REDIRECT (.*)')
PLUGIN_OUTPUT_PREFIX = '[wikipedia] '


class WikiParser(HTMLParser):
    def __init__(self, section_name):
        HTMLParser.__init__(self)
        self.consume = True
        self.is_header = False
        self.section_name = section_name

        self.citations = False
        self.span_depth = 0
        self.div_depth = 0

        self.result = ''

    def handle_starttag(self, tag, attrs):
        if tag == 'sup':    # don't consume anything in superscript (citation-related tags)
            self.consume = False

        elif re.match(r'^h\d$', tag):
            self.is_header = True

        elif tag == 'span':
            if self.span_depth:
                self.span_depth += 1
            else:
                for attr in attrs:  # remove 'edit' tags, and keep track of depth for nested <span> tags
                    if attr[0] == 'class' and 'edit' in attr[1]:
                        self.span_depth += 1

        elif tag == 'div':  # We want to skip thumbnail text and the inexplicable table of contents, and as such also need to track div depth
            if self.div_depth:
                self.div_depth += 1
            else:
                for attr in attrs:
                    if attr[0] == 'class' and ('thumb' in attr[1] or attr[1] == 'toc'):
                        self.div_depth += 1

        elif tag == 'ol':
            for attr in attrs:
                if attr[0] == 'class' and 'references' in attr[1]:
                    self.citations = True   # once we hit citations, we can stop

    def handle_endtag(self, tag):
        if not self.consume and tag == 'sup':
            self.consume = True
        if self.is_header and re.match(r'^h\d$', tag):
            self.is_header = False
        if self.span_depth and tag == 'span':
            self.span_depth -= 1
        if self.div_depth and tag == 'div':
            self.div_depth -= 1

    def handle_data(self, data):
        if self.consume and not any([self.citations, self.span_depth, self.div_depth]):
            if not (self.is_header and data == self.section_name):  # Skip the initial header info only
                self.result += data

    def get_result(self):
        return self.result


class WikipediaSection(types.StaticSection):
    default_lang = types.ValidatedAttribute('default_lang', default='en')
    """The default language to find articles from (same as Wikipedia language subdomain)."""
    lang_per_channel = types.ValidatedAttribute('lang_per_channel')
    """List of ``#channel:langcode`` pairs to define Wikipedia language per channel.

    Deprecated: Will be removed in Sopel 8. Use ``.wpclang`` to manage per-channel language settings.
    """


def setup(bot):
    bot.config.define_section('wikipedia', WikipediaSection)


def configure(config):
    """
    | name | example | purpose |
    | ---- | ------- | ------- |
    | default\\_lang | en | The default language to find articles from (same as Wikipedia language subdomain) |
    """
    config.define_section('wikipedia', WikipediaSection)
    config.wikipedia.configure_setting(
        'default_lang',
        "Enter the default language to find articles from."
    )


def choose_lang(bot, trigger):
    """Determine what language to use for queries based on sender/context."""
    user_lang = bot.db.get_nick_value(trigger.nick, 'wikipedia_lang')
    if user_lang:
        return user_lang

    if not trigger.sender.is_nick():
        channel_lang = bot.db.get_channel_value(trigger.sender, 'wikipedia_lang')
        if channel_lang:
            return channel_lang

    if bot.config.wikipedia.lang_per_channel:
        customlang = re.search('(' + trigger.sender + r'):(\w+)',
                               bot.config.wikipedia.lang_per_channel)
        if customlang is not None:
            LOGGER.warning(
                'Language for %s loaded from the deprecated config setting, '
                'wikipedia.lang_per_channel',
                trigger.sender,
            )
            return customlang.group(2)

    return bot.config.wikipedia.default_lang


def mw_search(server, query, num):
    """Search a MediaWiki site

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
    return None


def say_snippet(bot, trigger, server, query, show_url=True):
    page_name = query.replace('_', ' ')
    query = quote(query.replace(' ', '_'))
    url = 'https://{}/wiki/{}'.format(server, query)

    # If the trigger looks like another instance of this plugin, assume it is
    if trigger.startswith(PLUGIN_OUTPUT_PREFIX) and trigger.endswith(' | ' + url):
        return

    try:
        snippet = mw_snippet(server, query)
    except KeyError:
        if show_url:
            bot.reply("Error fetching snippet for \"{}\".".format(page_name))
        return

    msg = '{} | "{}'.format(page_name, snippet)

    trailing = '"'
    if show_url:
        trailing += ' | ' + url

    bot.say(msg, truncation=' […]', trailing=trailing)


def mw_snippet(server, query):
    """Retrieves a snippet of the given page from the given MediaWiki server."""
    snippet_url = ('https://' + server + '/w/api.php?format=json'
                   '&action=query&prop=extracts&exintro&explaintext'
                   '&exchars=500&redirects&titles=')
    snippet_url += query
    snippet = get(snippet_url).json()
    snippet = snippet['query']['pages']

    # For some reason, the API gives the page *number* as the key, so we just
    # grab the first page number in the results.
    snippet = snippet[list(snippet.keys())[0]]

    return snippet['extract']


def say_section(bot, trigger, server, query, section):
    page_name = query.replace('_', ' ')
    query = quote(query.replace(' ', '_'))

    snippet = mw_section(server, query, section)
    if not snippet:
        bot.reply("Error fetching section \"{}\" for page \"{}\".".format(section, page_name))
        return

    msg = '{} - {} | "{}"'.format(page_name, section.replace('_', ' '), snippet)
    bot.say(msg, truncation=' […]"')


def mw_section(server, query, section):
    """
    Retrieves a snippet from the specified section from the given page
    on the given server.
    """
    sections_url = ('https://{0}/w/api.php?format=json&redirects'
                    '&action=parse&prop=sections&page={1}'
                    .format(server, query))
    sections = get(sections_url).json()

    section_number = None

    for entry in sections['parse']['sections']:
        if entry['anchor'] == section:
            section_number = entry['index']
            break

    if not section_number:
        return None

    snippet_url = ('https://{0}/w/api.php?format=json&redirects'
                   '&action=parse&page={1}&prop=text'
                   '&section={2}').format(server, query, section_number)

    data = get(snippet_url).json()

    parser = WikiParser(section.replace('_', ' '))
    parser.feed(data['parse']['text']['*'])
    text = parser.get_result()
    text = ' '.join(text.split())  # collapse multiple whitespace chars

    return text


# Matches a wikipedia page (excluding spaces and #, but not /File: links), with a separate optional field for the section
@plugin.url(r'https?:\/\/([a-z]+\.wikipedia\.org)\/wiki\/((?!File\:)[^ #]+)#?([^ ]*)')
@plugin.output_prefix(PLUGIN_OUTPUT_PREFIX)
def mw_info(bot, trigger, match=None):
    """Retrieves and outputs a snippet of the linked page."""
    if match.group(3):
        if match.group(3).startswith('cite_note-'):  # Don't bother trying to retrieve a snippet when cite-note is linked
            say_snippet(bot, trigger, match.group(1), unquote(match.group(2)), show_url=False)
        else:
            say_section(bot, trigger, match.group(1), unquote(match.group(2)), unquote(match.group(3)))
    else:
        say_snippet(bot, trigger, match.group(1), unquote(match.group(2)), show_url=False)


@plugin.command('w', 'wiki', 'wik')
@plugin.example('.w San Francisco')
@plugin.output_prefix('[wikipedia] ')
def wikipedia(bot, trigger):
    """Search Wikipedia."""
    if trigger.group(2) is None:
        bot.reply("What do you want me to look up?")
        return plugin.NOLIMIT

    lang = choose_lang(bot, trigger)
    query = trigger.group(2)
    args = re.search(r'^-([a-z]{2,12})\s(.*)', query)
    if args is not None:
        lang = args.group(1)
        query = args.group(2)

    if not query:
        bot.reply('What do you want me to look up?')
        return plugin.NOLIMIT
    server = lang + '.wikipedia.org'
    query = mw_search(server, query, 1)
    if not query:
        bot.reply("I can't find any results for that.")
        return plugin.NOLIMIT
    else:
        query = query[0]
    say_snippet(bot, trigger, server, query)


@plugin.command('wplang')
@plugin.example('.wplang pl')
def wplang(bot, trigger):
    if not trigger.group(3):
        bot.reply(
            "Your current Wikipedia language is: {}"
            .format(
                bot.db.get_nick_value(
                    trigger.nick, 'wikipedia_lang',
                    bot.config.wikipedia.default_lang)
            )
        )
    else:
        bot.db.set_nick_value(trigger.nick, 'wikipedia_lang', trigger.group(3))
        bot.reply(
            "Set your Wikipedia language to: {}"
            .format(trigger.group(3))
        )


@plugin.command('wpclang')
@plugin.example('.wpclang ja')
@plugin.require_chanmsg()
@plugin.output_prefix(PLUGIN_OUTPUT_PREFIX)
def wpclang(bot, trigger):
    if not (trigger.admin or bot.channels[trigger.sender.lower()].privileges[trigger.nick.lower()] >= plugin.OP):
        bot.reply("You don't have permission to change this channel's Wikipedia language setting.")
        return plugin.NOLIMIT
    if not trigger.group(3):
        bot.say(
            "{}'s current Wikipedia language is: {}"
            .format(
                trigger.sender,
                bot.db.get_nick_value(
                    trigger.nick, 'wikipedia_lang',
                    bot.config.wikipedia.default_lang)
            )
        )
    else:
        bot.db.set_channel_value(trigger.sender, 'wikipedia_lang', trigger.group(3))
        bot.say(
            "Set {}'s Wikipedia language to: {}"
            .format(trigger.sender, trigger.group(3))
        )
