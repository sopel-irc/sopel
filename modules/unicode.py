#!/usr/bin/env python
"""
unicode.py - Jenni Unicode Module
Copyright 2010, Michael Yanovich, yanovich.net
Licensed under the Eiffel Forum License 2.

More info:
 * Jenni: https://github.com/myano/jenni/
 * Phenny: http://inamidst.com/phenny/
"""

def meh (jenni, input):
    import unicodedata
    s = 'u'
    for i in xrange(1,3000):
        if unicodedata.category(unichr(i)) == "Mn":
            s += unichr(i)
        if len(s) > 100:
            break
    jenni.say(s)
meh.commands = ['sc']

if __name__ == '__main__':
    print __doc__.strip()
