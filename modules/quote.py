#!/usr/bin/env python
"""
quote.py - Jenni Quote Module
Copyright 2008-10, Michael Yanovich, yanovich.net
Licensed under the Eiffel Forum License 2.

More info:
 * Jenni: https://github.com/myano/jenni/
 * Phenny: http://inamidst.com/phenny/
"""

import random
import re
import web

quoteuri = 'http://www.randomquotes.org/'
r_qa = re.compile(r'(?i)<p><a href="\S+">(.*)</a><br />.*\n.*">(.*)</a></p>')


def getquote(jenni, input):
    page = web.get(quoteuri)
    quotes = r_qa.findall(page)
    random.seed()
    item = random.randint(0, len(quotes))
    quote = quotes[item]
    response = '"%s" -- %s' % (quote[0], quote[1])
    jenni.reply(response)
getquote.commands = ['q']
getquote.priority = 'medium'
getquote.example = '.q'
getquote.rate = 30

if __name__ == '__main__':
    print __doc__.strip()
