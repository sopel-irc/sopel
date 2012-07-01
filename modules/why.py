#!/usr/bin/env python
"""
why.py - Jenni Why Module
Copyright 2009-10, Michael Yanovich, yanovich.net
Licensed under the Eiffel Forum License 2.

More info:
 * Jenni: https://github.com/myano/jenni/
 * Phenny: http://inamidst.com/phenny/
"""

import re
import web

whyuri = 'http://www.leonatkinson.com/random/index.php/rest.html?method=advice'
r_paragraph = re.compile(r'<quote>.*?</quote>')


def getwhy(jenni, input):
    page = web.get(whyuri)
    paragraphs = r_paragraph.findall(page)
    line = re.sub(r'<[^>]*?>', '', unicode(paragraphs[0]))
    jenni.say(line.lower().capitalize() + ".")
getwhy.commands = ['why', 'tubbs']
getwhy.thread = False
getwhy.rate = 30

if __name__ == '__main__':
    print __doc__.strip()
