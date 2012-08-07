#!/usr/bin/env python
"""
yp.py - YourPants tools for Jenni
Copyright 2012 Edward Powell, http://embolalia.net
Licensed under the Eiffel Forum License 2.

More info:
 * Jenni: https://github.com/myano/jenni/
 * Phenny: http://inamidst.com/phenny/
"""
import web, re

def profile(jenni, input):
    name = input.group(2)
    if name:
        url = 'http://yourpants.org/members/' + name + '/profile'
        response = web.get(url)
        result = re.search('<title>Page not found',\
                       response)
        if not result: jenni.say(url)
profile.commands = ['yp','profile']

def ning(jenni, input):
    jenni.say('http://nerdfighters.ning.com/profile/'+ input.group(2))
ning.commands = ['ning']
