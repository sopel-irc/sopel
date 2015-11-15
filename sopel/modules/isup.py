# coding=utf-8
"""
isup.py - Simple website status check with isup.me
Author: Edward Powell http://embolalia.net
About: http://sopel.chat

This allows users to check if a website is up through isup.me.
"""
from __future__ import unicode_literals, absolute_import, print_function, division

from sopel import web
from sopel.module import commands


@commands('isup')
def isup(bot, trigger):
    """isup.me website status checker"""
    site = trigger.group(2)
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
        response = web.get(site)
    except Exception:
        bot.say(site + ' looks down from here.')
        return

    if response:
        bot.say(site + ' looks fine to me.')
    else:
        bot.say(site + ' is down from here.')
