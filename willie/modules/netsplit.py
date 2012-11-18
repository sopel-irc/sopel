"""
netsplit.py - Message the debug channel on a netsplit.
Author: Edward Powell - embolalia.net

http://willie.dftba.net
"""

import re

def netsplit(willie, trigger):
    network = willie.config.host.lstrip('irc')#A fair guess, I'd say.
    server = '\S+?'+network
    
    if not re.match(server+' '+server, trigger.group(1)): return
    willie.debug('Netsplit', 'Yarg, netsplit!', 'warning')
netsplit.event = 'QUIT'
netsplit.rule = '(.*)'

if __name__ == '__main__': 
    print __doc__.strip()
