#!/usr/bin/env python
"""
why.py - Jenni Why Module
Copyright 2009-10, Michael Yanovich, opensource.osu.edu/~yanovich/wiki/
Licensed under the Eiffel Forum License 2.

http://inamidst.com/phenny/
"""

import re, urllib
import web

whyuri = 'http://www.leonatkinson.com/random/index.php/rest.html?method=advice'
r_paragraph = re.compile(r'<quote>.*?</quote>')

def getwhy(jenni, input):
    global whyuri
    global r_paragraph
    bytes = web.get(whyuri)
    paragraphs = r_paragraph.findall(bytes)
    line = re.sub(r'<[^>]*?>', '', str(paragraphs[0]))
    jenni.say(line.lower().capitalize() + ".")
getwhy.commands = ['why']
getwhy.thread = False

def getwhy2(jenni, input):
    getwhy(jenni, input)
getwhy2.commands = ['tubbs']
getwhy2.thread = False

if __name__ == '__main__':
    print __doc__.strip()
