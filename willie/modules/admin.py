# coding=utf-8
"""
admin.py - Willie Admin Module
Copyright 2010-2011, Sean B. Palmer (inamidst.com) and Michael Yanovich (yanovich.net)
Copyright © 2012, Elad Alfassa, <elad@fedoraproject.org>

Licensed under the Eiffel Forum License 2.

http://willie.dfbta.net
"""

import os

def configure(config):
    """
    | [admin] | example | purpose |
    | -------- | ------- | ------- |
    | hold_ground | False | Auto re-join on kick |
    """
    config.add_option('admin', 'hold_ground', "Auto re-join on kick")

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
    """
    Send a message to a given channel or nick. Can only be done in privmsg by an
    admin.
    """
    if trigger.sender.startswith('#'): 
        return
    a, b = trigger.group(2), trigger.group(3)
    if (not a) or (not b): 
        return
    if trigger.admin: 
        willie.msg(a, b)
msg.rule = (['msg'], r'(#?\S+) (.+)')
msg.priority = 'low'
msg.example = '.msg #YourPants Does anyone else smell neurotoxin?'

def me(willie, trigger): 
    """
    Send an ACTION (/me) to a given channel or nick. Can only be done in privmsg
    by an admin.
    """
    if trigger.sender.startswith('#'): 
        return
    if trigger.admin: 
        msg = '\x01ACTION %s\x01' % trigger.group(3)
        willie.msg(trigger.group(2), msg)
me.rule = (['me'], r'(#?\S+) (.*)')
me.priority = 'low'

def hold_ground(willie, trigger):
    """
    This function monitors all kicks across all channels willie is in. If it
    detects that it is the one kicked it'll automatically join that channel.

    WARNING: This may not be needed and could cause problems if willie becomes
    annoying. Please use this with caution.
    """
    if willie.config.has_section('admin') and willie.config.admin.hold_ground:
        channel = trigger.sender
        if trigger.args[1] == willie.nick:
         willie.join(channel)
hold_ground.event = 'KICK'
hold_ground.rule = '.*'
hold_ground.priority = 'low'

def mode(willie, trigger):
    """Set a user mode on Willie. Can only be done in privmsg by an admin."""
    if trigger.sender.startswith('#'):
        return
    if trigger.admin:
        mode = trigger.group(1)
        willie.write(('MODE ', willie.nick + ' ' + mode))
mode.rule = r'\.mode ([\+-]\S+)'
mode.priority = 'low'

if __name__ == '__main__':
   print __doc__.strip()

