"""
wikipedia.py - Sopel Wikipedia Plugin
Copyright 2013 Elsie Powell - embolalia.com
Licensed under the Eiffel Forum License 2.

https://sopel.chat
"""
from __future__ import annotations

from html.parser import HTMLParser
import logging
import re
from urllib.parse import quote, unquote, urlparse

from requests import get

from sopel import plugin
from sopel.config import types


LOGGER = logging.getLogger(__name__)

REDIRECT = re.compile(r'^REDIRECT (.*)')
PLUGIN_OUTPUT_PREFIX = '[wikipedia] '


class WikiParser(HTMLParser):
    NO_CONSUME_TAGS = ('sup', 'style')
    """Tags whose contents should always be ignored.

    These are used in things like inline citations or section "hatnotes", none
    of which are useful output for IRC.
    """

    def __init__(self, section_name):
        HTMLParser.__init__(self)
        self.consume = True
        self.no_consume_depth = 0
        self.is_header = False
        self.section_name = section_name

        self.citations = False
        self.messagebox = False
        self.span_depth = 0
        self.div_depth = 0

        self.result = ''

    def handle_starttag(self, tag, attrs):
        if tag in self.NO_CONSUME_TAGS:
            self.consume = False
            self.no_consume_depth += 1

        elif re.match(r'^h\d$', tag):
            self.is_header = True

        elif tag == 'span':
            if self.span_depth:
                self.span_depth += 1
            else:
                for attr in attrs:  # remove 'edit' tags, and keep track of depth for nested <span> tags
                    if attr[0] == 'class' and 'edit' in attr[1]:
                        self.span_depth += 1

        elif tag == 'div':
            # We want to skip thumbnail text, the table of contents, and section "hatnotes".
            # This also requires tracking div nesting level.
            if self.div_depth:
                self.div_depth += 1
            else:
                for attr in attrs:
                    if attr[0] == 'class' and (
                        'thumb' in attr[1] or 'hatnote' in attr[1] or attr[1] == 'toc'
                    ):
                        self.div_depth += 1
                        break

        elif tag == 'table':
            # Message box templates are what we want to ignore here
            for attr in attrs:
                if (
                    attr[0] == 'class'
                    and any(classname in attr[1].lower() for classname in [
                        # Most of list from https://en.wikipedia.org/wiki/Template:Mbox_templates_see_also
                        'ambox',  # messageboxes on article pages
                        'cmbox',  # messageboxes on category pages
                        'imbox',  # messageboxes on file (image) pages
                        'tmbox',  # messageboxes on talk pages
                        'fmbox',  # header and footer messageboxes
                        'ombox',  # messageboxes on other types of page
                        'mbox',  # for messageboxes that are used in different namespaces and change their presentation accordingly
                        'dmbox',  # for disambiguation messageboxes
                    ])
                ):
                    self.messagebox = True

        elif tag == 'ol':
            for attr in attrs:
                if attr[0] == 'class' and 'references' in attr[1]:
                    self.citations = True   # once we hit citations, we can stop

    def handle_endtag(self, tag):
        if not self.consume and tag in self.NO_CONSUME_TAGS:
            if self.no_consume_depth:
                self.no_consume_depth -= 1
            if not self.no_consume_depth:
                self.consume = True
        if self.is_header and re.match(r'^h\d$', tag):
            self.is_header = False
        if self.span_depth and tag == 'span':
            self.span_depth -= 1
        if self.div_depth and tag == 'div':
            self.div_depth -= 1
        if self.messagebox and tag == 'table':
            self.messagebox = False

    def handle_data(self, data):
        if self.consume and not any([self.citations, self.messagebox, self.span_depth, self.div_depth]):
            if not (self.is_header and data == self.section_name):  # Skip the initial header info only
                self.result += data

    def get_result(self):
        return self.result


class WikipediaSection(types.StaticSection):
    default_lang = types.ValidatedAttribute('default_lang', default='en')
    """The default language to find articles from (same as Wikipedia language subdomain)."""


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


