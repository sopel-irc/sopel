#!/usr/bin/env python
"""
tld.py - Jenni Why Module
Copyright 2009-10, Michael Yanovich, yanovich.net
Licensed under the Eiffel Forum License 2.

More info:
 * Jenni: https://github.com/myano/jenni/
 * Phenny: http://inamidst.com/phenny/
"""

import re, urllib2
import web

uri = 'https://en.wikipedia.org/wiki/List_of_Internet_top-level_domains'

def gettld(jenni, input):
    page = web.get(uri)
    #page = urllib2.urlopen(uri).read()
    search = r'(?i)<td><a href="\S+" title="\S+">\.{0}</a></td>\n<td>(\S+)</td>'
    search = search.format(input.group(2))
    re_country = re.compile(search)
    matches = re_country.findall(page)
    if matches:
        jenni.reply(matches[0])
    else:
        search = r'<td><a href="\S+" title="\S+">\.{0}</a></td>\n<td>.*\">(\S+)</a></td>'
        search = search.format(unicode(input.group(2)))
        re_country = re.compile(search)
        matches = re_country.findall(page)
        if matches:
            jenni.reply(matches[0])
        else:
            reply = "No matches found for TLD: {0}".format(unicode(input.group(2)))
            jenni.reply(reply)
gettld.commands = ['tld']
gettld.thread = False

if __name__ == '__main__':
    print __doc__.strip()
