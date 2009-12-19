#!/usr/bin/env python
"""
xkcd.py - XKCD Module
Author: Michael S. Yanovich http://opensource.cse.ohio-state.edu/
Phenny (About): http://inamidst.com/phenny/
"""

#
#       xkcd.py
#       
#       Copyright 2009 Michael S. Yanovich
#       
#       This program is free software; you can redistribute it and/or modify
#       it under the terms of the GNU General Public License as published by
#       the Free Software Foundation; either version 3 of the License, or
#       (at your option) any later version.
#       
#       This program is distributed in the hope that it will be useful,
#       but WITHOUT ANY WARRANTY; without even the implied warranty of
#       MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#       GNU General Public License for more details.
#       
#       You should have received a copy of the GNU General Public License
#       along with this program; if not, write to the Free Software
#       Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#       MA 02110-1301, USA.

import random

def xkcd(phenny, input):
   """.xkcd - Generates a url for a random XKCD clip."""
   #import urllib2
   #from lxml import etree

   #body = urllib2.urlopen("http://xkcd.com/rss.xml").readlines()[1]
   #parsed = etree.fromstring(body)
   #newest = etree.tostring(parsed.findall("channel/item/link")[0])
   #max_int = int(newest.split("/")[-3])
   #website = "http://xkcd.com/%d/" % random.randint(0,max_int)
   #phenny.say(website)

   website = "http://xkcd.com/%d/" % random.randint(0,673)
   phenny.say(website)
xkcd.commands = ['xkcd']

if __name__ == '__main__': 
   print __doc__.strip()
