#!/usr/bin/env python
"""
why.py - Jenni Why Module
Copyright 2009-10, Michael Yanovich, opensource.osu.edu/~yanovich/wiki/
Licensed under the Eiffel Forum License 2.

http://inamidst.com/phenny/
"""

import re, urllib
import web

whyuri = 'http://www.leonatkinson.com/random/index.php/lyrics.html'
r_paragraph = re.compile(r'(?ims)<tr><td bgcolor=".*?">.*?</td></tr>')

def getwhy(jenni, input):
	global whyuri
	global r_paragraph
	bytes = web.get(whyuri)
	paragraphs = r_paragraph.findall(bytes)
	line = re.sub(r'<[^>]*?>', '', str(paragraphs[1]))
	jenni.say(line)
getwhy.commands = ['why']
getwhy.priority = 'high'

if __name__ == '__main__':
	print __doc__.strip()
