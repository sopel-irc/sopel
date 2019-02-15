# coding=utf-8
# Copyright 2010-2011, Michael Yanovich, Alek Rollyson, and Elsie Powell
# Copyright © 2012, Elad Alfassa <elad@fedoraproject.org>
# Licensed under the Eiffel Forum License 2.
from __future__ import unicode_literals, absolute_import, print_function, division

import re
from sopel import formatting
from sopel.module import commands, priority, OP, HALFOP, require_privilege, require_chanmsg
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
@commands('kick')
@priority('high')
def kick(bot, trigger):
    """
    Kick a user from the channel.
    """
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
        bot.write(['KICK', channel, nick], reason)


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


@require_chanmsg
@require_privilege(OP, 'You are not a channel operator.')
@commands('ban')
@priority('high')
def ban(bot, trigger):
    """
    This give admins the ability to ban a user.
    The bot must be a Channel Operator for this command to work.
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
    """
    This give admins the ability to unban a user.
    The bot must be a Channel Operator for this command to work.
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
    """
    This gives admins the ability to quiet a user.
    The bot must be a Channel Operator for this command to work.
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
    """
    This gives admins the ability to unquiet a user.
    The bot must be a Channel Operator for this command to work.
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
@priority('high')
def kickban(bot, trigger):
    """
    This gives admins the ability to kickban a user.
    The bot must be a Channel Operator for this command to work.
    .kickban [#chan] user1 user!*@* get out of here
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
    bot.write(['KICK', channel, nick], reason)


@require_chanmsg
@require_privilege(OP, 'You are not a channel operator.')
@commands('topic')
def topic(bot, trigger):
    """
    This gives ops the ability to change the topic.
    The bot must be a Channel Operator for this command to work.
    """
    if bot.channels[trigger.sender].privileges[bot.nick] < HALFOP:
        return bot.reply("I'm not a channel operator!")
    if not trigger.group(2):
        return
    channel = trigger.sender.lower()

    narg = 1
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
    """
    Set the mask to use for .topic in the current channel. {} is used to allow
    substituting in chunks of text.
    """
    bot.db.set_channel_value(trigger.sender, 'topic_mask', trigger.group(2))
    bot.say("Gotcha, " + trigger.nick)


@require_chanmsg
@require_privilege(OP, 'You are not a channel operator.')
@commands('showmask')
def show_mask(bot, trigger):
    """Show the topic mask for the current channel."""
    mask = bot.db.get_channel_value(trigger.sender, 'topic_mask')
    mask = mask or default_mask(trigger)
    bot.say(mask)
