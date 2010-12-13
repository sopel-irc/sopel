#!/usr/bin/env python
"""
startup.py - Jenni Startup Module
Copyright 2008, Sean B. Palmer, inamidst.com
Licensed under the Eiffel Forum License 2.

http://inamidst.com/phenny/
"""

def startup(jenni, input): 
	if hasattr(jenni.config, 'serverpass'): 
		jenni.write(('PASS', jenni.config.serverpass))

	if hasattr(jenni.config, 'password'): 
		jenni.msg('NickServ', 'IDENTIFY %s' % jenni.config.password)
		__import__('time').sleep(5)

	# Cf. http://swhack.com/logs/2005-12-05#T19-32-36
	for channel in jenni.channels: 
		jenni.write(('JOIN', channel))
startup.rule = r'(.*)'
startup.event = '251'
startup.priority = 'low'

if __name__ == '__main__': 
	print __doc__.strip()
