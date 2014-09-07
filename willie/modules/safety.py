# coding=utf8
"""
safety.py - Alerts about malicious URLs
Copyright © 2014, Elad Alfassa, <elad@fedoraproject.org>
Licensed under the Eiffel Forum License 2.

This module uses virustotal.com
"""
#TODO malwaredomains.com support
from __future__ import unicode_literals
import willie.web as web
from willie.config import ConfigurationError
from willie.formatting import color, bold
import willie.tools
import willie.module
import sys
import json
import time

if sys.version_info.major > 2:
    unicode = str

vt_base_api_url = 'https://www.virustotal.com/vtapi/v2/url/'


def configure(config):
    """

    | [safety] | example | purpose |
    | ---- | ------- | ------- |
    | enabled_by_default | True | Enable safety on implicity on channels |
    | vt_api_key | ea4ca709a686edfcc96a144c224935776e2ba46b77 | VirusTotal API key |
    """
    if config.option('Configure malicious URL protection'):
        config.add_section('safety')
        config.add_option('safety', 'enabled_by_default', 'Enable malicious URL checking for channels by default?', True)
        config.interactive_add('safety', 'vt_api_key', 'VirusTotal API Key (not mandatory)', None)


def setup(bot):
    if not bot.config.has_section('safety'):
        raise ConfigurationError("Safety module not configured")
    if bot.db and not bot.db.preferences.has_columns('safety'):
        bot.db.preferences.add_columns(['safety'])
    bot.memory['safety_cache'] = willie.tools.WillieMemory()


@willie.module.rule('(?u).*(https?://\S+).*')
def url_handler(bot, trigger):
    """ Check for malicious URLs """
    check = True  # Enable URL checking
    strict = False  # Strict mode: kick on malicious URL
    positives = 0  # Number of engines saying it's malicious
    total = 0  # Number of total engines
    if bot.config.has_section('safety'):
        check = bot.config.safety.enabled_by_default
        if check is None:
            # If not set, assume default
            check = True
        else:
            check = bool(check)
    # DB overrides config:
    if bot.db and trigger.sender.lower() in bot.db.preferences:
        setting = bot.db.preferences.get(trigger.sender.lower(), 'safety')
        if setting == 'off':
            return  # Not checking
        elif setting in ['on', 'strict']:
            check = True
        if setting == 'strict':
            strict = True

    if not check:
        return  # Not overriden by DB, configured default off

    apikey = bot.config.safety.vt_api_key
    if apikey is not None:
        payload = {'resource': unicode(trigger), 'apikey': apikey, 'scan': '1'}

        if trigger not in bot.memory['safety_cache']:
            result = web.post(vt_base_api_url+'report', payload)
            if sys.version_info.major > 2:
                result = result.decode('utf-8')
            result = json.loads(result)
            age = time.time()
            bot.memory['safety_cache'][trigger] = {'positives':
                                                   result['positives'],
                                                   'total': result['total'],
                                                   'age': age}
            if len(bot.memory['safety_cache']) > 1024:
                _clean_cache(bot)
        else:
            print('using cache')
            result = bot.memory['safety_cache'][trigger]
        positives = result['positives']
        total = result['total']
        perecent_sure = '{}%'.format(round((positives / total) * 100))

    if positives > 1:
        # Possibly malicious URL detected!
        msg = 'link posted by %s is possibliy malicious ' % bold(trigger.nick)
        msg += '(confidence %s - %s/%s)' % (perecent_sure, positives, total)
        bot.say('[' + bold(color('WARNING', 'red')) + '] ' + msg)
        if strict:
            bot.write(['KICK', trigger.sender, trigger.nick,
                       'Posted a malicious link'])


@willie.module.commands('safety')
def toggle_safety(bot, trigger):
    """ Toggle safety setting for channel """
    allowed_states = ['strict', 'on', 'off']
    if not trigger.group(2) or trigger.group(2).lower() not in allowed_states:
        bot.reply('Available options: strict / on /off')
        return
    if not bot.db:
        bot.reply('No database configured, can\'t modify settings')
        return
    if not trigger.isop and not trigger.admin:
        bot.reply('Only channel operators can change safety settings')

    channel = trigger.sender.lower()
    bot.db.preferences.update(channel, {'safety': trigger.group(2).lower()})
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
