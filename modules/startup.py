#!/usr/bin/env python
"""
startup.py - Phenny Startup Module
Copyright 2008, Sean B. Palmer, inamidst.com
Licensed under the Eiffel Forum License 2.

http://inamidst.com/phenny/
"""

def startup(phenny, input): 
   if hasattr(phenny.config, 'serverpass'): 
      phenny.write(('PASS', phenny.config.serverpass))

   if hasattr(phenny.config, 'password'): 
      phenny.msg('NickServ', 'IDENTIFY %s' % phenny.config.password)
      __import__('time').sleep(5)

   # Cf. http://swhack.com/logs/2005-12-05#T19-32-36
   for channel in phenny.channels: 
      phenny.write(('JOIN', channel))
startup.rule = r'(.*)'
startup.event = '251'
startup.priority = 'low'

if __name__ == '__main__': 
   print __doc__.strip()
