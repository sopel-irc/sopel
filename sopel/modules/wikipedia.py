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
    from HTMLParser import HTMLParser
else:
    from urllib.parse import quote, unquote
    from html.parser import HTMLParser

REDIRECT = re.compile(r'^REDIRECT (.*)')


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
    search_url = ('http://%s/w/api.php?format=json&action=query'
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


def say_section(bot, trigger, server, query, section):
    page_name = query.replace('_', ' ')
    query = quote(query.replace(' ', '_'))

    snippet = mw_section(server, query, section)
    if not snippet:
        bot.say("[WIKIPEDIA] Error fetching section \"{}\" for page \"{}\".".format(section, page_name))
        return

    msg = '[WIKIPEDIA] {} - {} | "{}"'.format(page_name, section.replace('_', ' '), snippet)
    bot.say(msg)


def mw_section(server, query, section):
    """
    Retrives a snippet from the specified section from the given page
    on the given server.
    """
    sections_url = ('https://{0}/w/api.php?format=json&redirects'
                    '&action=parse&prop=sections&page={1}')\
                    .format(server, query)
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
    text = ' '.join(text.split())   # collapse multiple whitespace chars

    trimmed = False

    while len(text) > (420 - len(query) - len(section) - 18):
        text = text.rsplit(None, 1)[0]
        trimmed = True
    if trimmed:
        text += '...'

    return text


# Get a wikipedia page (excluding spaces and #, but not /File: links), with a separate optional field for the section
@rule(r'.*\/([a-z]+\.wikipedia\.org)\/wiki\/((?!File\:)[^ #]+)#?([^ ]*).*')
def mw_info(bot, trigger, found_match=None):
    """
    Retrives a snippet of the specified length from the given page on the given
    server.
    """
    match = found_match or trigger
    if match.group(3):
        if match.group(3).startswith('cite_note-'):  # Don't bother trying to retrieve a snippet when cite-note is linked
            say_snippet(bot, trigger, match.group(1), unquote(match.group(2)), show_url=False)
        else:
            say_section(bot, trigger, match.group(1), unquote(match.group(2)), unquote(match.group(3)))
    else:
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
