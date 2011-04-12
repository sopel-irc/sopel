#!/usr/bin/env python
"""
ham.py - Ham Radio Module
Author: Michael Yanovich - http://yanovich.net/
This contains a collection of lookups and calls for ham radio enthusiasts.
"""

import re
import web

re_look = re.compile('<FONT FACE="Arial, Helvetica, sans-serif" SIZE=4>(.*)<BR>')

def lookup(jenni, input):
    cs = input.group(2)
    link = "http://www.qth.com/callsign.php?cs=" + unicode(cs)
    page = web.get(link)
    name = re_look.findall(page)
    if name:
        jenni.say(name[0])
    else:
        jenni.say('No matches found')
lookup.commands = ['cs']

if __name__ == '__main__':
    print __doc__.strip()

