# coding=utf-8
"""
safety.py - Alerts about malicious URLs
Copyright © 2014, Elad Alfassa, <elad@fedoraproject.org>
Licensed under the Eiffel Forum License 2.

This plugin uses virustotal.com
"""
from __future__ import absolute_import, division, print_function, unicode_literals

import logging
import os.path
import re
import sys
import threading
import time

import requests

from sopel import formatting, plugin, tools
from sopel.config import types

try:
    # This is done separately from the below version if/else because JSONDecodeError
    # didn't appear until Python 3.5, but Sopel claims support for 3.3+
    # Redo this whole block of nonsense when dropping py2/old py3 support
    from json import JSONDecodeError as InvalidJSONResponse
except ImportError:
    InvalidJSONResponse = ValueError

if sys.version_info.major > 2:
    unicode = str
    from urllib.request import urlretrieve
    from urllib.parse import urlparse
else:
    from urllib import urlretrieve
    from urlparse import urlparse


LOGGER = logging.getLogger(__name__)
PLUGIN_OUTPUT_PREFIX = '[safety] '

vt_base_api_url = 'https://www.virustotal.com/vtapi/v2/url/'
malware_domains = set()
known_good = []
cache_limit = 512


class SafetySection(types.StaticSection):
    enabled_by_default = types.BooleanAttribute('enabled_by_default', default=True)
    """Whether to enable URL safety in all channels where it isn't explicitly disabled."""
    known_good = types.ListAttribute('known_good')
    """List of "known good" domains to ignore."""
    vt_api_key = types.ValidatedAttribute('vt_api_key')
    """Optional VirusTotal API key (improves malicious URL detection)."""


def configure(config):
    """
    | name | example | purpose |
    | ---- | ------- | ------- |
    | enabled\\_by\\_default | True | Enable URL safety in all channels where it isn't explicitly disabled. |
    | known\\_good | sopel.chat,dftba.net | List of "known good" domains to ignore. |
    | vt\\_api\\_key | 0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef | Optional VirusTotal API key to improve malicious URL detection |
    """
    config.define_section('safety', SafetySection)
    config.safety.configure_setting(
        'enabled_by_default',
        "Enable URL safety in channels that don't specifically disable it?",
    )
    config.safety.configure_setting(
        'known_good',
        'Enter any domains to whitelist',
    )
    config.safety.configure_setting(
        'vt_api_key',
        "Optionally, enter a VirusTotal API key to improve malicious URL "
        "protection.\nOtherwise, only the StevenBlack list will be used."
    )


def setup(bot):
    bot.config.define_section('safety', SafetySection)

    if 'safety_cache' not in bot.memory:
        bot.memory['safety_cache'] = tools.SopelMemory()
    if 'safety_cache_lock' not in bot.memory:
        bot.memory['safety_cache_lock'] = threading.Lock()
    for item in bot.config.safety.known_good:
        known_good.append(re.compile(item, re.I))

    old_file = os.path.join(bot.config.homedir, 'malwaredomains.txt')
    if os.path.exists(old_file) and os.path.isfile(old_file):
        LOGGER.info('Removing old malwaredomains file from %s', old_file)
        try:
            os.remove(old_file)
        except Exception as err:
            # for lack of a more specific error type...
            # Python on Windows throws an exception if the file is in use
            LOGGER.info('Could not delete %s: %s', old_file, str(err))

    loc = os.path.join(bot.config.homedir, 'unsafedomains.txt')
    if os.path.isfile(loc):
        if os.path.getmtime(loc) < time.time() - 24 * 60 * 60:
            # File exists but older than one day — update it
            _download_domain_list(loc)
    else:
        _download_domain_list(loc)
    with open(loc, 'r') as f:
        for line in f:
            if sys.version_info.major < 3:
                line = unicode(line, 'utf-8')
            else:
                line = unicode(line)

            clean_line = line.strip().lower()

            if not clean_line or clean_line[0] == '#':
                # blank line or comment
                continue

            parts = clean_line.split(' ', 1)
            try:
                domain = parts[1]
            except IndexError:
                # line does not contain a hosts entry; skip it
                continue

            if '.' in domain:
                # only publicly routable domains matter; skip loopback/link-local stuff
                malware_domains.add(domain)


def shutdown(bot):
    bot.memory.pop('safety_cache', None)
    bot.memory.pop('safety_cache_lock', None)


def _download_domain_list(path):
    url = 'https://raw.githubusercontent.com/StevenBlack/hosts/master/hosts'
    LOGGER.info('Downloading malicious domain list from %s', url)
    urlretrieve(url, path)


