# coding=utf-8
"""
adminchannel.py - Sopel Channel Admin Plugin
Copyright 2010-2011, Michael Yanovich, Alek Rollyson, and Elsie Powell
Copyright © 2012, Elad Alfassa <elad@fedoraproject.org>
Licensed under the Eiffel Forum License 2.

https://sopel.chat
"""
from __future__ import absolute_import, division, print_function, unicode_literals

import re

from sopel import formatting, plugin, tools


ERROR_MESSAGE_NOT_OP = "I'm not a channel operator!"
ERROR_MESSAGE_NO_PRIV = "You are not a channel operator."


def default_mask(trigger):
    welcome = formatting.color('Welcome to:', formatting.colors.PURPLE)
    chan = formatting.color(trigger.sender, formatting.colors.TEAL)
    topic_ = formatting.bold('Topic:')
    topic_ = formatting.color('| ' + topic_, formatting.colors.PURPLE)
    arg = formatting.color('{}', formatting.colors.GREEN)
    return '{} {} {} {}'.format(welcome, chan, topic_, arg)


@plugin.require_chanmsg
@plugin.require_privilege(plugin.OP, ERROR_MESSAGE_NO_PRIV, reply=True)
@plugin.require_bot_privilege(plugin.OP, ERROR_MESSAGE_NOT_OP, reply=True)
@plugin.command('op')
def op(bot, trigger):
    """
    Command to op users in a room. If no nick is given,
    Sopel will op the nick who sent the command
    """
    nick = trigger.group(2)
    channel = trigger.sender
    if not nick:
        nick = trigger.nick
    bot.write(['MODE', channel, "+o", nick])


@plugin.require_chanmsg
@plugin.require_privilege(plugin.OP, ERROR_MESSAGE_NO_PRIV, reply=True)
@plugin.require_bot_privilege(plugin.OP, ERROR_MESSAGE_NOT_OP, reply=True)
@plugin.command('deop')
def deop(bot, trigger):
    """
    Command to deop users in a room. If no nick is given,
    Sopel will deop the nick who sent the command
    """
    nick = trigger.group(2)
    channel = trigger.sender
    if not nick:
        nick = trigger.nick
    bot.write(['MODE', channel, "-o", nick])


@plugin.require_chanmsg
@plugin.require_privilege(plugin.OP, ERROR_MESSAGE_NO_PRIV, reply=True)
@plugin.require_bot_privilege(plugin.HALFOP, ERROR_MESSAGE_NOT_OP, reply=True)
@plugin.command('voice')
def voice(bot, trigger):
    """
    Command to voice users in a room. If no nick is given,
    Sopel will voice the nick who sent the command
    """
    nick = trigger.group(2)
    channel = trigger.sender
    if not nick:
        nick = trigger.nick
    bot.write(['MODE', channel, "+v", nick])


@plugin.require_chanmsg
@plugin.require_privilege(plugin.OP, ERROR_MESSAGE_NO_PRIV, reply=True)
@plugin.require_bot_privilege(plugin.HALFOP, ERROR_MESSAGE_NOT_OP, reply=True)
@plugin.command('devoice')
def devoice(bot, trigger):
    """
    Command to devoice users in a room. If no nick is given,
    Sopel will devoice the nick who sent the command
    """
    nick = trigger.group(2)
    channel = trigger.sender
    if not nick:
        nick = trigger.nick
    bot.write(['MODE', channel, "-v", nick])


@plugin.require_chanmsg
@plugin.require_privilege(plugin.OP, ERROR_MESSAGE_NO_PRIV, reply=True)
@plugin.require_bot_privilege(plugin.HALFOP, ERROR_MESSAGE_NOT_OP, reply=True)
@plugin.command('kick')
@plugin.priority('high')
def kick(bot, trigger):
    """Kick a user from the channel."""
    text = trigger.group().split()
    argc = len(text)
    if argc < 2:
        return
    opt = tools.Identifier(text[1])
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


@plugin.require_chanmsg
@plugin.require_privilege(plugin.OP, ERROR_MESSAGE_NO_PRIV, reply=True)
@plugin.require_bot_privilege(plugin.HALFOP, ERROR_MESSAGE_NOT_OP, reply=True)
@plugin.command('ban')
@plugin.priority('high')
def ban(bot, trigger):
    """Ban a user from the channel

    The bot must be a channel operator for this command to work.
    """
    text = trigger.group().split()
    argc = len(text)
    if argc < 2:
        return
    opt = tools.Identifier(text[1])
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


