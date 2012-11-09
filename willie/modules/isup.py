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
    uri = 'http://www.isup.me/' + site
    try:
        response = web.get(uri)
    except Exception as e:
        willie.say(site + ' is ' + str(e))
        return
    result = re.search('(?:<title>)(http://\S* Is )(Down|Up)',\
                       response)
    if result:
        willie.say(site + ' is ' + result.group(2))
    else:
        willie.say('Couldn\'t read the result from isup.me -- sorry!')
isup.commands = ['isup']
