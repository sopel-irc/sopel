#!/usr/bin/env python
"""
startup.py - Jenney Startup Module
Copyright 2008, Sean B. Palmer, inamidst.com
Licensed under the Eiffel Forum License 2.

http://inamidst.com/phenny/
"""

def startup(jenney, input): 
	if hasattr(jenney.config, 'serverpass'): 
		jenney.write(('PASS', jenney.config.serverpass))

	if hasattr(jenney.config, 'password'): 
		jenney.msg('NickServ', 'IDENTIFY %s' % jenney.config.password)
		__import__('time').sleep(5)

	# Cf. http://swhack.com/logs/2005-12-05#T19-32-36
	for channel in jenney.channels: 
		jenney.write(('JOIN', channel))
startup.rule = r'(.*)'
startup.event = '251'
startup.priority = 'low'

if __name__ == '__main__': 
	print __doc__.strip()
