# coding=utf-8
"""
coretasks.py - Willie Ruotine Core tasks
Copyright 2008-2011, Sean B. Palmer (inamidst.com) and Michael Yanovich
(yanovich.net)
Copyright © 2012, Elad Alfassa <elad@fedoraproject.org>
Copyright 2012, Edward Powell (embolalia.net)
Licensed under the Eiffel Forum License 2.

Willie: http://willie.dftba.net/

This is written as a module to make it easier to extend to support more
responses to standard IRC codes without having to shove them all into the
dispatch function in bot.py and making it easier to maintain.
"""
import re
import threading
import time
import willie
from willie.tools import Nick


@willie.module.event('251')
@willie.module.rule('.*')
@willie.module.priority('low')
def startup(bot, trigger):
    """
    Runs when we recived 251 - lusers, which is just before the server sends the
    motd, and right after establishing a sucessful connection.
    """
    if bot.config.core.nickserv_password is not None:
        bot.msg('NickServ', 'IDENTIFY %s'
                   % bot.config.core.nickserv_password)

    if (bot.config.core.oper_name is not None
            and bot.config.core.oper_password is not None):
        bot.write(('OPER', bot.config.core.oper_name + ' '
                     + bot.config.oper_password))

    #Set bot modes per config, +B if no config option is defined
    if bot.config.has_option('core', 'modes'):
        modes = bot.config.core.modes
    else:
        modes = 'B'
    bot.write(('MODE ', '%s +%s' % (bot.nick, modes)))

    for channel in bot.config.core.get_list('channels'):
        bot.write(('JOIN', channel))

#Functions to maintain a list of chanops in all of willie's channels.


@willie.module.command('newoplist')
def refresh_list(bot, trigger):
    ''' If you need to use this, then it means you found a bug '''
    if trigger.admin:
        bot.reply('Refreshing ops list for ' + trigger.sender + '.')
        bot.flushOps(trigger.sender)
        bot.write(('NAMES', trigger.sender))


@willie.module.command('listops')
def list_ops(bot, trigger):
    """
    List channel operators in the given channel, or current channel if none is
    given.
    """
    if trigger.group(2):
        bot.say(trigger.group(2))
        if trigger.group(2) in bot.ops:
            bot.say(str(bot.ops[channel]))
        else:
            bot.say('None')
    else:
        if trigger.sender in bot.ops:
            bot.say(str(bot.ops[trigger.sender]))
        else:
            bot.say('None')


@willie.module.command('listvoices')
def list_voices(bot, trigger):
    """
    List users with voice in the given channel, or current channel if none is
    given.
    """
    if trigger.group(2):
        bot.say(trigger.group(2))
        if trigger.group(2) in bot.voices:
            bot.say(str(bot.voices[channel]))
        else:
            bot.say('None')
    else:
        if trigger.sender in bot.voices:
            bot.say(str(bot.voices[trigger.sender]))
        else:
            bot.say('None')


@willie.module.rule('(.*)')
@willie.module.event('353')
@willie.module.thread(False)
def handle_names(bot, trigger):
    ''' Handle NAMES response, happens when joining to channels'''
    names = re.split(' ', trigger)
    channels = re.search('(#\S*)', bot.raw)
    if (channels is None):
        return
    channel = channels.group(1)
    bot.init_ops_list(channel)
    for name in names:
        if '@' in name or '~' in name or '&' in name:
            bot.add_op(channel, name.lstrip('@&%+~'))
            bot.add_halfop(channel, name.lstrip('@&%+~'))
            bot.add_voice(channel, name.lstrip('@&%+~'))
        elif '%' in name:
            bot.add_halfop(channel, name.lstrip('@&%+~'))
            bot.add_voice(channel, name.lstrip('@&%+~'))
        elif '+' in name:
            bot.add_voice(channel, name.lstrip('@&%+~'))


@willie.module.rule('(.*)')
@willie.module.event('MODE')
def track_modes(bot, trigger):
    ''' Track usermode changes and keep our lists of ops up to date '''
    # 0 is who set it, 1 is MODE. We don't need those.
    line = bot.raw.split(' ')[2:]

    # If the first character of where the mode is being set isn't a #
    # then it's a user mode, not a channel mode, so we'll ignore it.
    if line[0][0] != '#':
        return
    channel, mode_sec = line[:2]
    nicks = line[2:]

    # Break out the modes, because IRC allows e.g. MODE +aB-c foo bar baz
    sign = ''
    modes = []
    for char in mode_sec:
        if char == '+' or char == '-':
            sign = char
        else:
            modes.append(sign + char)

    # Some basic checks for broken replies from server. Probably unnecessary.
    if len(modes) > len(nicks):
        bot.debug('core',
                     'MODE recieved from server with more modes than nicks.',
                     'warning')
        modes = modes[:(len(nicks) + 1)]  # Try truncating, in case that works.
    elif len(modes) < len(nicks):
        bot.debug('core',
                     'MODE recieved from server with more nicks than modes.',
                     'warning')
        nicks = nicks[:(len(modes) - 1)]  # Try truncating, in case that works.
    # This one is almost certainly unneeded.
    if not (len(modes) and len(nicks)):
        bot.debug('core', 'MODE recieved from server without arguments',
                     'verbose')
        return  # Nothing to do here.

    for nick, mode in zip(nicks, modes):
        if mode[1] == 'o' or mode[1] == 'q':  # Op or owner (for UnrealIRCd)
            if mode[0] == '+':
                bot.add_op(channel, nick)
            else:
                bot.del_op(channel, nick)
        elif mode[1] == 'h':  # Halfop
            if mode[0] == '+':
                bot.add_halfop(channel, nick)
            else:
                bot.del_halfop(channel, nick)
        elif mode[1] == 'v':
            if mode[0] == '+':
                bot.add_voice(channel, nick)
            else:
                bot.del_voice(channel, nick)


