#!/usr/bin/env python
"""
xkcd.py - XKCD Module
Author: Michael S. Yanovich and Goose Morgan http://opensource.cse.ohio-state.edu/
Jenni (About): http://inamidst.com/phenny/
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

if __name__ == '__main__': 
	print __doc__.strip()
