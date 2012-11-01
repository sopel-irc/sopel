#!/usr/bin/env python
# coding=utf-8
"""
coretasks.py - Willie Ruotine Core tasks
Copyright 2008-2011, Sean B. Palmer (inamidst.com) and Michael Yanovich (yanovich.net)
Copyright © 2012, Elad Alfassa <elad@fedoraproject.org>
Copyright 2012, Edward Powell (embolalia.net)
Licensed under the Eiffel Forum License 2.

Willie: http://willie.dftba.net/

This is written as a module to make it easier to extend to support more responses to standard IRC codes without having to shove them all into the dispatch function in bot.py and making it easier to maintain.
"""
import re
import threading, time



def startup(willie, trigger):
    ''' runs when we recived 251 - lusers, which is just before the server sends the motd, and right after establishing a sucessful connection '''
    if willie.config.core.nickserv_password is not None:
        willie.msg('NickServ', 'IDENTIFY %s' % willie.config.core.nickserv_password)

    if willie.config.core.oper_name is not None and willie.config.core.oper_password is not None:
        willie.write(('OPER', willie.config.core.oper_name+' '+willie.config.oper_password))
    
    #Set bot modes per config, +B if no config option is defined
    if willie.config.has_option('core', 'modes'):
        modes = willie.config.core.modes
    else:
        modes = 'B'
    willie.write(('MODE ', '%s +%s'%(willie.nick, modes)))

    for channel in willie.channels:
        willie.write(('JOIN', channel))

startup.rule = r'(.*)'
startup.event = '251'
startup.priority = 'low'



#Functions to maintain a list of chanops in all of willie's channels.

def refresh_list(willie, trigger):
    ''' If you need to use this, then it means you found a bug '''
    willie.reply('Refreshing ops list for '+trigger.sender+'.')
    willie.flushOps(trigger.sender)
    if trigger.admin: willie.write(('NAMES', trigger.sender))
refresh_list.commands = ['newoplist']

def list_ops(willie, trigger):
    for channel in willie.ops:
        willie.debug('Oplist', channel+' '+str(willie.ops[channel]), 'always')
list_ops.commands = ['listops']

def handle_names(willie, trigger):
    ''' Handle NAMES response, happens when joining to channels'''
    names = re.split(' ', trigger.group(1))
    channel = re.search('(#\S+)', willie.raw).group(1)
    willie.init_ops_list(channel)
    for name in names:
        if '@' in name or '~' in name or '&' in name:
            willie.add_op(channel, name.lstrip('@&%+~'))
            willie.add_halfop(channel, name.lstrip('@&%+~'))
        elif '%' in name:
            willie.add_halfop(channel, name.lstrip('@&%+~'))
handle_names.rule = r'(.*)'
handle_names.event = '353'
handle_names.thread = False

def track_modes(willie, trigger):
    ''' Track usermode changes and keep our lists of ops up to date '''
    line = re.findall('([\+\-][ahoqv]*)', willie.raw)
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
                willie.add_halfop(channel, nick)
            else:
                willie.del_halfop(channel, nick)
        elif mode[0] == 'o':
            if mode[1] is True:
                willie.add_op(channel, nick)
            else:
                willie.del_op(channel, nick)
track_modes.rule = r'(.*)'
track_modes.event = 'MODE'

def track_nicks(willie, trigger):
    '''Track nickname changes and maintain our chanops list accordingly'''
    old = trigger.nick
    new = trigger.group(1)
    
    for channel in willie.halfplus:
        if old in willie.halfplus[channel]:
            willie.del_halfop(channel, old)
            willie.add_halfop(channel, new)
    for channel in willie.ops:
        if old in willie.ops[channel]:
            willie.del_op(channel, old)
            willie.add_op(channel, new)
    
track_nicks.rule = r'(.*)'
track_nicks.event = 'NICK'


#Live blocklist editing

def blocks(willie, trigger):
    if not trigger.admin: return

    STRINGS = {
            "success_del" : "Successfully deleted block: %s",
            "success_add" : "Successfully added block: %s",
            "no_nick" : "No matching nick block found for: %s",
            "no_host" : "No matching hostmask block found for: %s",
            "invalid" : "Invalid format for %s a block. Try: .blocks add (nick|hostmask) willie",
            "invalid_display" : "Invalid input for displaying blocks.",
            "nonelisted" : "No %s listed in the blocklist.",
            'huh' : "I could not figure out what you wanted to do.",
            }

    masks = willie.config.core.host_blocks
    nicks = willie.config.core.nick_blocks
    print nicks, masks
    text = trigger.group().split()

    if len(text) == 3 and text[1] == "list":
        if text[2] == "hostmask":
            if len(masks) > 0 and masks.count("") == 0:
                for each in masks:
                    if len(each) > 0:
                        willie.say("blocked hostmask: " + each)
            else:
                willie.reply(STRINGS['nonelisted'] % ('hostmasks'))
        elif text[2] == "nick":
            if len(nicks) > 0 and nicks.count("") == 0:
                for each in nicks:
                    if len(each) > 0:
                        willie.say("blocked nick: " + each)
            else:
                willie.reply(STRINGS['nonelisted'] % ('nicks'))
        else:
            willie.reply(STRINGS['invalid_display'])

    elif len(text) == 4 and text[1] == "add":
        if text[2] == "nick":
            nicks.append(text[3])
            willie.config.core.nick_blocks = nicks
            willie.config.save()
        elif text[2] == "hostmask":
            masks.append(text[3].lower())
            willie.config.core.host_blocks = masks
        else:
            willie.reply(STRINGS['invalid'] % ("adding"))
            return

        willie.reply(STRINGS['success_add'] % (text[3]))

    elif len(text) == 4 and text[1] == "del":
        if text[2] == "nick":
            try:
                nicks.remove(text[3])
                willie.config.core.nick_blocks = nicks
                willie.config.save()
                willie.reply(STRINGS['success_del'] % (text[3]))
            except:
                willie.reply(STRINGS['no_nick'] % (text[3]))
                return
        elif text[2] == "hostmask":
            try:
                masks.remove(text[3].lower())
                willie.config.core.host_blocks = masks
                willie.config.save()
                willie.reply(STRINGS['success_del'] % (text[3]))
            except:
                willie.reply(STRINGS['no_host'] % (text[3]))
                return
        else:
            willie.reply(STRINGS['invalid'] % ("deleting"))
            return
    else:
        willie.reply(STRINGS['huh'])

blocks.commands = ['blocks']
blocks.priority = 'low'
blocks.thread = False

if __name__ == '__main__':
    print __doc__.strip()
