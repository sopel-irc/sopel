# coding=utf-8
"""
adminchannel.py - Sopel Channel Admin Module
Copyright 2010-2011, Michael Yanovich, Alek Rollyson, and Elsie Powell
Copyright © 2012, Elad Alfassa <elad@fedoraproject.org>
Licensed under the Eiffel Forum License 2.

https://sopel.chat
"""
from __future__ import unicode_literals, absolute_import, print_function, division

import re

from sopel import formatting
from sopel.module import (
    commands, example, priority, OP, HALFOP, require_privilege, require_chanmsg
)
from sopel.tools import Identifier


def default_mask(trigger):
    welcome = formatting.color('Welcome to:', formatting.colors.PURPLE)
    chan = formatting.color(trigger.sender, formatting.colors.TEAL)
    topic_ = formatting.bold('Topic:')
    topic_ = formatting.color('| ' + topic_, formatting.colors.PURPLE)
    arg = formatting.color('{}', formatting.colors.GREEN)
    return '{} {} {} {}'.format(welcome, chan, topic_, arg)


@require_chanmsg
@require_privilege(OP, 'You are not a channel operator.')
@commands('op')
def op(bot, trigger):
    """
    Command to op users in a room. If no nick is given,
    Sopel will op the nick who sent the command
    """
    if bot.channels[trigger.sender].privileges[bot.nick] < OP:
        return bot.reply("I'm not a channel operator!")
    nick = trigger.group(2)
    channel = trigger.sender
    if not nick:
        nick = trigger.nick
    bot.write(['MODE', channel, "+o", nick])


@require_chanmsg
@require_privilege(OP, 'You are not a channel operator.')
@commands('deop')
def deop(bot, trigger):
    """
    Command to deop users in a room. If no nick is given,
    Sopel will deop the nick who sent the command
    """
    if bot.channels[trigger.sender].privileges[bot.nick] < OP:
        return bot.reply("I'm not a channel operator!")
    nick = trigger.group(2)
    channel = trigger.sender
    if not nick:
        nick = trigger.nick
    bot.write(['MODE', channel, "-o", nick])


@require_chanmsg
@require_privilege(OP, 'You are not a channel operator.')
@commands('voice')
def voice(bot, trigger):
    """
    Command to voice users in a room. If no nick is given,
    Sopel will voice the nick who sent the command
    """
    if bot.channels[trigger.sender].privileges[bot.nick] < HALFOP:
        return bot.reply("I'm not a channel operator!")
    nick = trigger.group(2)
    channel = trigger.sender
    if not nick:
        nick = trigger.nick
    bot.write(['MODE', channel, "+v", nick])


@require_chanmsg
@require_privilege(OP, 'You are not a channel operator.')
@commands('devoice')
def devoice(bot, trigger):
    """
    Command to devoice users in a room. If no nick is given,
    Sopel will devoice the nick who sent the command
    """
    if bot.channels[trigger.sender].privileges[bot.nick] < HALFOP:
        return bot.reply("I'm not a channel operator!")
    nick = trigger.group(2)
    channel = trigger.sender
    if not nick:
        nick = trigger.nick
    bot.write(['MODE', channel, "-v", nick])


@require_chanmsg
@require_privilege(OP, 'You are not a channel operator.')
@commands('kick')
@priority('high')
def kick(bot, trigger):
    """Kick a user from the channel."""
    if bot.channels[trigger.sender].privileges[bot.nick] < HALFOP:
        return bot.reply("I'm not a channel operator!")
    text = trigger.group().split()
    argc = len(text)
    if argc < 2:
        return
    opt = Identifier(text[1])
    nick = opt
    channel = trigger.sender
    reasonidx = 2
    if not opt.is_nick():
        if argc < 3:
            return
        nick = text[2]
        channel = opt
        reasonidx = 3
    reason = ' '.join(text[reasonidx:])
    if nick != bot.config.core.nick:
        bot.kick(nick, channel, reason)


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

    if re.match(r'^\S+[!]\S+[@]\S+$', mask) is not None:
        return mask
    return ''


@require_chanmsg
@require_privilege(OP, 'You are not a channel operator.')
@commands('ban')
@priority('high')
def ban(bot, trigger):
    """Ban a user from the channel

    The bot must be a channel operator for this command to work.
    """
    if bot.channels[trigger.sender].privileges[bot.nick] < HALFOP:
        return bot.reply("I'm not a channel operator!")
    text = trigger.group().split()
    argc = len(text)
    if argc < 2:
        return
    opt = Identifier(text[1])
    banmask = opt
    channel = trigger.sender
    if not opt.is_nick():
        if argc < 3:
            return
        channel = opt
        banmask = text[2]
    banmask = configureHostMask(banmask)
    if banmask == '':
        return
    bot.write(['MODE', channel, '+b', banmask])


