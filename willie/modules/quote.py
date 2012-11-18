"""
quote.py - Willie Quote Module
Copyright 2008-10, Michael Yanovich, yanovich.net
Licensed under the Eiffel Forum License 2.

http://willie.dftba.net
"""

import random
import re
import willie.web as web

quoteuri = 'http://www.randomquotes.org/'
r_qa = re.compile(r'(?i)<p><a href="\S+">(.*)</a><br />.*\n.*">(.*)</a></p>')


def getquote(willie, trigger):
    """Show a random quote."""
    page = web.get(quoteuri)
    quotes = r_qa.findall(page)
    random.seed()
    item = random.randint(0, len(quotes)-1)
    quote = quotes[item]
    response = '"%s" -- %s' % (quote[0], quote[1])
    willie.reply(response)
getquote.commands = ['q']
getquote.priority = 'medium'
getquote.example = '.q'

if __name__ == '__main__':
    print __doc__.strip()