@plugin.require_chanmsg
@plugin.require_privilege(plugin.OP, ERROR_MESSAGE_NO_PRIV, reply=True)
@plugin.require_bot_privilege(plugin.HALFOP, ERROR_MESSAGE_NOT_OP, reply=True)
@plugin.command('unban')
def unban(bot, trigger):
    """Unban a user from the channel

    The bot must be a channel operator for this command to work.
    """
    text = trigger.group().split()
    argc = len(text)
    if argc < 2:
        return
    opt = tools.Identifier(text[1])
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


@plugin.require_chanmsg
@plugin.require_privilege(plugin.OP, ERROR_MESSAGE_NO_PRIV, reply=True)
@plugin.require_bot_privilege(plugin.OP, ERROR_MESSAGE_NOT_OP, reply=True)
@plugin.command('quiet')
def quiet(bot, trigger):
    """Quiet a user

    The bot must be a channel operator for this command to work.
    """
    text = trigger.group().split()
    argc = len(text)
    if argc < 2:
        return
    opt = tools.Identifier(text[1])
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


@plugin.require_chanmsg
@plugin.require_privilege(plugin.OP, ERROR_MESSAGE_NO_PRIV, reply=True)
@plugin.require_bot_privilege(plugin.OP, ERROR_MESSAGE_NOT_OP, reply=True)
@plugin.command('unquiet')
def unquiet(bot, trigger):
    """Unquiet a user

    The bot must be a channel operator for this command to work.
    """
    text = trigger.group().split()
    argc = len(text)
    if argc < 2:
        return
    opt = tools.Identifier(text[1])
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


@plugin.require_chanmsg
@plugin.require_privilege(plugin.OP, ERROR_MESSAGE_NO_PRIV, reply=True)
@plugin.require_bot_privilege(plugin.OP, ERROR_MESSAGE_NOT_OP, reply=True)
@plugin.command('kickban', 'kb')
@plugin.example('.kickban [#chan] user1 user!*@* get out of here')
@plugin.priority('high')
def kickban(bot, trigger):
    """Kick and ban a user from the channel

    The bot must be a channel operator for this command to work.
    """
    text = trigger.group().split()
    argc = len(text)
    if argc < 4:
        return
    opt = tools.Identifier(text[1])
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


@plugin.require_chanmsg
@plugin.command('topic')
def topic(bot, trigger):
    """Change the channel topic

    The bot must be a channel operator for this command to work in +t channels.
    """
    mode_t = bot.channels[trigger.sender].modes.get("t", False)
    if mode_t and not bot.has_channel_privilege(trigger.sender, plugin.HALFOP):
        bot.reply(ERROR_MESSAGE_NOT_OP)
        return
    if mode_t and bot.channels[trigger.sender].privileges[trigger.nick] < plugin.HALFOP:
        bot.reply(ERROR_MESSAGE_NO_PRIV)
        return
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
        message = "Not enough arguments. You gave {}; it requires {}.".format(
            len(args), narg)
        bot.reply(message)
        return
    topic = mask.format(*args)

    topiclen = getattr(bot.isupport, 'TOPICLEN', None)
    if topiclen is not None:
        my_len = len(topic.encode('utf-8'))
        if my_len > topiclen:
            bot.reply(
                "Formatted topic is too long ({} bytes); "
                "the server limit is {} bytes."
                .format(my_len, topiclen))
            return

    bot.write(('TOPIC', channel + ' :' + topic))


@plugin.require_chanmsg
@plugin.require_privilege(plugin.OP, ERROR_MESSAGE_NO_PRIV)
@plugin.command('tmask')
def set_mask(bot, trigger):
    """Set the topic mask to use for the current channel

    Within the topic mask, {} is used to allow substituting in chunks of text.

    This mask is used when running the 'topic' command.
    """
    bot.db.set_channel_value(trigger.sender, 'topic_mask', trigger.group(2))
    message = (
        'Topic mask set. '
        'Use `{prefix}topic <args>` to set topic '
        'and `{prefix}showmask` to see current mask.'
    ).format(prefix=bot.settings.core.help_prefix)
    bot.reply(message)


@plugin.require_chanmsg
@plugin.require_privilege(plugin.OP, ERROR_MESSAGE_NO_PRIV)
@plugin.command('showmask')
def show_mask(bot, trigger):
    """Show the topic mask for the current channel."""
    bot.say(bot.db.get_channel_value(trigger.sender, 'topic_mask', default_mask(trigger)))