@willie.module.rule('.*')
@willie.module.event('NICK')
def track_nicks(bot, trigger):
    '''Track nickname changes and maintain our chanops list accordingly'''
    old = trigger.nick
    new = Nick(trigger)

    # Give debug mssage, and PM the owner, if the bot's own nick changes.
    if old == bot.nick:
        privmsg = "Hi, I'm your bot, %s. Something has made my nick change. This can cause some problems for me, and make me do weird things. You'll probably want to restart me, and figure out what made that happen so you can stop it happening again. (Usually, it means you tried to give me a nick that's protected by NickServ.)" % bot.nick
        debug_msg = "Nick changed by server. This can cause unexpected behavior. Please restart the bot."
        bot.debug('[CORE]', debug_msg, 'always')
        bot.msg(bot.config.core.owner, privmsg)
        return

    for channel in bot.halfplus:
        if old in bot.halfplus[channel]:
            bot.del_halfop(channel, old)
            bot.add_halfop(channel, new)
    for channel in bot.ops:
        if old in bot.ops[channel]:
            bot.del_op(channel, old)
            bot.add_op(channel, new)
    for channel in bot.voices:
        if old in bot.voices[channel]:
            bot.del_voice(channel, old)
            bot.add_voice(channel, new)


@willie.module.rule('(.*)')
@willie.module.event('PART')
def track_part(bot, trigger):
    if trigger.nick == bot.nick:
        bot.channels.remove(trigger.sender)


@willie.module.rule('.*')
@willie.module.event('KICK')
def track_kick(bot, trigger):
    if trigger.args[1] == bot.nick:
        bot.channels.remove(trigger.sender)


@willie.module.rule('.*')
@willie.module.event('JOIN')
def track_join(bot, trigger):
    if trigger.nick == bot.nick and trigger.sender not in bot.channels:
        bot.channels.append(trigger.sender)

#Live blocklist editing


@willie.module.command('blocks')
@willie.module.priority('low')
@willie.module.thread(False)
def blocks(bot, trigger):
    """
    Manage Willie's blocking features.
    https://github.com/embolalia/willie/wiki/Making-Willie-ignore-people
    """
    if not trigger.admin:
        return

    STRINGS = {
        "success_del": "Successfully deleted block: %s",
        "success_add": "Successfully added block: %s",
        "no_nick": "No matching nick block found for: %s",
        "no_host": "No matching hostmask block found for: %s",
        "invalid": "Invalid format for %s a block. Try: .blocks add (nick|hostmask) willie",
        "invalid_display": "Invalid input for displaying blocks.",
        "nonelisted": "No %s listed in the blocklist.",
        'huh': "I could not figure out what you wanted to do.",
    }

    masks = bot.config.core.get_list('host_blocks')
    nicks = [Nick(nick) for nick in bot.config.core.get_list('nick_blocks')]
    print masks, nicks
    text = trigger.group().split()

    if len(text) == 3 and text[1] == "list":
        if text[2] == "hostmask":
            if len(masks) > 0 and masks.count("") == 0:
                for each in masks:
                    if len(each) > 0:
                        bot.say("blocked hostmask: " + each)
            else:
                bot.reply(STRINGS['nonelisted'] % ('hostmasks'))
        elif text[2] == "nick":
            if len(nicks) > 0 and nicks.count("") == 0:
                for each in nicks:
                    if len(each) > 0:
                        bot.say("blocked nick: " + each)
            else:
                bot.reply(STRINGS['nonelisted'] % ('nicks'))
        else:
            bot.reply(STRINGS['invalid_display'])

    elif len(text) == 4 and text[1] == "add":
        if text[2] == "nick":
            nicks.append(text[3])
            bot.config.core.nick_blocks = nicks
            bot.config.save()
        elif text[2] == "hostmask":
            masks.append(text[3].lower())
            bot.config.core.host_blocks = masks
        else:
            bot.reply(STRINGS['invalid'] % ("adding"))
            return

        bot.reply(STRINGS['success_add'] % (text[3]))

    elif len(text) == 4 and text[1] == "del":
        if text[2] == "nick":
            try:
                nicks.remove(Nick(text[3]))
                bot.config.core.nick_blocks = nicks
                bot.config.save()
                bot.reply(STRINGS['success_del'] % (text[3]))
            except:
                bot.reply(STRINGS['no_nick'] % (text[3]))
                return
        elif text[2] == "hostmask":
            try:
                masks.remove(text[3].lower())
                bot.config.core.host_blocks = masks
                bot.config.save()
                bot.reply(STRINGS['success_del'] % (text[3]))
            except:
                bot.reply(STRINGS['no_host'] % (text[3]))
                return
        else:
            bot.reply(STRINGS['invalid'] % ("deleting"))
            return
    else:
        bot.reply(STRINGS['huh'])
