#!/usr/bin/env python
"""
startup.py - Jenni Startup Module
Copyright 2008, Sean B. Palmer, inamidst.com
Licensed under the Eiffel Forum License 2.

More info:
 * Jenni: https://github.com/myano/jenni/
 * Phenny: http://inamidst.com/phenny/
"""
import re

import threading, time

def setup(jenni):
    # by clsn
    jenni.data = {}
    refresh_delay = 300.0

    if hasattr(jenni.config, 'refresh_delay'):
        try: refresh_delay = float(jenni.config.refresh_delay)
        except: pass

        def close():
            print "Nobody PONGed our PING, restarting"
            jenni.handle_close()

        def pingloop():
            timer = threading.Timer(refresh_delay, close, ())
            jenni.data['startup.setup.timer'] = timer
            jenni.data['startup.setup.timer'].start()
            # print "PING!"
            jenni.write(('PING', jenni.config.host))
        jenni.data['startup.setup.pingloop'] = pingloop

        def pong(jenni, input):
            try:
                # print "PONG!"
                jenni.data['startup.setup.timer'].cancel()
                time.sleep(refresh_delay + 60.0)
                pingloop()
            except: pass
        pong.event = 'PONG'
        pong.thread = True
        pong.rule = r'.*'
        jenni.variables['pong'] = pong

        # Need to wrap handle_connect to start the loop.
        inner_handle_connect = jenni.handle_connect

        def outer_handle_connect():
            inner_handle_connect()
            if jenni.data.get('startup.setup.pingloop'):
                jenni.data['startup.setup.pingloop']()

        jenni.handle_connect = outer_handle_connect

def startup(jenni, input):
    if hasattr(jenni.config, 'serverpass'):
        jenni.write(('PASS', jenni.config.serverpass))

    if hasattr(jenni.config, 'password'):
        jenni.msg('NickServ', 'IDENTIFY %s' % jenni.config.password)
        __import__('time').sleep(5)
    
    #Add a line Oper = (name, pass) to the config file to give Willie server ops
    if hasattr(jenni.config, 'Oper'):
        jenni.write(('OPER', jenni.config.Oper[0]+' '+jenni.config.Oper[1]))

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
    jenni.reply('Refreshing ops list for '+input.sender+'.')
    jenni.flushOps(input.sender)
    if input.admin: jenni.write(('NAMES', input.sender))
refreshList.commands = ['newoplist']

def opList(jenni, input):
    for channel in jenni.ops:
        jenni.debug('Oplist', channel+' '+str(jenni.ops[channel]), 'verbose')
opList.commands = ['listops']

def handleNames(jenni, input):
    names = re.split(' ', input.group(1))
    channel = re.search('(#\S+)', jenni.raw).group(1)
    jenni.startOpsList(channel)
    for name in names:
        if '@' in name or '~' in name or '&' in name:
            jenni.addOp(channel, name.lstrip('@&%+~'))
        if '%' in name:
            jenni.addHalfOp(channel, name.lstrip('@&%+~'))
handleNames.rule = r'(.*)'
handleNames.event = '353'
handleNames.thread = False

def runningUpdate(jenni, input):
    line = re.search('(#\S+) ([+-])([hoaq]) (\S+)', jenni.raw)
    if line: channel, pm, mode, nick = line.groups()
    else: return
    
    add = pm == '+'
    if 'h' in mode:
        if add: jenni.addHalfOp(channel, nick)
        else: jenni.delHalfOp(channel, nick)
    else:
        if add: jenni.addOp(channel, nick)
        else: jenni.delOp(channel, nick)
runningUpdate.rule = r'(.*)'
runningUpdate.event = 'MODE'

if __name__ == '__main__':
    print __doc__.strip()
