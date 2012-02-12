"""
isup.py - Simple website status check with isup.me
Author: Edward Powell http://embolalia.net
About: http://inamidst.com/phenny/

This allows users to check if a website is up through isup.me.
"""

import web, re

def isup(jenni, input):
    """isup.me website status checker"""
    site = input.group(2)
    if not site:
        return jenni.reply("What site do you want to check?")
    uri = 'http://www.isup.me/' + site
    response = web.get(uri)
    result = re.search('(?:<title>)(http://\S* Is )(Down|Up)',\
                       response)
    if result:
        jenni.say(site + ' is ' + result.group(2))
    else:
        jenni.say('Couldn\'t read the result from isup.me -- sorry!')
isup.commands = ['isup']
