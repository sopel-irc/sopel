#!/usr/bin/env python
"""
xkcd.py - XKCD Module
Copyright 2010, Michael Yanovich (yanovich.net), and Morgan Goose
Copyright 2012, Lior Ramati
Licensed under the Eiffel Forum License 2.

More info:
* Jenni: https://github.com/myano/jenni/
* Phenny: http://inamidst.com/phenny/
"""

import random
from search import google_search
from url import find_title
import urllib2
from lxml import etree

""".xkcd - Finds an xkcd comic strip. Takes one of 3 inputs:
If no input is provided it will return a random comic
If numeric input is provided it will return that comic
If non-numeric input is provided it will return the first google result for those keywords on the xkcd.com site"""
    
def xkcd(jenni, input):
    # get latest comic for rand function and numeric input
    body = urllib2.urlopen("http://xkcd.com/rss.xml").readlines()[1]
    parsed = etree.fromstring(body)
    newest = etree.tostring(parsed.findall("channel/item/link")[0])
    max_int = int(newest.split("/")[-3])

    # if no input is given (pre - FireRogue's edits code)
    if not input.group(2):
    	random.seed()
    	website = "http://xkcd.com/%d/" % random.randint(0,max_int+1)
    else:
        query = input.group(2)

        # numeric input!
        if (query.strip().isdigit()):
        	if (int(query.strip()) > max_int):
         		jenni.say("Sorry, comic #" + query.strip() + " hasn't been posted yet. The last comic was #%d" % max_int)
         		return
         	else: website = "http://xkcd.com/" + query.strip() + '/'
        
        # non-numeric input! code lifted from search.g
        else:
           try:
                query = query.encode('utf-8')
           except:
               pass
           website = google_search("site:xkcd.com "+ query)
    if website: # format and say result
        website += ' [' + find_title(website)[6:] + ']'
        jenni.say(website)
    elif website is False: jenni.say("Problem getting data from Google.")
    else: jenni.say("No results found for '%s'." % query)
xkcd.commands = ['xkcd']
xkcd.priority = 'low'

if __name__ == '__main__':
    print __doc__.strip()
