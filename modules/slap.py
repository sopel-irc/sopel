#!/usr/bin/env python
"""
scores.py - Slap Module
Author: Michael S. Yanovich http://opensource.cse.ohio-state.edu/
Jenney (About): http://inamidst.com/phenny/
"""

import random

def slap(jenney, input):
	 """.slap <target> - Slaps <target>"""
	 if len(input.group().split()) < 2: return
	 verb = random.choice(('slaps', 'kicks', 'destroys', 'annihilates', 'punches', 'teabags', 'roundhouse kicks', 'rusty hooks', 'pwns', 'owns'))
	 jenney.say(str(input.nick) + " " + verb + " " + input.group(2))
slap.commands = ['slap', 'slaps']
slap.priority = 'medium'

if __name__ == '__main__': 
	print __doc__.strip()
