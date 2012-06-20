#!/usr/bin/env python
"""
xkcd.py - XKCD Module
Copyright 2010, Michael Yanovich (yanovich.net), and Morgan Goose
Licensed under the Eiffel Forum License 2.

More info:
 * Jenni: https://github.com/myano/jenni/
 * Phenny: http://inamidst.com/phenny/
"""

import random

random.seed()

def xkcd(jenni, input):
    """.xkcd - Generates a url for a random XKCD clip."""
    import urllib2
    from lxml import etree

    body = urllib2.urlopen("http://xkcd.com/rss.xml").readlines()[1]
    parsed = etree.fromstring(body)
    newest = etree.tostring(parsed.findall("channel/item/link")[0])
    max_int = int(newest.split("/")[-3])
    website = "http://xkcd.com/%d/" % random.randint(0,max_int+1)
    jenni.say(website)
xkcd.commands = ['xkcd']
xkcd.priority = 'low'
xkcd.rate = 30

if __name__ == '__main__':
    print __doc__.strip()
