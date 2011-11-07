#!/usr/bin/env python
"""
latex.py - Jenni LaTeX Module
Copyright 2011, Michael Yanovich, yanovich.net
Licensed under the Eiffel Forum License 2.

More info:
 * Jenni: https://github.com/myano/jenni/
 * Phenny: http://inamidst.com/phenny/
"""

import web

uri = 'http://latex.codecogs.com/gif.latex?'

def latex(jenni, input):
    text = input.group(2)
    text = text.replace(" ", "%20")
    url = "http://tinyurl.com/api-create.php?url={0}".format(uri + text)
    a = web.get(url)
    jenni.reply(a)
latex.commands = ['tex']
latex.priority = 'high'

if __name__ == '__main__':
    print __doc__.strip()
