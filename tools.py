#!/usr/bin/env python
# coding=utf-8
"""
tools.py - Willie misc tools
Copyright 2008, Sean B. Palmer, inamidst.com
Copyright © 2012, Elad Alfassa <elad@fedoraproject.org>
Licensed under the Eiffel Forum License 2.

https://willie.dftba.net
"""
import sys

def deprecated(old):
    def new(willie, input, old=old):
        self = willie
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
    
# from http://parand.com/say/index.php/2007/07/13/simple-multi-dimensional-dictionaries-in-python/
# A simple class to make mutli dimensional dict easy to use
class Ddict(dict):
    ''' A simple multi dimensional dict '''
    def __init__(self, default=None):
        self.default = default

    def __getitem__(self, key):
        if not self.has_key(key):
            self[key] = self.default()
        return dict.__getitem__(self, key)

def try_print(string):
    ''' Try printing to terminal, ignore errors '''
    try:
        print string
    except:
        pass
        
def try_print_stderr(string):
    ''' Try printing to stderr, ignore errors '''
    try:
        print >> sys.stderr, string
    except:
        pass
if __name__ == '__main__':
    print __doc__.strip()

