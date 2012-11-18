"""
xkcd.py - XKCD Module
Copyright 2010, Michael Yanovich (yanovich.net), and Morgan Goose
Copyright 2012, Lior Ramati
Licensed under the Eiffel Forum License 2.

http://willie.dftba.net
"""

import random
from willie.modules.search import google_search
from willie.modules.url import find_title
import urllib2
from lxml import etree
import re

def xkcd(willie, trigger):
    """
    .xkcd - Finds an xkcd comic strip. Takes one of 3 inputs:
    If no input is provided it will return a random comic
    If numeric input is provided it will return that comic
    If non-numeric input is provided it will return the first google result for those keywords on the xkcd.com site
    """
    # get latest comic for rand function and numeric input
    body = urllib2.urlopen("http://xkcd.com/rss.xml").readlines()[1]
    parsed = etree.fromstring(body)
    newest = etree.tostring(parsed.findall("channel/item/link")[0])
    max_int = int(newest.split("/")[-3])

    # if no input is given (pre - lior's edits code)
    if not trigger.group(2): # get rand comic
        random.seed()
        website = "http://xkcd.com/%d/" % random.randint(0,max_int+1)
    else:
        query = trigger.group(2).strip()

        # numeric input! get that comic number if it exists
        if (query.isdigit()):
            if (int(query) > max_int):
                willie.say("Sorry, comic #" + query + " hasn't been posted yet. The last comic was #%d" % max_int)
                return
            else: website = "http://xkcd.com/" + query
        
        # non-numeric input! code lifted from search.g
        else:
            if (query.lower() == "latest" or query.lower() == "newest"): # special commands
                website = "https://xkcd.com/"
            else: # just google
                try:
                    query = query.encode('utf-8')
                except:
                    pass
                website = google_search("site:xkcd.com "+ query)
                chkForum = re.match(re.compile(r'.*?([0-9].*?):.*'), find_title(website)) # regex for comic specific forum threads
                if (chkForum):
                    website = "http://xkcd.com/" + chkForum.groups()[0].lstrip('0')
    if website: # format and say result
        website += ' [' + find_title(website)[6:] + ']'
        willie.say(website)
    elif website is False: willie.say("Problem getting data from Google.")
    else: willie.say("No results found for '%s'." % query)
xkcd.commands = ['xkcd']
xkcd.priority = 'low'

if __name__ == '__main__':
    print __doc__.strip()
