"""
isup.py - Simple website status check with isup.me
Author: Edward Powell http://embolalia.net
About: http://willie.dftba.net

This allows users to check if a website is up through isup.me.
"""

import willie.web as web
import re

def isup(willie, trigger):
    """isup.me website status checker"""
    site = trigger.group(2)
    if not site:
        return willie.reply("What site do you want to check?")

    if site[:6] != 'http://' and site[:7] != 'https://':
        if '://' in site:
            protocol = site.split('://')[0] + '://'
            return willie.reply("Try it again without the %s" % protocol)
        else:
            site = 'http://' + site
    try:
        response = web.get(site)
    except Exception as e:
        willie.say(site + ' looks down from here.')
        return

    if response:
        willie.say(site + ' looks fine to me.')
    else:
        willie.say(site + ' is down from here.')
isup.commands = ['isup']
