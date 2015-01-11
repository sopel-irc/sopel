# coding=utf8
"""
coretasks.py - Willie Routine Core tasks
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
from __future__ import unicode_literals


import re
import time
import willie
from willie.tools import Identifier, iteritems
import base64
from willie.logger import get_logger

LOGGER = get_logger(__name__)


@willie.module.event('001', '251')
@willie.module.rule('.*')
@willie.module.thread(False)
@willie.module.unblockable
def startup(bot, trigger):
    """Do tasks related to connecting to the network.

    001 RPL_WELCOME is from RFC2812 and is the first message that is sent after
    the connection has been registered on the network.

    251 RPL_LUSERCLIENT is a mandatory message that is sent after client
    connects to the server in rfc1459. RFC2812 does not require it and all
    networks might not send it. We support both.

    """
    if bot.connection_registered:
        return

    bot.connection_registered = True

    if bot.config.core.nickserv_password is not None:
        bot.msg(
            'NickServ',
            'IDENTIFY %s' % bot.config.core.nickserv_password
        )

    if (bot.config.core.oper_name is not None
            and bot.config.core.oper_password is not None):
        bot.write((
            'OPER',
            bot.config.core.oper_name + ' ' + bot.config.oper_password
        ))

    #Use Authserv if authserv_password and authserv_account is set in config.
    if (bot.config.core.authserv_password is not None
            and bot.config.core.authserv_account is not None):
        bot.write((
            'AUTHSERV auth',
            bot.config.core.authserv_account + ' ' + bot.config.authserv_password
        ))

    #Set bot modes per config, +B if no config option is defined
    if bot.config.has_option('core', 'modes'):
        modes = bot.config.core.modes
    else:
        modes = 'B'
    bot.write(('MODE ', '%s +%s' % (bot.nick, modes)))

    bot.memory['retry_join'] = dict()

    if bot.config.has_option('core', 'throttle_join'):
        throttle_rate = int(bot.config.core.throttle_join)
        channels_joined = 0
        for channel in bot.config.core.get_list('channels'):
            channels_joined += 1
            if not channels_joined % throttle_rate:
                time.sleep(1)
            bot.join(channel)
    else:
        for channel in bot.config.core.get_list('channels'):
            bot.join(channel)


@willie.module.event('477')
@willie.module.rule('.*')
@willie.module.priority('high')
def retry_join(bot, trigger):
    """Give NickServer enough time to identify on a +R channel.

    Give NickServ enough time to identify, and retry rejoining an
    identified-only (+R) channel. Maximum of ten rejoin attempts.

    """
    channel = trigger.args[1]
    if channel in bot.memory['retry_join'].keys():
        bot.memory['retry_join'][channel] += 1
        if bot.memory['retry_join'][channel] > 10:
            LOGGER.warning('Failed to join %s after 10 attempts.', channel)
            return
    else:
        bot.memory['retry_join'][channel] = 0
        bot.join(channel)
        return

    time.sleep(6)
    bot.join(channel)

#Functions to maintain a list of chanops in all of willie's channels.


@willie.module.rule('(.*)')
@willie.module.event('353')
@willie.module.priority('high')
@willie.module.thread(False)
@willie.module.unblockable
def handle_names(bot, trigger):
    """Handle NAMES response, happens when joining to channels."""
    names = trigger.split()

    #TODO specific to one channel type. See issue 281.
    channels = re.search('(#\S*)', trigger.raw)
    if not channels:
        return
    channel = Identifier(channels.group(1))
    if channel not in bot.privileges:
        bot.privileges[channel] = dict()
    bot.init_ops_list(channel)

    # This could probably be made flexible in the future, but I don't think
    # it'd be worth it.
    mapping = {'+': willie.module.VOICE,
               '%': willie.module.HALFOP,
               '@': willie.module.OP,
               '&': willie.module.ADMIN,
               '~': willie.module.OWNER}

    for name in names:
        priv = 0
        for prefix, value in iteritems(mapping):
            if prefix in name:
                priv = priv | value
        nick = Identifier(name.lstrip(''.join(mapping.keys())))
        bot.privileges[channel][nick] = priv

        # Old op list maintenance is down here, and should be removed at some
        # point
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
@willie.module.priority('high')
@willie.module.thread(False)
@willie.module.unblockable
def track_modes(bot, trigger):
    """Track usermode changes and keep our lists of ops up to date."""
    # Mode message format: <channel> *( ( "-" / "+" ) *<modes> *<modeparams> )
    channel = Identifier(trigger.args[0])
    line = trigger.args[1:]

    # If the first character of where the mode is being set isn't a #
    # then it's a user mode, not a channel mode, so we'll ignore it.
    if channel.is_nick():
        return

    def handle_old_modes(nick, mode):
        #Old mode maintenance. Drop this crap in 5.0.
        if mode[1] == 'o' or mode[1] == 'q' or mode[1] == 'a':
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

    mapping = {'v': willie.module.VOICE,
               'h': willie.module.HALFOP,
               'o': willie.module.OP,
               'a': willie.module.ADMIN,
               'q': willie.module.OWNER}

    modes = []
    for arg in line:
        if len(arg) == 0:
            continue
        if arg[0] in '+-':
            # There was a comment claiming IRC allows e.g. MODE +aB-c foo, but
            # I don't see it in any RFCs. Leaving in the extra parsing for now.
            sign = ''
            modes = []
            for char in arg:
                if char == '+' or char == '-':
                    sign = char
                else:
                    modes.append(sign + char)
        else:
            arg = Identifier(arg)
            for mode in modes:
                priv = bot.privileges[channel].get(arg, 0)
                value = mapping.get(mode[1])
                if value is not None:
                    if mode[0] == '+':
                        priv = priv | value
                    else:
                        priv = priv & ~value
                    bot.privileges[channel][arg] = priv
                handle_old_modes(arg, mode)


@willie.module.rule('.*')
@willie.module.event('NICK')
@willie.module.priority('high')
@willie.module.thread(False)
@willie.module.unblockable
def track_nicks(bot, trigger):
    """Track nickname changes and maintain our chanops list accordingly."""
    old = trigger.nick
    new = Identifier(trigger)

    # Give debug mssage, and PM the owner, if the bot's own nick changes.
    if old == bot.nick:
        privmsg = "Hi, I'm your bot, %s." + \
            " Something has made my nick change." + \
            " This can cause some problems for me," + \
            " and make me do weird things." + \
            " You'll probably want to restart me," + \
            " and figure out what made that happen" + \
            " so you can stop it happening again." + \
            " (Usually, it means you tried to give me a nick" + \
            " that's protected by NickServ.)" % bot.nick
        debug_msg = "Nick changed by server." + \
            " This can cause unexpected behavior. Please restart the bot."
        LOGGER.critical(debug_msg)
        bot.msg(bot.config.core.owner, privmsg)
        return

    for channel in bot.privileges:
        channel = Identifier(channel)
        if old in bot.privileges[channel]:
            value = bot.privileges[channel].pop(old)
            bot.privileges[channel][new] = value

    # Old privilege maintenance
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
@willie.module.priority('high')
@willie.module.thread(False)
@willie.module.unblockable
def track_part(bot, trigger):
    if trigger.nick == bot.nick:
        bot.channels.remove(trigger.sender)
        del bot.privileges[trigger.sender]
    else:
        try:
            del bot.privileges[trigger.sender][trigger.nick]
        except KeyError:
            pass


@willie.module.rule('.*')
@willie.module.event('KICK')
@willie.module.priority('high')
@willie.module.thread(False)
@willie.module.unblockable
def track_kick(bot, trigger):
    nick = Identifier(trigger.args[1])
    if nick == bot.nick:
        bot.channels.remove(trigger.sender)
        del bot.privileges[trigger.sender]
    else:
        # Temporary fix to stop KeyErrors from being sent to channel
        # The privileges dict may not have all nicks stored at all times
        # causing KeyErrors
        try:
            del bot.privileges[trigger.sender][nick]
        except KeyError:
            pass


@willie.module.rule('.*')
@willie.module.event('JOIN')
@willie.module.priority('high')
@willie.module.thread(False)
@willie.module.unblockable
def track_join(bot, trigger):
    if trigger.nick == bot.nick and trigger.sender not in bot.channels:
        bot.channels.append(trigger.sender)
        bot.privileges[trigger.sender] = dict()
    bot.privileges[trigger.sender][trigger.nick] = 0


@willie.module.rule('.*')
@willie.module.event('QUIT')
@willie.module.priority('high')
@willie.module.thread(False)
@willie.module.unblockable
def track_quit(bot, trigger):
    for chanprivs in bot.privileges.values():
        if trigger.nick in chanprivs:
            del chanprivs[trigger.nick]


@willie.module.rule('.*')
@willie.module.event('CAP')
@willie.module.thread(False)
@willie.module.priority('high')
@willie.module.unblockable
def recieve_cap_list(bot, trigger):
    # Server is listing capabilites
    if trigger.args[1] == 'LS':
        recieve_cap_ls_reply(bot, trigger)
    # Server denied CAP REQ
    elif trigger.args[1] == 'NAK':
        entry = bot._cap_reqs.get(trigger, None)
        # If it was requested with bot.cap_req
        if entry:
            for req in entry:
                # And that request was mandatory/prohibit, and a callback was
                # provided
                if req[0] and req[2]:
                    # Call it.
                    req[2](bot, req[0] + trigger)
    # Server is acknowledinge SASL for us.
    elif (trigger.args[0] == bot.nick and trigger.args[1] == 'ACK' and
          'sasl' in trigger.args[2]):
        recieve_cap_ack_sasl(bot)


def recieve_cap_ls_reply(bot, trigger):
    if bot.server_capabilities:
        # We've already seen the results, so someone sent CAP LS from a module.
        # We're too late to do SASL, and we don't want to send CAP END before
        # the module has done what it needs to, so just return
        return
    bot.server_capabilities = set(trigger.split(' '))

    # If some other module requests it, we don't need to add another request.
    # If some other module prohibits it, we shouldn't request it.
    if 'multi-prefix' not in bot._cap_reqs:
        # Whether or not the server supports multi-prefix doesn't change how we
        # parse it, so we don't need to worry if it fails.
        bot._cap_reqs['multi-prefix'] = (['', 'coretasks', None],)

    for cap, reqs in iteritems(bot._cap_reqs):
        # At this point, we know mandatory and prohibited don't co-exist, but
        # we need to call back for optionals if they're also prohibited
        prefix = ''
        for entry in reqs:
            if prefix == '-' and entry[0] != '-':
                entry[2](bot, entry[0] + cap)
                continue
            if entry[0]:
                prefix = entry[0]

        # It's not required, or it's supported, so we can request it
        if prefix != '=' or cap in bot.server_capabilities:
            # REQs fail as a whole, so we send them one capability at a time
            bot.write(('CAP', 'REQ', entry[0] + cap))
        elif req[2]:
            # Server is going to fail on it, so we call the failure function
            req[2](bot, entry[0] + cap)

    # If we want to do SASL, we have to wait before we can send CAP END. So if
    # we are, wait on 903 (SASL successful) to send it.
    if bot.config.core.sasl_password:
        bot.write(('CAP', 'REQ', 'sasl'))
    else:
        bot.write(('CAP', 'END'))


def recieve_cap_ack_sasl(bot):
    # Presumably we're only here if we said we actually *want* sasl, but still
    # check anyway.
    if not bot.config.core.sasl_password:
        return
    mech = bot.config.core.sasl_mechanism or 'PLAIN'
    bot.write(('AUTHENTICATE', mech))


@willie.module.event('AUTHENTICATE')
@willie.module.rule('.*')
def auth_proceed(bot, trigger):
    if trigger.args[0] != '+':
        # How did we get here? I am not good with computer.
        return
    # Is this right?
    if bot.config.core.sasl_username:
        sasl_username = bot.config.core.sasl_username
    else:
        sasl_username = bot.nick
    sasl_token = '\0'.join((sasl_username, sasl_username,
                           bot.config.core.sasl_password))
    # Spec says we do a base 64 encode on the SASL stuff
    bot.write(('AUTHENTICATE', base64.b64encode(sasl_token)))


@willie.module.event('903')
@willie.module.rule('.*')
def sasl_success(bot, trigger):
    bot.write(('CAP', 'END'))


#Live blocklist editing


@willie.module.commands('blocks')
@willie.module.priority('low')
@willie.module.thread(False)
@willie.module.unblockable
def blocks(bot, trigger):
    """Manage Willie's blocking features.

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
    nicks = [Identifier(nick) for nick in bot.config.core.get_list('nick_blocks')]
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
            if Identifier(text[3]) not in nicks:
                bot.reply(STRINGS['no_nick'] % (text[3]))
                return
            nicks.remove(Identifier(text[3]))
            bot.config.core.nick_blocks = nicks
            bot.config.save()
            bot.reply(STRINGS['success_del'] % (text[3]))
        elif text[2] == "hostmask":
            mask = text[3].lower()
            if mask not in masks:
                bot.reply(STRINGS['no_host'] % (text[3]))
                return
            masks.remove(mask)
            bot.config.core.host_blocks = masks
            bot.config.save()
            bot.reply(STRINGS['success_del'] % (text[3]))
        else:
            bot.reply(STRINGS['invalid'] % ("deleting"))
            return
    else:
        bot.reply(STRINGS['huh'])
