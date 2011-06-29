#!/usr/bin/env python
"""
tools.py - Jenni Tools
Copyright 2008, Sean B. Palmer, inamidst.com
Licensed under the Eiffel Forum License 2.

http://inamidst.com/phenny/
"""

def deprecated(old):
    def new(jenni, input, old=old):
        self = jenni
        origin = type('Origin', (object,), {
            'sender': input.sender,
            'nick': input.nick
        })()
        match = input.match
        args = [input.bytes, input.sender, '@@']

        old(self, origin, match, args)
    new.__module__ = old.__module__
    new.__name__ = old.__name__
    return new

if __name__ == '__main__':
    print __doc__.strip()

