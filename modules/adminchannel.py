#!/usr/bin/env python
# coding=utf-8
"""
admin.py - Jenni Admin Module
Copyright 2010-2011, Michael Yanovich, Alek Rollyson, and Edward Powell
Copyright © 2012, Elad Alfassa <elad@fedoraproject.org>
Licensed under the Eiffel Forum License 2.

More info:
 * Jenni: https://github.com/myano/jenni/
 * Phenny: http://inamidst.com/phenny/
 * Willie: http://willie.dftba.net/

Beefed up by Alek Rollyson. added functions for op, deop, voice, devoice
Uses NickServ ACC to verify that a nick is identified with services, as well
as m5's admin list as a double verification system. Should eliminate the possibility of nick spoofing. May only work with freenode, hasn't been tested
on other networks.
Also includes ability to have locked topic
"""

import re

auth_list = []
admins = []


def op(jenni, trigger):
    """
    Command to op users in a room. If no nick is given,
    jenni will op the nick who sent the command
    """
    if not trigger.isop:
        return
    nick = trigger.group(2)
    verify = auth_check(jenni, trigger.nick, nick)
    if verify:
        channel = trigger.sender
        if not nick:
            nick = trigger.nick
        jenni.write(['MODE', channel, "+o", nick])
op.rule = (['op'], r'(\S+)?')
op.priority = 'low'

def deop(jenni, trigger):
    """
    Command to deop users in a room. If no nick is given,
    jenni will deop the nick who sent the command
    """
    if not trigger.isop:
        return
    nick = trigger.group(2)
    verify = auth_check(jenni, trigger.nick, nick)
    if verify:
        channel = trigger.sender
        if not nick:
            nick = trigger.nick
        jenni.write(['MODE', channel, "-o", nick])
deop.rule = (['deop'], r'(\S+)?')
deop.priority = 'low'

def voice(jenni, trigger):
    """
    Command to voice users in a room. If no nick is given,
    jenni will voice the nick who sent the command
    """
    if not trigger.isop:
        return
    nick = trigger.group(2)
    verify = auth_check(jenni, trigger.nick, nick)
    if verify:
        channel = trigger.sender
        if not nick:
            nick = trigger.nick
        jenni.write(['MODE', channel, "+v", nick])
voice.rule = (['voice'], r'(\S+)?')
voice.priority = 'low'

def devoice(jenni, trigger):
    """
    Command to devoice users in a room. If no nick is given,
    jenni will devoice the nick who sent the command
    """
    if not trigger.isop:
        return
    nick = trigger.group(2)
    verify = auth_check(jenni, trigger.nick, nick)
    if verify:
        channel = trigger.sender
        if not nick:
            nick = trigger.nick
        jenni.write(['MODE', channel, "-v", nick])
devoice.rule = (['devoice'], r'(\S+)?')
devoice.priority = 'low'

def auth_request(jenni, trigger):
    """
    This will scan every message in a room for nicks in jenni's
    admin list.  If one is found, it will send an ACC request
    to NickServ.  May only work with Freenode.
    """
    admins = jenni.config.admins
    pattern = '(' + '|'.join([re.escape(x) for x in admins]) + ')'
    matches = re.findall(pattern, trigger)
    for x in matches:
        jenni.msg('NickServ', 'ACC ' + x)
auth_request.rule = r'.*'
auth_request.priority = 'high'

def auth_verify(jenni, trigger):
    """
    This will wait for notices from NickServ and scan for ACC
    responses.  This verifies with NickServ that nicks in the room
    are identified with NickServ so that they cannot be spoofed.
    May only work with freenode.
    """
    global auth_list
    nick = trigger.group(1)
    level = trigger.group(3)
    if trigger.nick != 'NickServ':
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
auth_verify.event = 'NOTICE'
auth_verify.rule = r'(\S+) (ACC) ([0-3])'
auth_verify.priority = 'high'

def auth_check(jenni, nick, target=None):
    """
    Checks if nick is on the auth list and returns true if so
    """
    global auth_list
    if target == jenni.config.nick:
        return 0
    elif nick in auth_list:
        return 1

def deauth(nick):
    """
    Remove pepole from the deauth list.
    """
    global auth_list
    if nick in auth_list:
        a = auth_list.index(nick)
        del(auth_list[a])

def deauth_quit(jenni, trigger):
    deauth(trigger.nick)
deauth_quit.event = 'QUIT'
deauth_quit.rule = '.*'

def deauth_part(jenni, trigger):
    deauth(trigger.nick)
deauth_part.event = 'PART'
deauth_part.rule = '.*'

def deauth_nick(jenni, trigger):
    deauth(trigger.nick)
deauth_nick.event = 'NICK'
deauth_nick.rule = '.*'

def kick(jenni, trigger):
    if not trigger.isop:
        return
    text = trigger.group().split()
    argc = len(text)
    if argc < 2: return
    opt = text[1]
    nick = opt
    channel = trigger.sender
    reasonidx = 2
    if opt.startswith('#'):
        if argc < 3: return
        nick = text[2]
        channel = opt
        reasonidx = 3
    reason = ' '.join(text[reasonidx:])
    if nick != jenni.config.nick:
        jenni.write(['KICK', channel, nick, reason])
kick.commands = ['kick']
kick.priority = 'high'

def configureHostMask (mask):
    if mask == '*!*@*': return mask
    if re.match('^[^.@!/]+$', mask) is not None: return '%s!*@*' % mask
    if re.match('^[^@!]+$', mask) is not None: return '*!*@%s' % mask

    m = re.match('^([^!@]+)@$', mask)
    if m is not None: return '*!%s@*' % m.group(1)

    m = re.match('^([^!@]+)@([^@!]+)$', mask)
    if m is not None: return '*!%s@%s' % (m.group(1), m.group(2))

    m = re.match('^([^!@]+)!(^[!@]+)@?$', mask)
    if m is not None: return '%s!%s@*' % (m.group(1), m.group(2))
    return ''

