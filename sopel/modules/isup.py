# coding=utf-8
"""Simple website status check with isup.me"""
# Author: Elsie Powell http://embolalia.com
from __future__ import unicode_literals, absolute_import, print_function, division

import requests
from sopel.module import commands

from requests.exceptions import SSLError


@commands('isup', 'isupinsecure')
def isup(bot, trigger):
    """isup.me website status checker"""
    site = trigger.group(2)
    secure = trigger.group(1).lower() != 'isupinsecure'
    if not site:
        return bot.reply("What site do you want to check?")

    if site[:7] != 'http://' and site[:8] != 'https://':
        if '://' in site:
            protocol = site.split('://')[0] + '://'
            return bot.reply("Try it again without the %s" % protocol)
        else:
            site = 'http://' + site

    if not '.' in site:
        site += ".com"

    try:
        response = requests.head(site, verify=secure).headers
    except SSLError:
        bot.say(site + ' looks down from here. Try using %sisupinsecure' % bot.config.core.help_prefix)
        return
    except Exception:
        bot.say(site + ' looks down from here.')
        return

    if response:
        bot.say(site + ' looks fine to me.')
    else:
        bot.say(site + ' is down from here.')
