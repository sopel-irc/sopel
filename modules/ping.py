#!/usr/bin/env python
"""
ping.py - Jenney Ping Module
Author: Sean B. Palmer, inamidst.com
Modified by: Michael S. Yanovich
About: http://inamidst.com/phenny/
"""

import random

def interjection(jenney, input): 
	jenney.say(input.nick + '!')
interjection.rule = r'($nickname!)'
interjection.priority = 'high'
interjection.thread = False

if __name__ == '__main__': 
	print __doc__.strip()
