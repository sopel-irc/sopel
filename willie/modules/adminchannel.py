# coding=utf-8
"""
admin.py - Willie Admin Module
Copyright 2010-2011, Michael Yanovich, Alek Rollyson, and Edward Powell
Copyright © 2012, Elad Alfassa <elad@fedoraproject.org>
Licensed under the Eiffel Forum License 2.

http://willie.dftba.net/

"""

import re
from willie.module import command, commands, priority


def setup(bot):
    #Having a db means pref's exists. Later, we can just use `if bot.db`.
    if bot.db and not bot.db.preferences.has_columns('topic_mask'):
        bot.db.preferences.add_columns(['topic_mask'])


@command('op')
def op(bot, trigger):
    """
    Command to op users in a room. If no nick is given,
    willie will op the nick who sent the command
    """
    if trigger.isop:
        nick = trigger.group(2)
        channel = trigger.sender
        if not nick:
            nick = trigger.nick
        bot.write(['MODE', channel, "+o", nick])


@command('deop')
def deop(bot, trigger):
    """
    Command to deop users in a room. If no nick is given,
    willie will deop the nick who sent the command
    """
    if trigger.isop:
        nick = trigger.group(2)
        channel = trigger.sender
        if not nick:
            nick = trigger.nick
        bot.write(['MODE', channel, "-o", nick])


@command('voice')
def voice(bot, trigger):
    """
    Command to voice users in a room. If no nick is given,
    willie will voice the nick who sent the command
    """
    if trigger.isop:
        nick = trigger.group(2)
        channel = trigger.sender
        if not nick:
            nick = trigger.nick
        bot.write(['MODE', channel, "+v", nick])


@command('devoice')
def devoice(bot, trigger):
    """
    Command to devoice users in a room. If no nick is given,
    willie will devoice the nick who sent the command
    """
    if trigger.isop:
        nick = trigger.group(2)
        channel = trigger.sender
        if not nick:
            nick = trigger.nick
        bot.write(['MODE', channel, "-v", nick])


@command('kick')
@priority('high')
def kick(bot, trigger):
    """
    Kick a user from the channel.
    """
    if not trigger.isop:
        return
    text = trigger.group().split()
    argc = len(text)
    if argc < 2:
        return
    opt = text[1]
    nick = opt
    channel = trigger.sender
    reasonidx = 2
    if opt.startswith('#'):
        if argc < 3:
            return
        nick = text[2]
        channel = opt
        reasonidx = 3
    reason = ' '.join(text[reasonidx:])
    if nick != bot.config.nick:
        bot.write(['KICK', channel, nick, reason])


def configureHostMask(mask):
    if mask == '*!*@*':
        return mask
    if re.match('^[^.@!/]+$', mask) is not None:
        return '%s!*@*' % mask
    if re.match('^[^@!]+$', mask) is not None:
        return '*!*@%s' % mask

    m = re.match('^([^!@]+)@$', mask)
    if m is not None:
        return '*!%s@*' % m.group(1)

    m = re.match('^([^!@]+)@([^@!]+)$', mask)
    if m is not None:
        return '*!%s@%s' % (m.group(1), m.group(2))

    m = re.match('^([^!@]+)!(^[!@]+)@?$', mask)
    if m is not None:
        return '%s!%s@*' % (m.group(1), m.group(2))
    return ''


@command('ban')
@priority('high')
def ban(bot, trigger):
    """
    This give admins the ability to ban a user.
    The bot must be a Channel Operator for this command to work.
    """
    if not trigger.isop:
        return
    text = trigger.group().split()
    argc = len(text)
    if argc < 2:
        return
    opt = text[1]
    banmask = opt
    channel = trigger.sender
    if opt.startswith('#'):
        if argc < 3:
            return
        channel = opt
        banmask = text[2]
    banmask = configureHostMask(banmask)
    if banmask == '':
        return
    bot.write(['MODE', channel, '+b', banmask])


