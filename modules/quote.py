#!/usr/bin/env python
"""
quote.py - Jenni Quote Module
Copyright 2008-10, Michael Yanovich, opensource.osu.edu/~yanovich/wiki/
Licensed under the Eiffel Forum License 2.

http://inamidst.com/phenny/
"""

import re, urllib
import web

quoteuri = 'http://www.quotationspage.com/random.php3'
r_paragraph = re.compile(r'(?ims)<dt class="quote">.*?</dt>')
r_author = re.compile(r'(?ims)<dd class="author">.*?</dt>')
r_authorb = re.compile(r'(?ims)<b>.*</b>')

def getquote(jenni, input):
	global quoteuri
	global cleanup
	bytes = web.get(quoteuri)
	paragraphs = r_paragraph.findall(bytes)
	author_para = r_author.findall(bytes)
	author_para_b = r_authorb.findall(author_para[0])
	quote = re.sub(r'<[^>]*?>', '', str(paragraphs[0]))
	author_para_b =  re.sub(r'<[^>]*?>', '', author_para_b[0])
	quote += "-- " + author_para_b
	jenni.say(quote)
getquote.commands = ['q']
getquote.priority = 'medium'
getquote.example = '.q'

if __name__ == '__main__':
	print __doc__.strip()
