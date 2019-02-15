# coding=utf-8
"""
safety.py - Alerts about malicious URLs
Copyright © 2014, Elad Alfassa, <elad@fedoraproject.org>
Licensed under the Eiffel Forum License 2.

This module uses virustotal.com
"""
from __future__ import unicode_literals, absolute_import, print_function, division

from sopel.config.types import StaticSection, ValidatedAttribute, ListAttribute
from sopel.formatting import color, bold
from sopel.logger import get_logger
from sopel.module import OP
import sopel.tools
import sys
import time
import os.path
import re
import requests

try:
    # This is done separately from the below version if/else because JSONDecodeError
    # didn't appear until Python 3.5, but Sopel claims support for 3.3+
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

LOGGER = get_logger(__name__)

vt_base_api_url = 'https://www.virustotal.com/vtapi/v2/url/'
malware_domains = set()
known_good = []


class SafetySection(StaticSection):
    enabled_by_default = ValidatedAttribute('enabled_by_default', bool, default=True)
    """Enable URL safety in all channels where it isn't explicitly disabled."""
    known_good = ListAttribute('known_good')
    """List of "known good" domains to ignore."""
    vt_api_key = ValidatedAttribute('vt_api_key')
    """Optional VirusTotal API key."""


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
        "protection.\nOtherwise, only the Malwarebytes DB will be used."
    )


def setup(bot):
    bot.config.define_section('safety', SafetySection)

    bot.memory['safety_cache'] = sopel.tools.SopelMemory()
    for item in bot.config.safety.known_good:
        known_good.append(re.compile(item, re.I))

    loc = os.path.join(bot.config.homedir, 'malwaredomains.txt')
    if os.path.isfile(loc):
        if os.path.getmtime(loc) < time.time() - 24 * 60 * 60 * 7:
            # File exists but older than one week, update
            _download_malwaredomains_db(loc)
    else:
        _download_malwaredomains_db(loc)
    with open(loc, 'r') as f:
        for line in f:
            clean_line = unicode(line).strip().lower()
            if clean_line != '':
                malware_domains.add(clean_line)


def _download_malwaredomains_db(path):
    print('Downloading malwaredomains db...')
    urlretrieve('https://mirror1.malwaredomains.com/files/justdomains', path)


@sopel.module.rule(r'(?u).*(https?://\S+).*')
@sopel.module.priority('high')
def url_handler(bot, trigger):
    """ Check for malicious URLs """
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
        return  # Not overriden by DB, configured default off

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
                age = time.time()
                data = {'positives': result['positives'],
                        'total': result['total'],
                        'age': age}
                bot.memory['safety_cache'][trigger] = data
                if len(bot.memory['safety_cache']) > 1024:
                    _clean_cache(bot)
            else:
                print('using cache')
                result = bot.memory['safety_cache'][trigger]
            positives = result['positives']
            total = result['total']
    except requests.exceptions.RequestException:
        LOGGER.debug('[VirusTotal] Error obtaining response.', exc_info=True)
        pass  # Ignoring exceptions with VT so MalwareDomains will always work
    except InvalidJSONResponse:
        LOGGER.debug('[VirusTotal] Malformed response (invalid JSON).', exc_info=True)
        pass  # Ignoring exceptions with VT so MalwareDomains will always work

    if unicode(netloc).lower() in malware_domains:
        # malwaredomains is more trustworthy than some VT engines
        # therefor it gets a weight of 10 engines when calculating confidence
        positives += 10
        total += 10

    if positives > 1:
        # Possibly malicious URL detected!
        confidence = '{}%'.format(round((positives / total) * 100))
        msg = 'link posted by %s is possibly malicious ' % bold(trigger.nick)
        msg += '(confidence %s - %s/%s)' % (confidence, positives, total)
        bot.say('[' + bold(color('WARNING', 'red')) + '] ' + msg)
        if strict:
            bot.write(['KICK', trigger.sender, trigger.nick,
                       'Posted a malicious link'])


@sopel.module.commands('safety')
def toggle_safety(bot, trigger):
    """ Set safety setting for channel """
    if not trigger.admin and bot.channels[trigger.sender].privileges[trigger.nick] < OP:
        bot.reply('Only channel operators can change safety settings')
        return
    allowed_states = ['strict', 'on', 'off', 'local', 'local strict']
    if not trigger.group(2) or trigger.group(2).lower() not in allowed_states:
        options = ' / '.join(allowed_states)
        bot.reply('Available options: %s' % options)
        return

    channel = trigger.sender.lower()
    bot.db.set_channel_value(channel, 'safety', trigger.group(2).lower())
    bot.reply('Safety is now set to "%s" on this channel' % trigger.group(2))


# Clean the cache every day, also when > 1024 entries
@sopel.module.interval(24 * 60 * 60)
def _clean_cache(bot):
    """ Cleanup old entries in URL cache """
    # TODO probably should be using locks here, to make sure stuff doesn't
    # explode
    oldest_key_age = 0
    oldest_key = ''
    for key, data in sopel.tools.iteritems(bot.memory['safety_cache']):
        if data['age'] > oldest_key_age:
            oldest_key_age = data['age']
            oldest_key = key
    if oldest_key in bot.memory['safety_cache']:
        del bot.memory['safety_cache'][oldest_key]
