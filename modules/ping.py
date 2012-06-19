#!/usr/bin/env python
"""
ping.py - Jenni Ping Module
Author: Sean B. Palmer, inamidst.com
Modified by: Michael Yanovich
About: http://inamidst.com/phenny/
"""

import random

def interjection(jenni, input):
    jenni.say(input.nick + '!')
interjection.rule = r'($nickname!)'
interjection.priority = 'high'
interjection.thread = False
interjection.rate = 30

if __name__ == '__main__':
    print __doc__.strip()
