# coding=utf8
"""
safety.py - Alerts about malicious URLs
Copyright © 2014, Elad Alfassa, <elad@fedoraproject.org>
Licensed under the Eiffel Forum License 2.

This module uses virustotal.com
"""
from __future__ import unicode_literals
from __future__ import print_function
import willie.web as web
from willie.config import ConfigurationError
from willie.formatting import color, bold
from willie.logger import get_logger
import willie.tools
import willie.module
import sys
import json
import time
import os.path
import re

if sys.version_info.major > 2:
    unicode = str
    from urllib.request import urlretrieve
    from urllib.parse import urlparse
else:
    from urllib import urlretrieve
    from urlparse import urlparse

LOGGER = get_logger(__name__)

vt_base_api_url = 'https://www.virustotal.com/vtapi/v2/url/'
malware_domains = []
known_good = []


def configure(config):
    """

    | [safety] | example | purpose |
    | ---- | ------- | ------- |
    | enabled_by_default | True | Enable safety on implicity on channels |
    | vt_api_key | ea4ca709a686edfcc96a144c224935776e2ba46b77 | VirusTotal API key |
    | known_good | youtube.com,vimeo.com,.*\.tumblr.com | list of "known good" domains to ignore |
    """
    if config.option('Configure malicious URL protection?'):
        config.add_section('safety')
        config.add_option('safety', 'enabled_by_default', 'Enable malicious URL checking for channels by default?', True)
        config.interactive_add('safety', 'vt_api_key', 'VirusTotal API Key (not mandatory)', None)


def setup(bot):
    if not bot.config.has_section('safety'):
        raise ConfigurationError("Safety module not configured")
    bot.memory['safety_cache'] = willie.tools.WillieMemory()
    for item in bot.config.safety.get_list('known_good'):
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
            malware_domains.append(unicode(line).strip().lower())


def _download_malwaredomains_db(path):
    print('Downloading malwaredomains db...')
    urlretrieve('http://mirror1.malwaredomains.com/files/justdomains', path)


@willie.module.rule('(?u).*(https?://\S+).*')
@willie.module.priority('high')
def url_handler(bot, trigger):
    """ Check for malicious URLs """
    check = True    # Enable URL checking
    strict = False  # Strict mode: kick on malicious URL
    positives = 0   # Number of engines saying it's malicious
    total = 0       # Number of total engines
    use_vt = True   # Use VirusTotal
    if bot.config.has_section('safety'):
        check = bot.config.safety.enabled_by_default
        if check is None:
            # If not set, assume default
            check = True
        else:
            check = bool(check)
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

    netloc = urlparse(trigger).netloc
    if any(regex.search(netloc) for regex in known_good):
        return  # Whitelisted

    apikey = bot.config.safety.vt_api_key
    try:
        if apikey is not None and use_vt:
            payload = {'resource': unicode(trigger),
                       'apikey': apikey,
                       'scan': '1'}

            if trigger not in bot.memory['safety_cache']:
                result = web.post(vt_base_api_url + 'report', payload)
                if sys.version_info.major > 2:
                    result = result.decode('utf-8')
                result = json.loads(result)
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
    except Exception as e:
        LOGGER.debug('Error from checking URL with VT.', exc_info=True)
        pass  # Ignoring exceptions with VT so MalwareDomains will always work

    if unicode(netloc).lower() in malware_domains:
        # malwaredomains is more trustworthy than some VT engines
        # therefor it gets a weight of 10 engines when calculating confidence
        positives += 10
        total += 10

    if positives > 1:
        # Possibly malicious URL detected!
        confidence = '{}%'.format(round((positives / total) * 100))
        msg = 'link posted by %s is possibliy malicious ' % bold(trigger.nick)
        msg += '(confidence %s - %s/%s)' % (confidence, positives, total)
        bot.say('[' + bold(color('WARNING', 'red')) + '] ' + msg)
        if strict:
            bot.write(['KICK', trigger.sender, trigger.nick,
                       'Posted a malicious link'])


@willie.module.commands('safety')
def toggle_safety(bot, trigger):
    """ Set safety setting for channel """
    allowed_states = ['strict', 'on', 'off', 'local', 'local strict']
    if not trigger.group(2) or trigger.group(2).lower() not in allowed_states:
        options = ' / '.join(allowed_states)
        bot.reply('Available options: %s' % options)
        return
    if not trigger.isop and not trigger.admin:
        bot.reply('Only channel operators can change safety settings')

    channel = trigger.sender.lower()
    bot.db.set_channel_value(channel, 'safety', trigger.group(2).lower())
    bot.reply('Safety is now set to %s in this channel' % trigger.group(2))


# Clean the cache every day, also when > 1024 entries
@willie.module.interval(24 * 60 * 60)
def _clean_cache(bot):
    """ Cleanup old entries in URL cache """
    # TODO probably should be using locks here, to make sure stuff doesn't
    # explode
    oldest_key_age = 0
    oldest_key = ''
    for key, data in willie.tools.iteritems(bot.memory['safety_cache']):
        if data['age'] > oldest_key_age:
            oldest_key_age = data['age']
            oldest_key = key
    if oldest_key in bot.memory['safety_cache']:
        del bot.memory['safety_cache'][oldest_key]