def ban (jenni, trigger):
    """
    This give admins the ability to ban a user.
    The bot must be a Channel Operator for this command to work.
    """
    if not trigger.isop:
        return
    text = trigger.group().split()
    argc = len(text)
    if argc < 2: return
    opt = text[1]
    banmask = opt
    channel = trigger.sender
    if opt.startswith('#'):
        if argc < 3: return
        channel = opt
        banmask = text[2]
    banmask = configureHostMask(banmask)
    if banmask == '': return
    jenni.write(['MODE', channel, '+b', banmask])
ban.commands = ['ban']
ban.priority = 'high'

def unban (jenni, trigger):
    """
    This give admins the ability to unban a user.
    The bot must be a Channel Operator for this command to work.
    """
    if not trigger.isop:
        return
    text = trigger.group().split()
    argc = len(text)
    if argc < 2: return
    opt = text[1]
    banmask = opt
    channel = trigger.sender
    if opt.startswith('#'):
        if argc < 3: return
        channel = opt
        banmask = text[2]
    banmask = configureHostMask(banmask)
    if banmask == '': return
    jenni.write(['MODE', channel, '-b', banmask])
unban.commands = ['unban']
unban.priority = 'high'

def quiet (jenni, trigger):
    """
    This gives admins the ability to quiet a user.
    The bot must be a Channel Operator for this command to work
    """
    if not trigger.isop:
        return
    text = trigger.group().split()
    argc = len(text)
    if argc < 2: return
    opt = text[1]
    quietmask = opt
    channel = trigger.sender
    if opt.startswith('#'):
       if argc < 3: return
       quietmask = text[2]
       channel = opt
    quietmask = configureHostMask(quietmask)
    if quietmask == '': return
    jenni.write(['MODE', channel, '+q', quietmask])
quiet.commands = ['quiet']
quiet.priority = 'high'

def unquiet (jenni, trigger):
   """
   This gives admins the ability to unquiet a user.
   The bot must be a Channel Operator for this command to work
   """
   if not trigger.isop: return
   text = trigger.group().split()
   argc = len(text)
   if argc < 2: return
   opt = text[1]
   quietmask = opt
   channel = trigger.sender
   if opt.startswith('#'):
       if argc < 3: return
       quietmask = text[2]
       channel = opt
   quietmask = configureHostMask(quietmask)
   if quietmask == '': return
   jenni.write(['MODE', opt, '-q', quietmask])
unquiet.commands = ['unquiet']
unquiet.priority = 'high'

def kickban (jenni, trigger):
   """
   This gives admins the ability to kickban a user.
   The bot must be a Channel Operator for this command to work
   .kickban [#chan] user1 user!*@* get out of here
   """
   if not trigger.isop: return
   text = trigger.group().split()
   argc = len(text)
   if argc < 4: return
   opt = text[1]
   nick = opt
   mask = text[2]
   reasonidx = 3
   if opt.startswith('#'):
       if argc < 5: return
       channel = opt
       nick = text[2]
       mask = text[3]
       reasonidx = 4
   reason = ' '.join(text[reasonidx:])
   mask = configureHostMask(mask)
   if mask == '': return
   jenni.write(['MODE', channel, '+b', mask])
   jenni.write(['KICK', channel, nick, ' :', reason])
kickban.commands = ['kickban', 'kb']
kickban.priority = 'high'

def topic(jenni, trigger):
    """
    This gives ops the ability to change the topic.
    """
    purple, green, bold = '\x0306', '\x0310', '\x02'
    if trigger.isop:
        return
    text = trigger.group(2)
    if text == '':
        return
    channel = trigger.sender.lower()
    
    narg = 1
    mask = None
    if jenni.settings.hascolumn('topic_mask') and channel in jenni.settings:
        mask = jenni.settings.get(channel, 'topic_mask')
        narg = len(re.findall('%s', mask))
    if not mask or mask == '':
        mask = purple +'Welcome to: '+ green + channel + purple \
            +' | '+ bold +'Topic: '+ bold + green + '%s'
    
    top = trigger.group(2)
    text = tuple()
    if top:
        text = tuple(unicode.split(top, '~', narg))
        
    
    
    if len(text) != narg:
        message = "Not enough arguments. You gave "+str(len(text))+', it requires '+str(narg)+'.'
        return jenni.say(message)
    topic = mask % text
    
    jenni.write(('TOPIC', channel + ' :' + topic))
topic.commands = ['topic']
topic.priority = 'low'

def set_mask (jenni, trigger):
    if not trigger.isop:
        return
    if not jenni.settings.hascolumn('topic_mask'):
        jenni.say("I'm afraid I can't do that.")
    else:
        jenni.settings.update(trigger.sender, {'topic_mask': trigger.group(2)})
        jenni.say("Gotcha, " + trigger.nick)
set_mask.commands = ['tmask']

def show_mask (jenni, trigger):
    if not trigger.isop:
        return
    if not jenni.settings.hascolumn('topic_mask'):
        jenni.say("I'm afraid I can't do that.")
    else:
        jenni.say(jenni.settings.get(trigger.sender, 'topic_mask'))
show_mask.commands = ['showmask']

def isop (jenni, trigger):
    if trigger.isop:
        jenni.reply('yes')
    else:
        jenni.reply('no')
isop.commands = ['isop']

if __name__ == '__main__':
    print __doc__.strip()
