#!/usr/bin/env python
"""
ham.py - Ham Radio Module
Copyright 2011, Michael Yanovich, yanovich.net
Licensed under the Eiffel Forum License 2.

More info:
 * Jenni: https://github.com/myano/jenni/
 * Phenny: http://inamidst.com/phenny/

This contains a collection of lookups and calls for ham radio enthusiasts.
"""

import re
import web

re_look = re.compile('<FONT FACE="Arial, Helvetica, sans-serif" SIZE=4>(.*)<BR>')

def lookup(jenni, input):
    cs = input.group(2).upper()
    link = "http://www.qth.com/callsign.php?cs=" + unicode(cs)
    page = web.get(link)
    name = re_look.findall(page)
    if name:
        jenni.say("Name: " + name[0] + ", more information available at: " + link)
    else:
        jenni.say('No matches found')
lookup.commands = ['cs']

if __name__ == '__main__':
    print __doc__.strip()

