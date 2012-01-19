#!/usr/bin/env python
"""
startup.py - Jenni Startup Module
Copyright 2008, Sean B. Palmer, inamidst.com
Licensed under the Eiffel Forum License 2.

http://inamidst.com/phenny/
"""
import re

def startup(jenni, input):
    if hasattr(jenni.config, 'serverpass'):
        jenni.write(('PASS', jenni.config.serverpass))

    if hasattr(jenni.config, 'password'):
        jenni.msg('NickServ', 'IDENTIFY %s' % jenni.config.password)
        __import__('time').sleep(5)

    # Cf. http://swhack.com/logs/2005-12-05#T19-32-36
    for channel in jenni.channels:
        jenni.write(('JOIN', channel))
        
    #Attempt to set bot mode.
    jenni.write(('MODE ', jenni.nick + ' +B'))
startup.rule = r'(.*)'
startup.event = '251'
startup.priority = 'low'



#Functions to maintain a list of chanops in all of jenni's channels.
def refreshList(jenni, input):
    input.flushOps(input.channel)
    if input.admin: jenni.write(('NAMES', input.channel))
refreshList.commands = ['.oplist']

def handleNames(jenni, input):
    jenni.msg(input.devchan, 'input group 1: '+input.group(1))
    names = re.split(' ', input.group(1))
    print jenni.raw
    channel = re.search('(#\S+)', jenni.raw).group(1)
    jenni.msg(input.devchan, 'channel: '+channel)
    for name in names:
        if '@' in name or '~' in name or '&' in name:
            jenni.addOp(channel, name.lstrip('@&%+~'))
        if '%' in name:
            jenni.addHalfOp(channel, name.lstrip('@&%+~'))
    jenni.msg(input.devchan, 'ops and halfplus: '+str(jenni.ops)+'   '+str(jenni.halfplus))
handleNames.rule = r'(.*)'
handleNames.event = '353'

if __name__ == '__main__':
    print __doc__.strip()
