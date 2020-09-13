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

from sopel import plugin
from sopel.tools import web

if sys.version_info.major >= 3:
    unicode = str


LOGGER = logging.getLogger(__name__)


DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
IANA_LIST_URI = 'https://data.iana.org/TLD/tlds-alpha-by-domain.txt'
WIKI_PAGE_URI = 'https://en.wikipedia.org/wiki/List_of_Internet_top-level_domains'
r_tag = re.compile(r'<(?!!)[^>]+>')


def setup(bot):
    bot.memory['tld_list_cache'] = bot.db.get_plugin_value(
        'tld', 'tld_list_cache', [])
    bot.memory['tld_list_cache_updated'] = bot.db.get_plugin_value(
        'tld', 'tld_list_cache_updated', '2000-01-01 00:00:00')
    bot.memory['tld_list_cache_updated'] = datetime.strptime(
        bot.memory['tld_list_cache_updated'], DATE_FORMAT)



def shutdown(bot):
    if bot.memory['tld_list_cache']:
        bot.db.set_plugin_value(
            'tld', 'tld_list_cache', bot.memory['tld_list_cache'])
        bot.db.set_plugin_value(
            'tld', 'tld_list_cache_updated',
            bot.memory['tld_list_cache_updated'].strftime(DATE_FORMAT))

    for key in ['tld_list_cache', 'tld_list_cache_updated']:
        try:
            del bot.memory[key]
        except KeyError:
            pass


@plugin.interval(60 * 60)
def update_tld_list(bot):
    now = datetime.now()
    then = bot.memory['tld_list_cache_updated']
    since = now - then
    if since.days < 7:
        LOGGER.debug(
            "Skipping TLD list cache update; the cached list is only %d days old.",
            since.days,
        )
        return

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
    LOGGER.debug("Updated TLD list cache.")


@plugin.command('tld')
@plugin.example('.tld ru')
@plugin.output_prefix('[tld] ')
def gettld(bot, trigger):
    """Show information about the given Top Level Domain."""
    tld = trigger.group(2)
    if not tld:
        bot.reply("You must provide a top-level domain to search.")
        return  # Stop if no tld argument is provided
    if tld[0] == '.':
        tld = tld[1:]

    if not bot.memory['tld_list_cache']:
        update_tld_list(bot)
    tld_list = bot.memory['tld_list_cache']

    if not any([
        name in tld_list
        for name
        in [tld.lower(), idna.ToASCII(tld).decode('utf-8')]
    ]):
        bot.reply(
            "The top-level domain '{}' is not in IANA's list of valid TLDs."
            .format(tld))
        return

    page = requests.get(WIKI_PAGE_URI).text
    search = r'(?i)<td><a href="\S+" title="\S+">\.{0}</a></td>\n(<td><a href=".*</a></td>\n)?<td>([A-Za-z0-9].*?)</td>\n<td>(.*)</td>\n<td[^>]*>(.*?)</td>\n<td[^>]*>(.*?)</td>\n'
    search = search.format(tld)
    re_country = re.compile(search)
    matches = re_country.findall(page)
    if not matches:
        search = r'(?i)<td><a href="\S+" title="(\S+)">\.{0}</a></td>\n<td><a href=".*">(.*)</a></td>\n<td>([A-Za-z0-9].*?)</td>\n<td[^>]*>(.*?)</td>\n<td[^>]*>(.*?)</td>\n'
        search = search.format(tld)
        re_country = re.compile(search)
        matches = re_country.findall(page)
    if matches:
        matches = list(matches[0])
        i = 0
        while i < len(matches):
            matches[i] = r_tag.sub("", matches[i])
            i += 1
        desc = matches[2]
        if len(desc) > 400:
            desc = desc[:400] + "..."
        reply = "%s -- %s. IDN: %s, DNSSEC: %s" % (
            matches[1], desc, matches[3], matches[4]
        )
    else:
        search = r'<td><a href="\S+" title="\S+">.{0}</a></td>\n<td><span class="flagicon"><img.*?\">(.*?)</a></td>\n<td[^>]*>(.*?)</td>\n<td[^>]*>(.*?)</td>\n<td[^>]*>(.*?)</td>\n<td[^>]*>(.*?)</td>\n<td[^>]*>(.*?)</td>\n'
        search = search.format(unicode(tld))
        re_country = re.compile(search)
        matches = re_country.findall(page)
        if matches:
            matches = matches[0]
            dict_val = dict()
            dict_val["country"], dict_val["expl"], dict_val["notes"], dict_val["idn"], dict_val["dnssec"], dict_val["sld"] = matches
            for key in dict_val:
                if dict_val[key] == "&#160;":
                    dict_val[key] = "N/A"
                dict_val[key] = r_tag.sub('', dict_val[key])
            if len(dict_val["notes"]) > 400:
                dict_val["notes"] = dict_val["notes"][:400] + "..."
            reply = "%s (%s, %s). IDN: %s, DNSSEC: %s, SLD: %s" % (dict_val["country"], dict_val["expl"], dict_val["notes"], dict_val["idn"], dict_val["dnssec"], dict_val["sld"])
        else:
            reply = "The top-level domain '{}' exists, but no details about it could be found.".format(tld)
    # Final touches + output
    reply = web.decode(reply)
    bot.say(reply)
