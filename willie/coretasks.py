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

    for channel in willie.config.core.channels.split(','):
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
    """
    List channel operators in the given channel, or current channel if none is
    given.
    """
    if trigger.group(2):
        willie.say(trigger.group(2))
        if trigger.group(2) in willie.ops:
            willie.say(str(willie.ops[channel]))
        else:
            willie.say('None')
    else:
        if trigger.sender in willie.ops:
            willie.say(str(willie.ops[trigger.sender]))
        else:
            willie.say('None')
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
    # 0 is who set it, 1 is MODE. We don't need those.
    line = willie.raw.split(' ')[2:]
    
    # If the first character of where the mode is being set isn't a #
    # then it's a user mode, not a channel mode, so we'll ignore it.
    if line[0][0] != '#':
        return
    channel, mode_sec = line[:2]
    nicks = line[2:]

    # Break out the modes, because IRC allows e.g. MODE +aB-c foo bar baz
    sign = ''
    modes = []
    for char in mode_sec:
        if char == '+' or char == '-':
            sign = char
        else:
            modes.append(sign + char)
    
    # Some basic checks for broken replies from server. Probably unnecessary.
    if len(modes) > len(nicks):
        willie.debug('core',
            'MODE recieved from server with more modes than nicks.', 'warning')
        modes = modes[:(len(nicks) + 1)]  # Try truncating, in case that works.
    elif len(modes) < len(nicks):
        willie.debug('core',
            'MODE recieved from server with more nicks than modes.', 'warning')
        nicks = nicks[:(len(modes) - 1)]  # Try truncating, in case that works.
    # This one is almost certainly unneeded.
    if not (len(modes) and len(nicks)):
        willie.debug('core', 'MODE recieved from server without arguments',
            'verbose')
        return  # Nothing to do here.
    
    for nick, mode in zip(nicks, modes):
        if mode[1] == 'o' or mode[1] == 'q': # Op or owner (for UnrealIRCd)
            if mode[0] == '+':
                willie.add_op(channel, nick)
            else:
                willie.del_op(channel, nick)
        elif mode[1] == 'h': # Halfop
            if mode[0] == '+':
                willie.add_halfop(channel, nick)
            else:
                willie.del_halfop(channel, nick)
track_modes.rule = r'(.*)'
track_modes.event = 'MODE'

def track_nicks(willie, trigger):
    '''Track nickname changes and maintain our chanops list accordingly'''
    old = trigger.nick
    new = trigger.group(1)
    
    # Give debug mssage, and PM the owner, if the bot's own nick changes.
    if old == willie.nick:
        privmsg = "Hi, I'm your bot, %s. Something has made my nick change. This can cause some problems for me, and make me do weird things. You'll probably want to restart me, and figure out what made that happen so you can stop it happening again. (Usually, it means you tried to give me a nick that's protected by NickServ.)" % willie.nick
        debug_msg = "Nick changed by server. This can cause unexpected behavior. Please restart the bot."
        willie.debug('[CORE]', debug_msg, 'always')
        willie.msg(willie.config.core.owner, privmsg)
        return

    for channel in willie.halfplus:
        if old.lower() in willie.halfplus[channel]:
            willie.del_halfop(channel, old)
            willie.add_halfop(channel, new)
    for channel in willie.ops:
        if old.lower() in willie.ops[channel]:
            willie.del_op(channel, old)
            willie.add_op(channel, new)
    
track_nicks.rule = r'(.*)'
track_nicks.event = 'NICK'

def track_part(willie, trigger):
    if trigger.nick == willie.nick and trigger.sender in willie.channels:
        willie.channels.remove(trigger.sender)
track_part.rule = r'(.*)'
track_part.event = 'PART'

def track_join(willie, trigger):
    if trigger.nick == willie.nick and trigger.groups(1) in willie.channels:
        willie.channels.append(trigger.groups(1))
track_join.rule = r'(.*)'
track_join.event = 'JOIN'

#Live blocklist editing

def blocks(willie, trigger):
    """
    Manage Willie's blocking features.
    https://github.com/embolalia/willie/wiki/Making-Willie-ignore-people
    """
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
