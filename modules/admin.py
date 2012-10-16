#!/usr/bin/env python
# coding=utf-8
"""
admin.py - Willie Admin Module
Copyright 2010-2011, Sean B. Palmer (inamidst.com) and Michael Yanovich (yanovich.net)
Copyright © 2012, Elad Alfassa, <elad@fedoraproject.org>

Licensed under the Eiffel Forum License 2.

http://willie.dfbta.net
"""

import os

#TODO this will be reworked when we rework the configuration wizard, probably.
def configure(config):
    if config.option('Configure advanced administration options', False):
        if not config.has_section('url'):
            config.add_section('admin')
        #TODO add config for defend_ground
        config.add_list('admin', 'nick_blocks', 
            'Enter regular expressions for blocked nicks.', 'nick')
        config.add_list('admin', 'mask_blocks',
            'Enter regular expressions for blocked hostmasks.', 'mask')

def setup(willie):
    if willie.config.has_option('admin', 'nick_blocks') and willie.config.has_option('admin', 'mask_blocks'):
        if not isinstance(willie.config.admin.nick_blocks, list):
            willie.config.admin.nick_blocks = willie.config.admin.nick_blocks.split(',')
        if not isinstance(willie.config.admin.mask_blocks, list):
            willie.config.admin.mask_blocks = willie.config.admin.mask_blocks.split(',')

def join(willie, trigger):
    """Join the specified channel. This is an admin-only command."""
    # Can only be done in privmsg by an admin
    if trigger.sender.startswith('#'): 
        return
    if trigger.admin:
        channel, key = trigger.group(1), trigger.group(2)
        if not key:
            willie.join(channel)
        else: 
            willie.join(channel, key)
join.rule = r'\.join (#\S+)(?: *(\S+))?'
join.priority = 'low'
join.example = '.join #example or .join #example key'

def part(willie, trigger): 
    """Part the specified channel. This is an admin-only command."""
    # Can only be done in privmsg by an admin
    if trigger.sender.startswith('#'): 
        return
    if trigger.admin: 
        willie.part(trigger.group(2).strip())
part.commands = ['part']
part.priority = 'low'
part.example = '.part #example'

def quit(willie, trigger): 
    """Quit from the server. This is an owner-only command."""
    # Can only be done in privmsg by the owner
    if trigger.sender.startswith('#'): 
        return
    if trigger.owner:
        quit_message = 'Quitting on command from %s' % trigger.nick
        if trigger.group(2) is not None:
            quit_message = trigger.group(2)
        willie.quit(quit_message)
quit.commands = ['quit']
quit.priority = 'low'

def msg(willie, trigger): 
    # Can only be done in privmsg by an admin
    if trigger.sender.startswith('#'): 
        return
    a, b = trigger.group(2), trigger.group(3)
    if (not a) or (not b): 
        return
    if trigger.admin: 
        willie.msg(a, b)
msg.rule = (['msg'], r'(#?\S+) (.+)')
msg.priority = 'low'

def me(willie, trigger): 
    # Can only be done in privmsg by an admin
    if trigger.sender.startswith('#'): 
        return
    if trigger.admin: 
        msg = '\x01ACTION %s\x01' % trigger.group(3)
        willie.msg(trigger.group(2), msg)
me.rule = (['me'], r'(#?\S+) (.*)')
me.priority = 'low'

def defend_ground(willie, trigger):
    """
    This function monitors all kicks across all channels willie is in. If he
    detects that she is the one kicked she'll automatically join that channel.

    WARNING: This may not be needed and could cause problems if willie becomes
    annoying. Please use this with caution.
    """
    channel = trigger.sender
    willie.write(['JOIN'], channel)
defend_ground.event = 'KICK'
defend_ground.rule = '.*'
defend_ground.priority = 'low'

def mode(willie, trigger):
    # Can only be done in privmsg by an admin
    if trigger.sender.startswith('#'):
        return
    if trigger.admin:
        mode = trigger.group(1)
        willie.write(('MODE ', willie.nick + ' ' + mode))
mode.rule = r'\.mode ([\+-]\S+)'
mode.priority = 'low'

def raw(phenny, trigger):
    # Can only be done in privmsg by owner
    if trigger.sender.startswith('#'): return
    if trigger.owner:
        phenny.write((trigger.group(1), trigger.group(2)))
raw.rule = '.raw (\S+) (.*)'


def blocks(willie, trigger):
    if not trigger.admin: return
    
    if not (willie.config.has_option('admin', 'nick_blocks') and willie.config.has_option('admin', 'mask_blocks')):
        print 3
        return

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

    masks = willie.config.admin.mask_blocks
    nicks = willie.config.admin.nick_blocks

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
            willie.config.admin.nick_blocks = nicks
            willie.config.save()
        elif text[2] == "hostmask":
            masks.append(text[3].lower())
            willie.config.admin.host_blocks = masks
        else:
            willie.reply(STRINGS['invalid'] % ("adding"))
            return

        willie.reply(STRINGS['success_add'] % (text[3]))

    elif len(text) == 4 and text[1] == "del":
        if text[2] == "nick":
            try:
                nicks.remove(text[3])
                willie.config.admin.nick_blocks = nicks
                willie.config.save()
                willie.reply(STRINGS['success_del'] % (text[3]))
            except:
                willie.reply(STRINGS['no_nick'] % (text[3]))
                return
        elif text[2] == "hostmask":
            try:
                masks.remove(text[3].lower())
                willie.config.admin.mask_blocks = masks
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

