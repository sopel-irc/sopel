#!/usr/bin/env python
# coding=utf-8
"""
coretasks.py - Willie Ruotine Core tasks
Copyright 2008, Sean B. Palmer, inamidst.com
Copyright © 2012, Elad Alfassa <elad@fedoraproject.org>
Licensed under the Eiffel Forum License 2.

Willie: http://willie.dftba.net/

This is written as a module to make it easier to extend to support more responses to standard IRC codes without having to shove them all into the dispatch function in bot.py and making it easier to maintain.
"""
import re
import threading, time

#Ping timeout detection:

class runtime_data():
    ping_timer = None #A timer for ping-pong with the server

def setup(willie):
    ping_timeout = 300.0
    if hasattr(willie.config, 'ping_timeout'):
        try: refresh_delay = float(willie.config.ping_timeout)
        except: pass
    runtime_data.ping_timeout = ping_timeout

def close(willie):
    print "Ping timeout, restarting..."
    willie.handle_close()

def pingloop(willie):
    runtime_data.ping_timer = threading.Timer(runtime_data.ping_timeout, close, (willie,))
    runtime_data.ping_timer.start()
    willie.write(('PING', willie.config.host))

def pong(willie, Trigger):
    try:
        runtime_data.timer.cancel()
        time.sleep(runtime_data.ping_timeout + 60.0)
        pingloop(willie)
    except: pass
pong.event = 'PONG'
pong.rule = r'.*'


def startup(willie, trigger):
    ''' runs when we recived 251 - lusers, which is just before the server sends the motd, and right after establishing a sucessful connection '''
    if hasattr(willie.config, 'password'):
        willie.msg('NickServ', 'IDENTIFY %s' % willie.config.password)
    
    #Add a line Oper = (name, pass) to the config file to give Willie server ops
    if hasattr(willie.config, 'Oper'):
        willie.write(('OPER', willie.config.Oper[0]+' '+willie.config.Oper[1]))
    
    #Attempt to set bot mode.
    willie.write(('MODE ', willie.nick + ' +B'))

    for channel in willie.channels:
        willie.write(('JOIN', channel))

    pingloop(willie)
startup.rule = r'(.*)'
startup.event = '251'
startup.priority = 'low'



#Functions to maintain a list of chanops in all of willie's channels.

def refreshList(willie, trigger):
    ''' If you need to use this, then it means you found a bug '''
    willie.reply('Refreshing ops list for '+trigger.sender+'.')
    willie.flushOps(trigger.sender)
    if trigger.admin: willie.write(('NAMES', trigger.sender))
refreshList.commands = ['newoplist']

def opList(willie, trigger):
    for channel in willie.ops:
        willie.debug('Oplist', channel+' '+str(willie.ops[channel]), 'warning')
opList.commands = ['listops']

def handle_names(willie, trigger):
    ''' Handle NAMES response, happens when joining to channels'''
    names = re.split(' ', trigger.group(1))
    channel = re.search('(#\S+)', willie.raw).group(1)
    willie.startOpsList(channel)
    for name in names:
        if '@' in name or '~' in name or '&' in name:
            willie.addOp(channel, name.lstrip('@&%+~'))
            willie.addHalfOp(channel, name.lstrip('@&%+~'))
        elif '%' in name:
            willie.addHalfOp(channel, name.lstrip('@&%+~'))
handle_names.rule = r'(.*)'
handle_names.event = '353'
handle_names.thread = False

def track_modes(willie, trigger):
    ''' Track usermode changes and keep our lists of ops up to date '''
    line = re.findall('([\+\-][ahoqv].)', willie.raw)
    channel = re.search('(#\S+)', willie.raw)
    if channel is None:
        return #someone changed the bot's usermode, we don't care about that
    channel = channel.group(1)
    nicks = willie.raw.split(' ')[4:]
    modes = []
    for mode in line:
        for char in mode[1:]:
            if mode[0] == '+':
                modes.append((char, True))
            else:
                modes.append((char, False))
     
    if len(modes) == 0:
        return #We don't care about these mode changes
    for index in range(len(nicks)):
        mode = modes[index]
        nick = nicks[index]
        if mode[0]=='h':
            if mode[1] is True:
                willie.addHalfOp(channel, nick)
            else:
                willie.delHalfOp(channel, nick)
        elif mode[0] == 'o':
            if mode[1] is True:
                willie.addOp(channel, nick)
            else:
                willie.delOp(channel, nick)
track_modes.rule = r'(.*)'
track_modes.event = 'MODE'

def track_nicks(willie, trigger):
    '''Track nickname changes and maintain our chanops list accordingly'''
    old = trigger.nick
    new = trigger.group(1)
    
    for channel in willie.halfplus:
        if old in willie.halfplus[channel]:
            willie.delHalfOp(channel, old)
            willie.addHalfOp(channel, new)
    for channel in willie.ops:
        if old in willie.ops[channel]:
            willie.delOp(channel, old)
            willie.addOp(channel, new)
    
track_nicks.rule = r'(.*)'
track_nicks.event = 'NICK'

if __name__ == '__main__':
    print __doc__.strip()