def say_snippet(bot, trigger, server, query, show_url=True, commanded=False):
    page_name = query.replace('_', ' ')
    query = quote(query.replace(' ', '_'))
    url = 'https://{}/wiki/{}'.format(server, query)

    # If the trigger looks like another instance of this plugin, assume it is
    if trigger.startswith(PLUGIN_OUTPUT_PREFIX) and trigger.endswith(' | ' + url):
        return

    try:
        snippet = mw_snippet(server, query)
        # Coalesce repeated whitespace to avoid problems with <math> on MediaWiki
        # see https://github.com/sopel-irc/sopel/issues/2259
        snippet = re.sub(r"\s+", " ", snippet)
    except KeyError:
        msg = 'Error fetching snippet for "{}".'.format(page_name)
        if commanded:
            bot.reply(msg)
        else:
            bot.say(msg)
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
        bot.say('Error fetching section "{}" for page "{}".'.format(section, page_name))
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

    fetch_title = section_number = None

    for entry in sections['parse']['sections']:
        if entry['anchor'] == section:
            section_number = entry['index']
            # Needed to handle sections from transcluded pages properly
            # e.g. template documentation (usually pulled in from /doc subpage).
            # One might expect this prop to be nullable because in most cases it
            # will simply repeat the requested page title, but it's always set.
            fetch_title = entry.get('fromtitle')
            break

    if section_number is None or fetch_title is None:
        return None

    snippet_url = ('https://{0}/w/api.php?format=json&redirects'
                   '&action=parse&page={1}&prop=text'
                   '&section={2}').format(server, quote(fetch_title), section_number)

    data = get(snippet_url).json()

    parser = WikiParser(section.replace('_', ' '))
    parser.feed(data['parse']['text']['*'])
    text = parser.get_result()
    text = ' '.join(text.split())  # collapse multiple whitespace chars

    return text


def say_image_description(bot, trigger, server, image):
    desc = mw_image_description(server, image)

    if desc:
        bot.say(desc, truncation=" […]")


def mw_image_description(server, image):
    """Retrieves the description for the given image."""
    params = "&".join([
        "action=query",
        "prop=imageinfo",
        "format=json",
        "indexpageids=1",
        "iiprop=extmetadata",
        "iiextmetadatafilter=ImageDescription",
        "iilimit=1",
        "titles={image}".format(image=image),
    ])
    url = "https://{server}/w/api.php?{params}".format(server=server, params=params)

    response = get(url)
    json = response.json()

    try:
        query_data = json["query"]
        pageids = query_data["pageids"]
        pages = query_data["pages"]

        page = pages[pageids[0]]

        raw_desc = page["imageinfo"][0]["extmetadata"]["ImageDescription"]["value"]

    except LookupError:
        LOGGER.exception("Error getting image description for %r, response was: %r", image, json)
        return None

    # Some descriptions contain markup, use WikiParser to discard that
    parser = WikiParser(image)
    parser.feed(raw_desc)
    desc = parser.get_result()
    desc = ' '.join(desc.split())  # collapse multiple whitespace chars

    return desc


# Matches a Wikipedia link (excluding /File: pages)
@plugin.url(r'https?:\/\/([a-z]+(?:\.m)?\.wikipedia\.org)\/wiki\/((?!File\:)[^ ]+)')
@plugin.output_prefix(PLUGIN_OUTPUT_PREFIX)
def mw_info(bot, trigger, match=None):
    """Retrieves and outputs a snippet of the linked page."""
    server = match.group(1)
    page_info = urlparse(match.group(0))
    # in Python 3.9+ this can be str.removeprefix() instead, but we're confident that
    # "/wiki/" is at the start of the path anyway since it's part of the pattern
    trim_offset = len("/wiki/")
    article = unquote(page_info.path)[trim_offset:]
    section = unquote(page_info.fragment)

    if article.startswith("Special:"):
        # The MediaWiki query API does not include pages in the Special:
        # namespace, so there's no point bothering when we know this will error
        LOGGER.debug("Ignoring page in Special: namespace")
        return False

    if section:
        if section.startswith('cite_note-'):
            # Don't bother trying to retrieve a section snippet if cite-note is linked
            say_snippet(bot, trigger, server, article, show_url=False)
        elif section.startswith('/media'):
            # gh2316: media fragments are usually images; try to get an image description
            image = section[7:]  # strip '/media' prefix in pre-3.9 friendly way
            say_image_description(bot, trigger, server, image)
        else:
            say_section(bot, trigger, server, article, section)
    else:
        say_snippet(bot, trigger, server, article, show_url=False)


@plugin.command('wikipedia', 'wp')
@plugin.example('.wp San Francisco')
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

    if query.startswith("Special:"):
        bot.reply("Sorry, the MediaWiki API doesn't support querying the Special: namespace.")
        return False

    server = lang + '.wikipedia.org'
    query = mw_search(server, query, 1)
    if not query:
        bot.reply("I can't find any results for that.")
        return plugin.NOLIMIT
    else:
        query = query[0]
    say_snippet(bot, trigger, server, query, commanded=True)


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
        return

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
        return

    bot.db.set_channel_value(trigger.sender, 'wikipedia_lang', trigger.group(3))
    bot.say(
        "Set {}'s Wikipedia language to: {}"
        .format(trigger.sender, trigger.group(3))
    )
