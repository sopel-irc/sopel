#!/usr/bin/env python
"""
unicode.py - Jenni Unicode Module
Author: Michael Yanovich, yanovich.net
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
