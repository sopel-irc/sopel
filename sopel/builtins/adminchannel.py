"""
adminchannel.py - Sopel Channel Admin Plugin
Copyright 2010-2011, Michael Yanovich, Alek Rollyson, and Elsie Powell
Copyright © 2012, Elad Alfassa <elad@fedoraproject.org>
Licensed under the Eiffel Forum License 2.

https://sopel.chat
"""
from __future__ import annotations

import re

from sopel import formatting, plugin


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
@plugin.priority(plugin.Priority.HIGH)
def kick(bot, trigger):
    """Kick a user from the channel."""
    text = trigger.group().split()
    argc = len(text)
    if argc < 2:
        return
    opt = bot.make_identifier(text[1])
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

    if nick == bot.nick:
        bot.reply("Hey! Don't kick me. :(")
        return

    bot.kick(nick, channel, reason)


def configureHostMask(mask):
    # shortcut for nick!*@*
    if re.match(r'^[^.@!/\s]+$', mask) is not None:
        return '%s!*@*' % mask

    # shortcut for *!*@host
    # won't work for local names w/o dot, but does support cloaks/with/slashes
    if re.match(r'^[^@!\s]+$', mask) is not None:
        return '*!*@%s' % mask

    # shortcut for *!user@*
    # requires trailing @ to be recognized as a username instead of a nick
    m = re.match(r'^([^!@\s]+)@$', mask)
    if m is not None:
        return '*!%s@*' % m.group(1)

    # shortcut for *!user@host
    m = re.match(r'^([^!@\s]+)@([^@!\s]+)$', mask)
    if m is not None:
        return '*!%s@%s' % (m.group(1), m.group(2))

    # shortcut for nick!user@*
    m = re.match(r'^([^!@\s]+)!([^!@\s]+)@?$', mask)
    if m is not None:
        return '%s!%s@*' % (m.group(1), m.group(2))

    # not a shortcut; validate full NUH format
    if re.match(r'^[^!@\s]+![^!@\s]+@[^!@\s]+$', mask) is not None:
        return mask

    # not a shortcut nor a valid hostmask
    raise ValueError('Invalid hostmask format or unsupported shorthand')


@plugin.require_chanmsg
@plugin.require_privilege(plugin.OP, ERROR_MESSAGE_NO_PRIV, reply=True)
@plugin.require_bot_privilege(plugin.HALFOP, ERROR_MESSAGE_NOT_OP, reply=True)
@plugin.command('ban')
@plugin.priority(plugin.Priority.HIGH)
def ban(bot, trigger):
    """Ban a user from the channel

    The bot must be a channel operator for this command to work.
    """
    text = trigger.group().split()
    argc = len(text)
    if argc < 2:
        return
    opt = bot.make_identifier(text[1])
    banmask = opt
    channel = trigger.sender
    if not opt.is_nick():
        if argc < 3:
            return
        channel = opt
        banmask = text[2]

    try:
        banmask = configureHostMask(banmask)
    except ValueError:
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
    opt = bot.make_identifier(text[1])
    banmask = opt
    channel = trigger.sender
    if not opt.is_nick():
        if argc < 3:
            return
        channel = opt
        banmask = text[2]

    try:
        banmask = configureHostMask(banmask)
    except ValueError:
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
    opt = bot.make_identifier(text[1])
    quietmask = opt
    channel = trigger.sender
    if not opt.is_nick():
        if argc < 3:
            return
        quietmask = text[2]
        channel = opt

    try:
        quietmask = configureHostMask(quietmask)
    except ValueError:
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
    opt = bot.make_identifier(text[1])
    quietmask = opt
    channel = trigger.sender
    if not opt.is_nick():
        if argc < 3:
            return
        quietmask = text[2]
        channel = opt

    try:
        quietmask = configureHostMask(quietmask)
    except ValueError:
        return

    bot.write(['MODE', channel, '-q', quietmask])


@plugin.require_chanmsg
@plugin.require_privilege(plugin.OP, ERROR_MESSAGE_NO_PRIV, reply=True)
@plugin.require_bot_privilege(plugin.OP, ERROR_MESSAGE_NOT_OP, reply=True)
@plugin.command('kickban', 'kb')
@plugin.example('.kickban [#chan] user1 user!*@* get out of here')
@plugin.priority(plugin.Priority.HIGH)
def kickban(bot, trigger):
    """Kick and ban a user from the channel

    The bot must be a channel operator for this command to work.
    """
    text = trigger.group().split()
    argc = len(text)
    if argc < 4:
        return
    opt = bot.make_identifier(text[1])
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

    try:
        mask = configureHostMask(mask)
    except ValueError:
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

    mask = bot.db.get_channel_value(
        channel, 'topic_mask', default_mask(trigger))
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


@plugin.require_privilege(plugin.OP, ERROR_MESSAGE_NO_PRIV)
@plugin.commands('tmask set', 'tmask get', 'tmask clear', 'tmask')
@plugin.example('.tmask clear', user_help=True)
@plugin.example('.tmask get', user_help=True)
@plugin.example('.tmask set My {} topic mask!', user_help=True)
def topic_mask_management(bot, trigger):
    """Set, get, or clear the current channel's topic mask.

    Recognized subcommands are 'set', 'get', and 'clear'. A plain 'tmask'
    command with no arguments is equivalent to 'tmask get'.

    This mask is used by the 'topic' command. `{}` allows interpolating a chunk
    of text within the topic mask template.
    """
    command, _, subcommand = trigger.group(1).partition(' ')

    if not subcommand or subcommand == 'get':
        mask = bot.db.get_channel_value(
            trigger.sender, 'topic_mask', default_mask(trigger))
        bot.reply('Current topic mask: {}'.format(mask))
        return

    if subcommand == 'set':
        if not trigger.group(2):
            message = (
                'I need a non-empty topic mask to set. '
                'To delete the saved topic mask, use `{prefix}tmask clear`.'
            ).format(prefix=bot.settings.core.help_prefix)
            bot.reply(message)
            return

        bot.db.set_channel_value(trigger.sender, 'topic_mask', trigger.group(2))
        message = (
            'Topic mask set. '
            'Use `{prefix}topic <args>` to set topic, '
            '`{prefix}tmask get` to see the current mask, '
            'and `{prefix}tmask clear` to delete the saved topic mask.'
        ).format(prefix=bot.settings.core.help_prefix)
        bot.reply(message)
        return

    if subcommand == 'clear':
        bot.db.delete_channel_value(trigger.sender, 'topic_mask')
        bot.reply('Cleared topic mask.')
        return
