#!/usr/bin/env python
"""
yp.py - YourPants tools for Jenni
Copyright 2012 Edward Powell, http://embolalia.net
Licensed under the Eiffel Forum License 2.

More info:
 * Jenni: https://github.com/myano/jenni/
 * Phenny: http://inamidst.com/phenny/
"""

def profile(jenni, input):
    jenni.say('http://yourpants.org/members/'+ input.group(2) +'/profile')
profile.commands = ['yp','profile']

def chanstat(jenni,input):
	jenni.say('http://stats.nerdfighteria.net/')
chanstat.commands['chanstat','chanstats']