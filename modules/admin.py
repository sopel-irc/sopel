#!/usr/bin/env python
"""
admin.py - Jenni Admin Module
Copyright 2010-2011, Sean B. Palmer (inamidst.com) and Michael Yanovich (yanovich.net)
Licensed under the Eiffel Forum License 2.

More info:
 * Jenni: https://github.com/myano/jenni/
 * Phenny: http://inamidst.com/phenny/
"""

def join(phenny, input): 
    """Join the specified channel. This is an admin-only command."""
    # Can only be done in privmsg by an admin
    if input.sender.startswith('#'): return
    if input.admin: 
        channel, key = input.group(1), input.group(2)
        if not key: 
            phenny.write(['JOIN'], channel)
        else: phenny.write(['JOIN', channel, key])
join.rule = r'\.join (#\S+)(?: *(\S+))?'
join.priority = 'low'
join.example = '.join #example or .join #example key'

def part(phenny, input): 
    """Part the specified channel. This is an admin-only command."""
    # Can only be done in privmsg by an admin
    if input.sender.startswith('#'): return
    if input.admin: 
        phenny.write(['PART'], input.group(2))
part.commands = ['part']
part.priority = 'low'
part.example = '.part #example'

def quit(phenny, input): 
    """Quit from the server. This is an owner-only command."""
    # Can only be done in privmsg by the owner
    if input.sender.startswith('#'): return
    if input.owner: 
        phenny.write(['QUIT'])
        __import__('os')._exit(0)
quit.commands = ['quit']
quit.priority = 'low'

def msg(phenny, input): 
    # Can only be done in privmsg by an admin
    if input.sender.startswith('#'): return
    a, b = input.group(2), input.group(3)
    if (not a) or (not b): return
    if input.admin: 
        phenny.msg(a, b)
msg.rule = (['msg'], r'(#?\S+) (.+)')
msg.priority = 'low'

def me(phenny, input): 
    # Can only be done in privmsg by an admin
    if input.sender.startswith('#'): return
    if input.admin: 
        msg = '\x01ACTION %s\x01' % input.group(3)
        phenny.msg(input.group(2), msg)
me.rule = (['me'], r'(#?\S+) (.*)')
me.priority = 'low'

def defend_ground (jenni, input):
    """
    This function monitors all kicks across all channels jenni is in. If she
    detects that she is the one kicked she'll automatically join that channel.

    WARNING: This may not needed and could cause problems if jenni becomes
    annoying. Please use this with caution.
    """
    channel = input.sender
    jenni.write(['JOIN'], channel)
defend_ground.event = 'KICK'
defend_ground.rule = '.*'
defend_ground.priority = 'low'

def mode(phenny, input):
    # Can only be done in privmsg by an admin
    if input.sender.startswith('#'): return
    if input.admin:
        mode = input.group(1)
        phenny.write(('MODE ', jenni.nick + ' ' + mode))
mode.rule = r'\.mode ([\+-]\S+)'
mode.priority = 'low'

def raw(phenny, input):
    # Can only be done in privmsg by owner
    if input.sender.startswith('#'): return
    if input.owner:
        phenny.write((input.group(1), input.group(2))
raw.rule = '.raw (\S+) (.*)'

if __name__ == '__main__':
   print __doc__.strip()

