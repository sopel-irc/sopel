# coding=utf-8
"""
admin.py - Willie Admin Module
Copyright 2010-2011, Michael Yanovich, Alek Rollyson, and Edward Powell
Copyright © 2012, Elad Alfassa <elad@fedoraproject.org>
Licensed under the Eiffel Forum License 2.

http://willie.dftba.net/

"""

import re

def setup(willie):
    #Having a db means pref's exists. Later, we can just use `if willie.db`.
    if willie.db and not willie.db.preferences.has_columns('topic_mask'):
        willie.db.preferences.add_columns(['topic_mask'])

def op(willie, trigger):
    """
    Command to op users in a room. If no nick is given,
    willie will op the nick who sent the command
    """
    if not trigger.isop:
        return
    nick = trigger.group(2)
    verify = auth_check(willie, trigger.nick, nick)
    if verify:
        channel = trigger.sender
        if not nick:
            nick = trigger.nick
        willie.write(['MODE', channel, "+o", nick])
op.rule = (['op'], r'(\S+)?')
op.priority = 'low'

def deop(willie, trigger):
    """
    Command to deop users in a room. If no nick is given,
    willie will deop the nick who sent the command
    """
    if not trigger.isop:
        return
    nick = trigger.group(2)
    verify = auth_check(willie, trigger.nick, nick)
    if verify:
        channel = trigger.sender
        if not nick:
            nick = trigger.nick
        willie.write(['MODE', channel, "-o", nick])
deop.rule = (['deop'], r'(\S+)?')
deop.priority = 'low'

def voice(willie, trigger):
    """
    Command to voice users in a room. If no nick is given,
    willie will voice the nick who sent the command
    """
    if not trigger.isop:
        return
    nick = trigger.group(2)
    verify = auth_check(willie, trigger.nick, nick)
    if verify:
        channel = trigger.sender
        if not nick:
            nick = trigger.nick
        willie.write(['MODE', channel, "+v", nick])
voice.rule = (['voice'], r'(\S+)?')
voice.priority = 'low'

def devoice(willie, trigger):
    """
    Command to devoice users in a room. If no nick is given,
    willie will devoice the nick who sent the command
    """
    if not trigger.isop:
        return
    nick = trigger.group(2)
    verify = auth_check(willie, trigger.nick, nick)
    if verify:
        channel = trigger.sender
        if not nick:
            nick = trigger.nick
        willie.write(['MODE', channel, "-v", nick])
devoice.rule = (['devoice'], r'(\S+)?')
devoice.priority = 'low'

def kick(willie, trigger):
    """
    Kick a user from the channel.
    """
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
    if nick != willie.config.nick:
        willie.write(['KICK', channel, nick, reason])
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

def ban (willie, trigger):
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
    willie.write(['MODE', channel, '+b', banmask])
ban.commands = ['ban']
ban.priority = 'high'

def unban (willie, trigger):
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
    willie.write(['MODE', channel, '-b', banmask])
unban.commands = ['unban']
unban.priority = 'high'

def quiet (willie, trigger):
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
    willie.write(['MODE', channel, '+q', quietmask])
quiet.commands = ['quiet']
quiet.priority = 'high'

def unquiet (willie, trigger):
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
   willie.write(['MODE', opt, '-q', quietmask])
unquiet.commands = ['unquiet']
unquiet.priority = 'high'

def kickban (willie, trigger):
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
   willie.write(['MODE', channel, '+b', mask])
   willie.write(['KICK', channel, nick, ' :', reason])
kickban.commands = ['kickban', 'kb']
kickban.priority = 'high'

def topic(willie, trigger):
    """
    This gives ops the ability to change the topic.
    """
    purple, green, bold = '\x0306', '\x0310', '\x02'
    if not trigger.isop:
        return
    text = trigger.group(2)
    if text == '':
        return
    channel = trigger.sender.lower()
    
    narg = 1
    mask = None
    if willie.db and channel in willie.db.preferences:
        mask = willie.db.preferences.get(channel, 'topic_mask')
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
        return willie.say(message)
    topic = mask % text
    
    willie.write(('TOPIC', channel + ' :' + topic))
topic.commands = ['topic']
topic.priority = 'low'

def set_mask (willie, trigger):
    """
    Set the mask to use for .topic in the current channel. %s is used to allow
    substituting in chunks of text.
    """
    if not trigger.isop:
        return
    if not willie.db:
        willie.say("I'm afraid I can't do that.")
    else:
        willie.db.preferences.update(trigger.sender, {'topic_mask': trigger.group(2)})
        willie.say("Gotcha, " + trigger.nick)
set_mask.commands = ['tmask']

def show_mask (willie, trigger):
    """Show the topic mask for the current channel."""
    if not trigger.isop:
        return
    if not willie.db:
        willie.say("I'm afraid I can't do that.")
    elif trigger.sender in willie.db.preferences:
        willie.say(willie.db.preferences.get(trigger.sender, 'topic_mask'))
    else:
        willie.say("%s")
show_mask.commands = ['showmask']

def isop (willie, trigger):
    """Show if you are an operator in the current channel"""
    if trigger.isop:
        willie.reply('yes')
    else:
        willie.reply('no')
isop.commands = ['isop']

if __name__ == '__main__':
    print __doc__.strip()
