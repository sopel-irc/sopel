#!/usr/bin/env python
"""
ping.py - Phenny Ping Module
Author: Sean B. Palmer, inamidst.com
Modified by: Michael S. Yanovich
About: http://inamidst.com/phenny/
"""

import random

def interjection(phenny, input): 
	phenny.say(input.nick + '!')
interjection.rule = r'($nickname!|phenny!)'
interjection.priority = 'high'
interjection.thread = False

if __name__ == '__main__': 
	print __doc__.strip()
