#!/usr/bin/env python
"""
scores.py - Rand Module
Author: Michael S. Yanovich http://opensource.cse.ohio-state.edu/
Phenny (About): http://inamidst.com/phenny/
"""

#
#       rand.py
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
import urllib2
from lxml import etree

def rand(phenny, input):
	""".rand <arg1> <arg2> - Generates a random integer between <arg1> and <arg2>."""
	if input.group(2) == " " or input.group(2) == "" or str(input.group(2)) == None or str(input.group(2)) == "" or input.group(2) == None:
		phenny.say("I'm sorry, " + str(input.nick) + ", but you must enter at least one number.")
	else:
		li_integers = input.group(2)
		li_integers_str = li_integers.split()
		if len(li_integers_str) == 1:
			if int(li_integers_str[0]) <= 1:
				a = li_integers_str[0]
				a = int(a)
				randinte = random.randint(a, 0)
			else:
				a = li_integers_str[0]
				a = int(a)
				randinte = random.randint(0, a)
			phenny.say(str(input.nick) + ": your random integer is: " + str(randinte))
		else:
			a,b = li_integers.split()
			a = int(a)
			b = int(b)
			if a <= b:
				randinte = random.randint(a, b)
			else:
				randinte = random.randint(b, a)
			phenny.say(str(input.nick) + ": your random integer is: " + str(randinte))
rand.commands = ['rand']
rand.priority = 'medium'

#def xkcd(phenny, input):
#	""".xkcd - Generates a url for a random XKCD clip."""
	#xkcdint = random.randint(0,673)
	#website = "http://xkcd.com/" + str(xkcdint) + "/"
#	website = "http://xkcd.com/%d/" % random.randint(0,673)
#	phenny.say(website)
#xkcd.commands = ['xkcd']

def xkcd(phenny, input):
        """.xkcd - Generates a url for a random XKCD clip."""
	#import urllib2
	#from lxml import etree

	body = urllib2.urlopen("http://xkcd.com/rss.xml").readlines()[1]
	parsed = etree.fromstring(body)
	newest = etree.tostring(parsed.findall("channel/item/link")[0])
	max_int = int(newest.split("/")[-3])
        website = "http://xkcd.com/%d/" % random.randint(0,max_int)
        phenny.say(website)
xkcd.commands = ['xkcd']


if __name__ == '__main__': 
	print __doc__.strip()
