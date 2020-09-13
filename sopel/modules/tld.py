# coding=utf-8
"""
tld.py - Sopel TLD Plugin
Copyright 2009-10, Michael Yanovich, yanovich.net
Copyright 2020, dgw, technobabbl.es
Licensed under the Eiffel Forum License 2.

https://sopel.chat
"""
from __future__ import absolute_import, division, print_function, unicode_literals

from datetime import datetime
from encodings import idna
import logging
import re
import sys

import requests

from sopel import plugin, tools

if sys.version_info.major >= 3:
    unicode = str
    from html.parser import HTMLParser
else:
    from HTMLParser import HTMLParser


LOGGER = logging.getLogger(__name__)


DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
IANA_LIST_URI = 'https://data.iana.org/TLD/tlds-alpha-by-domain.txt'
WIKI_PAGE_URI = 'https://en.wikipedia.org/wiki/List_of_Internet_top-level_domains'
r_tld = re.compile(r'^\.(\S+)')
r_idn = re.compile(r'^(xn--[A-Za-z0-9]+)')


def setup(bot):
    bot.memory['tld_list_cache'] = bot.db.get_plugin_value(
        'tld', 'tld_list_cache', [])
    bot.memory['tld_list_cache_updated'] = bot.db.get_plugin_value(
        'tld', 'tld_list_cache_updated', '2000-01-01 00:00:00')
    bot.memory['tld_data_cache'] = bot.db.get_plugin_value(
        'tld', 'tld_data_cache', {})
    bot.memory['tld_data_cache_updated'] = bot.db.get_plugin_value(
        'tld', 'tld_data_cache_updated', '2000-01-01 00:00:00')

    # restore datetime objects from string format
    bot.memory['tld_list_cache_updated'] = datetime.strptime(
        bot.memory['tld_list_cache_updated'], DATE_FORMAT)
    bot.memory['tld_data_cache_updated'] = datetime.strptime(
        bot.memory['tld_data_cache_updated'], DATE_FORMAT)


def shutdown(bot):
    if bot.memory['tld_list_cache']:
        bot.db.set_plugin_value(
            'tld', 'tld_list_cache', bot.memory['tld_list_cache'])
        bot.db.set_plugin_value(
            'tld', 'tld_list_cache_updated',
            bot.memory['tld_list_cache_updated'].strftime(DATE_FORMAT))
    if bot.memory['tld_data_cache']:
        bot.db.set_plugin_value(
            'tld', 'tld_data_cache', bot.memory['tld_data_cache'])
        bot.db.set_plugin_value(
            'tld', 'tld_data_cache_updated',
            bot.memory['tld_data_cache_updated'].strftime(DATE_FORMAT))

    for key in [
        'tld_list_cache',
        'tld_list_cache_updated',
        'tld_data_cache',
        'tld_data_cache_updated',
    ]:
        try:
            del bot.memory[key]
        except KeyError:
            pass


class WikipediaTLDListParser(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)
        self.in_cell = False
        self.skipping = True
        self.current_row = []
        self.current_cell = ''
        self.rows = []
        self.tables = []

    def handle_starttag(self, tag, attrs):
        if tag == 'td' or tag == 'th':
            self.in_cell = True
        elif tag == 'sup':
            # ignore superscripts; they're almost exclusively footnotes
            self.skipping = True
        elif tag == 'table':
            for name, value in attrs:
                if name == 'class' and 'wikitable' in value:
                    self.skipping = False

    def handle_endtag(self, tag):
        if tag == 'td' or tag == 'th':
            self.in_cell = False
            if not self.skipping:
                self.current_row.append(self.current_cell)
            self.current_cell = ''
        elif tag == 'tr':
            if not self.skipping:
                self.rows.append(tuple([cell.strip() for cell in self.current_row]))
            self.current_row = []
        elif tag == 'table':
            if not self.skipping:
                self.tables.append(self.rows)
            self.rows = []
            self.skipping = True
            self.in_cell = False
        elif tag == 'sup' and self.in_cell:
            self.skipping = False

    def handle_data(self, data):
        if self.in_cell and not self.skipping:
            self.current_cell += data


