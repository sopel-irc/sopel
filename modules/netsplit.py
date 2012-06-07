#!/usr/bin/env python
"""
ping.py - jenni Ping Module
Author: Sean B. Palmer, inamidst.com
About: http://inamidst.com/phenny/
"""

import re

def netsplit(jenni, input):
    network = jenni.config.host.lstrip('irc')#A fair guess, I'd say.
    server = '\S+?'+network
    
    if not re.match(server+' '+server, input.group(1)): return
    jenni.msg('#Embo', 'Yarg, netsplit!')
netsplit.event = 'QUIT'
netsplit.rule = '(.*)'

if __name__ == '__main__': 
    print __doc__.strip()
