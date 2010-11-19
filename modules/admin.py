#!/usr/bin/env python
"""
mod.py - Channel Module
Author: Alek Rollyson, http://opensource.osu.edu/
Phenny (about): http://inamidst.com/phenny/

Beefed up by Alek Rollyson. added functions for op, deop, voice, devoice
Uses NickServ ACC to verify that a nick is identified with services, as well
as m5's admin list as a double verification system. Should eliminate the possibility
of nick spoofing. May only work with freenode, hasn't been tested on other networks.

Forked by Michael S. Yanovich, http://opensource.osu.edu/~yanovich/
"""

import re
import time
import sched

auth_list = []
admins = []

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

def op(phenny, input):
    """
    Command to op users in a room. If no nick is given,
    phenny will op the nick who sent the command
    """
    if not input.admin or not input.sender.startswith('#'):
        return
    nick = input.group(2)
    verify = auth_check(phenny, input.nick, nick)
    if verify:
        if not nick:
            nick = input.nick
            channel = input.sender
            phenny.write(['MODE', channel, "+o", nick])
        else:
            channel = input.sender
            phenny.write(['MODE', channel, "+o", nick])
op.rule = (['op'], r'(\S+)?')
op.priority = 'low'

def deop(phenny, input):
    """
    Command to deop users in a room. If no nick is given,
    phenny will deop the nick who sent the command
    """
    if not input.admin or not input.sender.startswith('#'):
        return
    nick = input.group(2)
    verify = auth_check(phenny, input.nick, nick)
    if verify:
        if not nick:
            nick = input.nick
            channel = input.sender
            phenny.write(['MODE', channel, "-o", nick])
        else:
            channel = input.sender
            phenny.write(['MODE', channel, "-o", nick])
deop.rule = (['deop'], r'(\S+)?')
deop.priority = 'low'

def voice(phenny, input):
    """
    Command to voice users in a room. If no nick is given,
    phenny will voice the nick who sent the command
    """
    if not input.admin or not input.sender.startswith('#'):
        return
    nick = input.group(2)
    verify = auth_check(phenny, input.nick, nick)
    if verify:
        if not nick:
            nick = input.nick
            channel = input.sender
            phenny.write(['MODE', channel, "+v", nick])
        else:
            channel = input.sender
            phenny.write(['MODE', channel, "+v", nick])
voice.rule = (['voice'], r'(\S+)?')
voice.priority = 'low'

def devoice(phenny, input):
    """
    Command to devoice users in a room. If no nick is given,
    phenny will devoice the nick who sent the command
    """
    if not input.admin or not input.sender.startswith('#'):
        return
    nick = input.group(2)
    verify = auth_check(phenny, input.nick, nick)
    if verify:
        if not nick:
            nick = input.nick
            channel = input.sender
            phenny.write(['MODE', channel, "-v", nick])
        else:
            channel = input.sender
            phenny.write(['MODE', channel, "-v", nick])
devoice.rule = (['devoice'], r'(\S+)?')
devoice.priority = 'low'

def auth_request(phenny, input):
    """
    This will scan every message in a room for nicks in phenny's
    admin list.  If one is found, it will send an ACC request
    to NickServ.  May only work with Freenode.
    """
    admins = phenny.config.admins
    pattern = '(' + '|'.join([re.escape(x) for x in admins]) + ')'
    matches = re.findall(pattern, input)
    for x in matches:
        phenny.msg('NickServ', 'ACC ' + x)
auth_request.rule = r'.*'
auth_request.priority = 'high'

def auth_verify(phenny, input):
    """
    This will wait for notices from NickServ and scan for ACC
    responses.  This verifies with NickServ that nicks in the room
    are identified with NickServ so that they cannot be spoofed.
    May only work with freenode.
    """
    global auth_list
    nick = input.group(1)
    level = input.group(3)
    if input.nick != 'NickServ':
        return
    elif level == '3':
        if nick in auth_list:
            return
        else:
            auth_list.append(nick)
    else:
        if nick not in auth_list:
            return
        else:
            auth_list.remove(nick)
    print auth_list
auth_verify.event = 'NOTICE'
auth_verify.rule = r'(\S+) (ACC) ([0-3])'
auth_verify.priority = 'high'

def auth_check(phenny, nick, target=None):
    """
    Checks if nick is on the auth list and returns true if so
    """
    global auth_list
    if target == phenny.config.nick:
	    return 0
    elif nick in auth_list:
        return 1

def kick(phenny, input):
    if not input.admin: 
        return
    text = input.group().split()
    nick = text[2]
    if nick != phenny.config.nick:
        tmp = text[1] + " " + nick
        phenny.write(['KICK', tmp])
kick.commands = ['kick']
kick.priority = 'high'

def topic(phenny, input):
    """
    This gives admins the ability to change the topic.
    Note: One does *NOT* have to be an OP, one just has to be on the list of
    admins.
    """
    if not input.admin:
        return
    try:
        topic = input.group().split(".topic ")[1]
    except:
        return

    verify = auth_check(phenny, input.nick)
    channel = input.sender
    if verify:
        text = "topic " + str(channel) + " " + str(topic)
        phenny.write(('PRIVMSG', 'chanserv'), text)
topic.commands = ['topic']
topic.priority = 'low'

def defend_ground (phenny, input):
    """
    This function monitors all kicks across all channels phenny is in. If she
    detects that she is the one kicked she'll automatically join that channel.
    """
    channel = input.sender
    text = input.group()
    phenny.write(['JOIN'], channel)                
defend_ground.event = 'KICK'
defend_ground.rule = '.*'
defend_ground.priority = 'low'

if __name__ == '__main__': 
   print __doc__.strip()