def process_parser_result(parser):
    tables = parser.tables
    tld_list = {}

    for table in tables:
        headings = table[0]
        for row in table[1:]:
            key = None
            idn_key = None
            for cell in row:
                tld = r_tld.match(cell)
                if tld:
                    key = tld.group(1).lower()
                idn = r_idn.match(cell)
                if idn:
                    idn_key = idn.group(1).lower()
            if not any([key, idn_key]):
                LOGGER.warning(
                    "Skipping row %s; could not find string to use as lookup key.",
                    str(row),
                )
                continue

            # Some cleanup happens directly in the dict comprehension here.
            # Empty values (actually falsy, but only empty strings are possible)
            # and values consisting only of a dash (indicating the absence of
            # information or restrictions) get left out of the final data.
            # When the data is presented later, these empty fields are just
            # clutter taking up limited space in the IRC line.
            zipped = {
                field: value
                for field, value
                in dict(zip(headings, row)).items()
                if value and value != '—'
            }
            if key:
                tld_list[key] = zipped
            if idn_key:
                tld_list[idn_key] = zipped

    return tld_list


def _update_tld_data(bot, which):
    if which == 'list':
        then = bot.memory['tld_list_cache_updated']
    elif which == 'data':
        then = bot.memory['tld_data_cache_updated']
    else:
        LOGGER.error("Asked to update unknown cache type '%s'.", which)
        return

    now = datetime.now()
    since = now - then
    if since.days < 7:
        LOGGER.debug(
            "Skipping TLD %s cache update; the cache is only %d days old.",
            which,
            since.days,
        )
        return

    if which == 'list':
        try:
            tld_list = requests.get(IANA_LIST_URI).text
        except requests.exceptions.RequestException:
            # Probably a transient error; log it and continue life
            LOGGER.warning(
                "Error fetching IANA TLD list; will try again later.",
                exc_info=True)
            return

        tld_list = [
            line.lower()
            for line in tld_list.splitlines()
            if not line.startswith('#')
        ]

        bot.memory['tld_list_cache'] = tld_list
        bot.memory['tld_list_cache_updated'] = now
    elif which == 'data':
        try:
            tld_data = requests.get(WIKI_PAGE_URI).text
        except requests.exceptions.RequestException:
            # Log error and continue life; it'll be fine
            LOGGER.warning(
                "Error fetching TLD data from Wikipedia; will try again later.",
                exc_info=True)
            return

        parser = WikipediaTLDListParser()
        parser.feed(tld_data)
        tld_data = process_parser_result(parser)

        bot.memory['tld_data_cache'] = tld_data
        bot.memory['tld_data_cache_updated'] = now

    LOGGER.debug("Updated TLD %s cache.", which)


@plugin.interval(60 * 60)
def update_caches(bot):
    _update_tld_data(bot, 'list')
    _update_tld_data(bot, 'data')


@plugin.command('tld')
@plugin.example('.tld ru')
@plugin.output_prefix('[tld] ')
def gettld(bot, trigger):
    """Show information about the given Top Level Domain."""
    tld = trigger.group(2)
    if not tld:
        bot.reply("You must provide a top-level domain to search.")
        return  # Stop if no tld argument is provided
    tld = tld.strip('.').lower()

    if not bot.memory['tld_list_cache']:
        _update_tld_data(bot, 'list')
    tld_list = bot.memory['tld_list_cache']

    if not any([
        name in tld_list
        for name
        in [tld, idna.ToASCII(tld).decode('utf-8')]
    ]):
        bot.reply(
            "The top-level domain '{}' is not in IANA's list of valid TLDs."
            .format(tld))
        return

    if not bot.memory['tld_data_cache']:
        _update_tld_data(bot, 'data')
    tld_data = bot.memory['tld_data_cache']

    record = tld_data.get(tld, None)
    if not record:
        bot.say(
            "The top-level domain '{}' exists, "
            "but no details about it could be found."
            .format(tld)
        )
        return

    # Build the order in which to output available data fields
    fields = list(record.keys())
    # This trick moves matching keys to the end of the list
    fields.sort(key=lambda s: s.startswith('Notes') or s.startswith('Comments'))
    # This column depends on HTML formatting to make sense; skip it for now
    try:
        fields.remove('Explanation')
    except ValueError:
        pass

    items = []
    for field in fields:
        value = record[field]
        if value:
            items.append('{}: {}'.format(field, value))

    message = ' | '.join(items)
    usable, excess = tools.get_sendable_message(message)
    if excess:
        message = usable + ' […]'

    bot.say(message)