@command('unban')
def unban(bot, trigger):
    """
    This give admins the ability to unban a user.
    The bot must be a Channel Operator for this command to work.
    """
    if not trigger.isop:
        return
    text = trigger.group().split()
    argc = len(text)
    if argc < 2:
        return
    opt = text[1]
    banmask = opt
    channel = trigger.sender
    if opt.startswith('#'):
        if argc < 3:
            return
        channel = opt
        banmask = text[2]
    banmask = configureHostMask(banmask)
    if banmask == '':
        return
    bot.write(['MODE', channel, '-b', banmask])


@command('quiet')
def quiet(bot, trigger):
    """
    This gives admins the ability to quiet a user.
    The bot must be a Channel Operator for this command to work
    """
    if not trigger.isop:
        return
    text = trigger.group().split()
    argc = len(text)
    if argc < 2:
        return
    opt = text[1]
    quietmask = opt
    channel = trigger.sender
    if opt.startswith('#'):
        if argc < 3:
            return
        quietmask = text[2]
        channel = opt
    quietmask = configureHostMask(quietmask)
    if quietmask == '':
        return
    bot.write(['MODE', channel, '+q', quietmask])


@command('unquiet')
def unquiet(bot, trigger):
    """
   This gives admins the ability to unquiet a user.
   The bot must be a Channel Operator for this command to work
   """
    if not trigger.isop:
        return
    text = trigger.group().split()
    argc = len(text)
    if argc < 2:
        return
    opt = text[1]
    quietmask = opt
    channel = trigger.sender
    if opt.startswith('#'):
        if argc < 3:
            return
        quietmask = text[2]
        channel = opt
    quietmask = configureHostMask(quietmask)
    if quietmask == '':
        return
    bot.write(['MODE', opt, '-q', quietmask])


@commands('kickban', 'kb')
@priority('high')
def kickban(bot, trigger):
    """
   This gives admins the ability to kickban a user.
   The bot must be a Channel Operator for this command to work
   .kickban [#chan] user1 user!*@* get out of here
   """
    if not trigger.isop:
        return
    text = trigger.group().split()
    argc = len(text)
    if argc < 4:
        return
    opt = text[1]
    nick = opt
    mask = text[2]
    reasonidx = 3
    if opt.startswith('#'):
        if argc < 5:
            return
        channel = opt
        nick = text[2]
        mask = text[3]
        reasonidx = 4
    reason = ' '.join(text[reasonidx:])
    mask = configureHostMask(mask)
    if mask == '':
        return
    bot.write(['MODE', channel, '+b', mask])
    bot.write(['KICK', channel, nick, ' :', reason])


@command('topic')
def topic(bot, trigger):
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
    if bot.db and channel in bot.db.preferences:
        mask = bot.db.preferences.get(channel, 'topic_mask')
        narg = len(re.findall('%s', mask))
    if not mask or mask == '':
        mask = purple + 'Welcome to: ' + green + channel + purple \
            + ' | ' + bold + 'Topic: ' + bold + green + '%s'

    top = trigger.group(2)
    text = tuple()
    if top:
        text = tuple(unicode.split(top, '~', narg))

    if len(text) != narg:
        message = "Not enough arguments. You gave " + str(len(text)) + ', it requires ' + str(narg) + '.'
        return bot.say(message)
    topic = mask % text

    bot.write(('TOPIC', channel + ' :' + topic))


@command('tmask')
def set_mask(bot, trigger):
    """
    Set the mask to use for .topic in the current channel. %s is used to allow
    substituting in chunks of text.
    """
    if not trigger.isop:
        return
    if not bot.db:
        bot.say("I'm afraid I can't do that.")
    else:
        bot.db.preferences.update(trigger.sender, {'topic_mask': trigger.group(2)})
        bot.say("Gotcha, " + trigger.nick)


@command('showmask')
def show_mask(bot, trigger):
    """Show the topic mask for the current channel."""
    if not trigger.isop:
        return
    if not bot.db:
        bot.say("I'm afraid I can't do that.")
    elif trigger.sender in bot.db.preferences:
        bot.say(bot.db.preferences.get(trigger.sender, 'topic_mask'))
    else:
        bot.say("%s")


@command('isop')
def isop(bot, trigger):
    """Show if you are an operator in the current channel"""
    if trigger.isop:
        bot.reply('yes')
    else:
        bot.reply('no')