@plugin.rule(r'(?u).*(https?://\S+).*')
@plugin.priority('high')
@plugin.output_prefix(PLUGIN_OUTPUT_PREFIX)
def url_handler(bot, trigger):
    """Checks for malicious URLs"""
    check = True    # Enable URL checking
    strict = False  # Strict mode: kick on malicious URL
    positives = 0   # Number of engines saying it's malicious
    total = 0       # Number of total engines
    use_vt = True   # Use VirusTotal
    check = bot.config.safety.enabled_by_default
    if check is None:
        # If not set, assume default
        check = True
    # DB overrides config:
    setting = bot.db.get_channel_value(trigger.sender, 'safety')
    if setting is not None:
        if setting == 'off':
            return  # Not checking
        elif setting in ['on', 'strict', 'local', 'local strict']:
            check = True
        if setting == 'strict' or setting == 'local strict':
            strict = True
        if setting == 'local' or setting == 'local strict':
            use_vt = False

    if not check:
        return  # Not overridden by DB, configured default off

    try:
        netloc = urlparse(trigger.group(1)).netloc
    except ValueError:
        return  # Invalid IPv6 URL

    if any(regex.search(netloc) for regex in known_good):
        return  # Whitelisted

    apikey = bot.config.safety.vt_api_key
    try:
        if apikey is not None and use_vt:
            payload = {'resource': unicode(trigger),
                       'apikey': apikey,
                       'scan': '1'}

            if trigger not in bot.memory['safety_cache']:
                r = requests.post(vt_base_api_url + 'report', data=payload)
                r.raise_for_status()
                result = r.json()
                fetched = time.time()
                if all(k in result for k in ['positives', 'total']):
                    # cache result only if it contains a scan report
                    # TODO: handle checking back for results from queued scans
                    data = {'positives': result['positives'],
                            'total': result['total'],
                            'fetched': fetched}
                    bot.memory['safety_cache'][trigger] = data
                    if len(bot.memory['safety_cache']) >= (2 * cache_limit):
                        _clean_cache(bot)
            else:
                LOGGER.debug('using cache')
                result = bot.memory['safety_cache'][trigger]
            positives = result.get('positives', 0)
            total = result.get('total', 0)
    except requests.exceptions.RequestException:
        # Ignoring exceptions with VT so domain list will always work
        LOGGER.debug('[VirusTotal] Error obtaining response.', exc_info=True)
    except InvalidJSONResponse:
        # Ignoring exceptions with VT so domain list will always work
        LOGGER.debug('[VirusTotal] Malformed response (invalid JSON).', exc_info=True)

    if unicode(netloc).lower() in malware_domains:
        positives += 1
        total += 1

    if positives >= 1:
        # Possibly malicious URL detected!
        confidence = '{}%'.format(round((positives / total) * 100))
        msg = (
            'link posted by %s is possibly malicious '
            % formatting.bold(trigger.nick)
        )
        msg += '(confidence %s - %s/%s)' % (confidence, positives, total)
        warning = formatting.bold(formatting.color('WARNING:', 'red'))
        bot.say(warning + ' ' + msg)
        if strict:
            bot.kick(trigger.nick, trigger.sender, 'Posted a malicious link')


@plugin.command('safety')
@plugin.output_prefix(PLUGIN_OUTPUT_PREFIX)
def toggle_safety(bot, trigger):
    """Set safety setting for channel"""
    if not trigger.admin and bot.channels[trigger.sender].privileges[trigger.nick] < plugin.OP:
        bot.reply('Only channel operators can change safety settings')
        return
    allowed_states = ['strict', 'on', 'off', 'local', 'local strict']
    if not trigger.group(2) or trigger.group(2).lower() not in allowed_states:
        options = ' / '.join(allowed_states)
        bot.reply('Available options: %s' % options)
        return

    channel = trigger.sender.lower()
    bot.db.set_channel_value(channel, 'safety', trigger.group(2).lower())
    bot.say('Safety is now set to "%s" on this channel' % trigger.group(2))


# Clean the cache every day
# Code above also calls this if there are too many cache entries
@plugin.interval(24 * 60 * 60)
def _clean_cache(bot):
    """Cleans up old entries in URL safety cache."""
    if bot.memory['safety_cache_lock'].acquire(False):
        LOGGER.info('Starting safety cache cleanup...')
        try:
            # clean up by age first
            cutoff = time.time() - (7 * 24 * 60 * 60)  # 7 days ago
            old_keys = []
            for key, data in tools.iteritems(bot.memory['safety_cache']):
                if data['fetched'] <= cutoff:
                    old_keys.append(key)
            for key in old_keys:
                bot.memory['safety_cache'].pop(key, None)

            # clean up more values if the cache is still too big
            overage = len(bot.memory['safety_cache']) - cache_limit
            if overage > 0:
                extra_keys = sorted(
                    (data.fetched, key)
                    for (key, data)
                    in bot.memory['safety_cache'].items())[:overage]
                for (_, key) in extra_keys:
                    bot.memory['safety_cache'].pop(key, None)
        finally:
            # No matter what errors happen (or not), release the lock
            bot.memory['safety_cache_lock'].release()

        LOGGER.info('Safety cache cleanup finished.')
    else:
        LOGGER.info(
            'Skipping safety cache cleanup: Cache is locked, '
            'cleanup already running.')