@require_chanmsg
@require_privilege(OP, 'You are not a channel operator.')
@commands('unban')
def unban(bot, trigger):
    """Unban a user from the channel

    The bot must be a channel operator for this command to work.
    """
    if bot.channels[trigger.sender].privileges[bot.nick] < HALFOP:
        return bot.reply("I'm not a channel operator!")
    text = trigger.group().split()
    argc = len(text)
    if argc < 2:
        return
    opt = Identifier(text[1])
    banmask = opt
    channel = trigger.sender
    if not opt.is_nick():
        if argc < 3:
            return
        channel = opt
        banmask = text[2]
    banmask = configureHostMask(banmask)
    if banmask == '':
        return
    bot.write(['MODE', channel, '-b', banmask])


@require_chanmsg
@require_privilege(OP, 'You are not a channel operator.')
@commands('quiet')
def quiet(bot, trigger):
    """Quiet a user

    The bot must be a channel operator for this command to work.
    """
    if bot.channels[trigger.sender].privileges[bot.nick] < OP:
        return bot.reply("I'm not a channel operator!")
    text = trigger.group().split()
    argc = len(text)
    if argc < 2:
        return
    opt = Identifier(text[1])
    quietmask = opt
    channel = trigger.sender
    if not opt.is_nick():
        if argc < 3:
            return
        quietmask = text[2]
        channel = opt
    quietmask = configureHostMask(quietmask)
    if quietmask == '':
        return
    bot.write(['MODE', channel, '+q', quietmask])


@require_chanmsg
@require_privilege(OP, 'You are not a channel operator.')
@commands('unquiet')
def unquiet(bot, trigger):
    """Unquiet a user

    The bot must be a channel operator for this command to work.
    """
    if bot.channels[trigger.sender].privileges[bot.nick] < OP:
        return bot.reply("I'm not a channel operator!")
    text = trigger.group().split()
    argc = len(text)
    if argc < 2:
        return
    opt = Identifier(text[1])
    quietmask = opt
    channel = trigger.sender
    if not opt.is_nick():
        if argc < 3:
            return
        quietmask = text[2]
        channel = opt
    quietmask = configureHostMask(quietmask)
    if quietmask == '':
        return
    bot.write(['MODE', channel, '-q', quietmask])


@require_chanmsg
@require_privilege(OP, 'You are not a channel operator.')
@commands('kickban', 'kb')
@example('.kickban [#chan] user1 user!*@* get out of here')
@priority('high')
def kickban(bot, trigger):
    """Kick and ban a user from the channel

    The bot must be a channel operator for this command to work.
    """
    if bot.channels[trigger.sender].privileges[bot.nick] < HALFOP:
        return bot.reply("I'm not a channel operator!")
    text = trigger.group().split()
    argc = len(text)
    if argc < 4:
        return
    opt = Identifier(text[1])
    nick = opt
    mask = text[2]
    channel = trigger.sender
    reasonidx = 3
    if not opt.is_nick():
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
    bot.kick(nick, channel, reason)


@require_chanmsg
@require_privilege(OP, 'You are not a channel operator.')
@commands('topic')
def topic(bot, trigger):
    """Change the channel topic

    The bot must be a channel operator for this command to work.
    """
    if bot.channels[trigger.sender].privileges[bot.nick] < HALFOP:
        return bot.reply("I'm not a channel operator!")
    if not trigger.group(2):
        return
    channel = trigger.sender.lower()

    mask = None
    mask = bot.db.get_channel_value(channel, 'topic_mask')
    mask = mask or default_mask(trigger)
    mask = mask.replace('%s', '{}')
    narg = len(re.findall('{}', mask))

    top = trigger.group(2)
    args = []
    if top:
        args = top.split('~', narg)

    if len(args) != narg:
        message = "Not enough arguments. You gave {}, it requires {}.".format(
            len(args), narg)
        return bot.say(message)
    topic = mask.format(*args)

    bot.write(('TOPIC', channel + ' :' + topic))


@require_chanmsg
@require_privilege(OP, 'You are not a channel operator.')
@commands('tmask')
def set_mask(bot, trigger):
    """Set the topic mask to use for the current channel

    Within the topic mask, {} is used to allow substituting in chunks of text.

    This mask is used when running the 'topic' command.
    """
    bot.db.set_channel_value(trigger.sender, 'topic_mask', trigger.group(2))
    bot.say("Gotcha, " + trigger.nick)


@require_chanmsg
@require_privilege(OP, 'You are not a channel operator.')
@commands('showmask')
def show_mask(bot, trigger):
    """Show the topic mask for the current channel."""
    bot.say(bot.db.get_channel_value(trigger.sender, 'topic_mask', default_mask(trigger)))
