# coding=utf-8
"""Tasks that allow the bot to run, but aren't user-facing functionality

This is written as a module to make it easier to extend to support more
responses to standard IRC codes without having to shove them all into the
dispatch function in bot.py and making it easier to maintain.
"""
# Copyright 2008-2011, Sean B. Palmer (inamidst.com) and Michael Yanovich
# (yanovich.net)
# Copyright © 2012, Elad Alfassa <elad@fedoraproject.org>
# Copyright 2012-2015, Elsie Powell embolalia.com
# Licensed under the Eiffel Forum License 2.
from __future__ import unicode_literals, absolute_import, print_function, division

from random import randint
import re
import sys
import time
import sopel
import sopel.module
from sopel.bot import _CapReq
from sopel.tools import Identifier, iteritems, events
from sopel.tools.target import User, Channel
import base64
from sopel.logger import get_logger

if sys.version_info.major >= 3:
    unicode = str

LOGGER = get_logger(__name__)

batched_caps = {}
who_reqs = {}  # Keeps track of reqs coming from this module, rather than others


def auth_after_register(bot):
    """Do NickServ/AuthServ auth"""
    if bot.config.core.auth_method == 'nickserv':
        nickserv_name = bot.config.core.auth_target or 'NickServ'
        bot.msg(
            nickserv_name,
            'IDENTIFY %s' % bot.config.core.auth_password
        )

    elif bot.config.core.auth_method == 'authserv':
        account = bot.config.core.auth_username
        password = bot.config.core.auth_password
        bot.write((
            'AUTHSERV auth',
            account + ' ' + password
        ))

    elif bot.config.core.auth_method == 'Q':
        account = bot.config.core.auth_username
        password = bot.config.core.auth_password
        bot.write((
            'AUTH',
            account + ' ' + password
        ))

    elif bot.config.core.auth_method == 'userserv':
        userserv_name = bot.config.core.auth_target or 'UserServ'
        account = bot.config.core.auth_username
        password = bot.config.core.auth_password
        bot.msg(userserv_name, "LOGIN {account} {password}".format(
                account=account, password=password))


@sopel.module.event(events.RPL_WELCOME, events.RPL_LUSERCLIENT)
@sopel.module.rule('.*')
@sopel.module.thread(False)
@sopel.module.unblockable
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

    auth_after_register(bot)

    modes = bot.config.core.modes
    bot.write(('MODE ', '%s +%s' % (bot.nick, modes)))

    bot.memory['retry_join'] = dict()

    if bot.config.core.throttle_join:
        throttle_rate = int(bot.config.core.throttle_join)
        channels_joined = 0
        for channel in bot.config.core.channels:
            channels_joined += 1
            if not channels_joined % throttle_rate:
                time.sleep(1)
            bot.join(channel)
    else:
        for channel in bot.config.core.channels:
            bot.join(channel)

    if (not bot.config.core.owner_account and
            'account-tag' in bot.enabled_capabilities and
            '@' not in bot.config.core.owner):
        msg = (
            "This network supports using network services to identify you as "
            "my owner, rather than just matching your nickname. This is much "
            "more secure. If you'd like to do this, make sure you're logged in "
            "and reply with \"{}useserviceauth\""
        ).format(bot.config.core.help_prefix)
        bot.msg(bot.config.core.owner, msg)


@sopel.module.require_privmsg()
@sopel.module.require_owner()
@sopel.module.commands('useserviceauth')
def enable_service_auth(bot, trigger):
    if bot.config.core.owner_account:
        return
    if 'account-tag' not in bot.enabled_capabilities:
        bot.say('This server does not fully support services auth, so this '
                'command is not available.')
        return
    if not trigger.account:
        bot.say('You must be logged in to network services before using this '
                'command.')
        return
    bot.config.core.owner_account = trigger.account
    bot.config.save()
    bot.say('Success! I will now use network services to identify you as my '
            'owner.')


@sopel.module.event(events.ERR_NOCHANMODES)
@sopel.module.rule('.*')
@sopel.module.priority('high')
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


@sopel.module.rule('(.*)')
@sopel.module.event(events.RPL_NAMREPLY)
@sopel.module.priority('high')
@sopel.module.thread(False)
@sopel.module.unblockable
def handle_names(bot, trigger):
    """Handle NAMES response, happens when joining to channels."""
    names = trigger.split()

    # TODO specific to one channel type. See issue 281.
    channels = re.search(r'(#\S*)', trigger.raw)
    if not channels:
        return
    channel = Identifier(channels.group(1))
    if channel not in bot.privileges:
        bot.privileges[channel] = dict()
    if channel not in bot.channels:
        bot.channels[channel] = Channel(channel)

    # This could probably be made flexible in the future, but I don't think
    # it'd be worth it.
    # If this ever needs to be updated, remember to change the mode handling in
    # the WHO-handler functions below, too.
    mapping = {'+': sopel.module.VOICE,
               '%': sopel.module.HALFOP,
               '@': sopel.module.OP,
               '&': sopel.module.ADMIN,
               '~': sopel.module.OWNER}

    for name in names:
        priv = 0
        for prefix, value in iteritems(mapping):
            if prefix in name:
                priv = priv | value
        nick = Identifier(name.lstrip(''.join(mapping.keys())))
        bot.privileges[channel][nick] = priv
        user = bot.users.get(nick)
        if user is None:
            # It's not possible to set the username/hostname from info received
            # in a NAMES reply, unfortunately.
            # Fortunately, the user should already exist in bot.users by the
            # time this code runs, so this is 99.9% ass-covering.
            user = User(nick, None, None)
            bot.users[nick] = user
        bot.channels[channel].add_user(user, privs=priv)


@sopel.module.rule('(.*)')
@sopel.module.event('MODE')
@sopel.module.priority('high')
@sopel.module.thread(False)
@sopel.module.unblockable
def track_modes(bot, trigger):
    """Track usermode changes and keep our lists of ops up to date."""
    # Mode message format: <channel> *( ( "-" / "+" ) *<modes> *<modeparams> )
    channel = Identifier(trigger.args[0])
    line = trigger.args[1:]

    # If the first character of where the mode is being set isn't a #
    # then it's a user mode, not a channel mode, so we'll ignore it.
    if channel.is_nick():
        return

    mapping = {'v': sopel.module.VOICE,
               'h': sopel.module.HALFOP,
               'o': sopel.module.OP,
               'a': sopel.module.ADMIN,
               'q': sopel.module.OWNER}

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
                priv = bot.channels[channel].privileges.get(arg, 0)
                # Log a warning if the two privilege-tracking data structures
                # get out of sync. That should never happen.
                # This is a good place to verify that bot.channels is doing
                # what it's supposed to do before ultimately removing the old,
                # deprecated bot.privileges structure completely.
                ppriv = bot.privileges[channel].get(arg, 0)
                if priv != ppriv:
                    LOGGER.warning("Privilege data error! Please share Sopel's"
                                   "raw log with the developers, if enabled. "
                                   "(Expected {} == {} for {} in {}.)"
                                   .format(priv, ppriv, arg, channel))
                value = mapping.get(mode[1])
                if value is not None:
                    if mode[0] == '+':
                        priv = priv | value
                    else:
                        priv = priv & ~value
                    bot.privileges[channel][arg] = priv
                    bot.channels[channel].privileges[arg] = priv


@sopel.module.rule('.*')
@sopel.module.event('NICK')
@sopel.module.priority('high')
@sopel.module.thread(False)
@sopel.module.unblockable
def track_nicks(bot, trigger):
    """Track nickname changes and maintain our chanops list accordingly."""
    old = trigger.nick
    new = Identifier(trigger)

    # Give debug mssage, and PM the owner, if the bot's own nick changes.
    if old == bot.nick and new != bot.nick:
        privmsg = ("Hi, I'm your bot, %s."
                   "Something has made my nick change. "
                   "This can cause some problems for me, "
                   "and make me do weird things. "
                   "You'll probably want to restart me, "
                   "and figure out what made that happen "
                   "so you can stop it happening again. "
                   "(Usually, it means you tried to give me a nick "
                   "that's protected by NickServ.)") % bot.nick
        debug_msg = ("Nick changed by server. "
            "This can cause unexpected behavior. Please restart the bot.")
        LOGGER.critical(debug_msg)
        bot.msg(bot.config.core.owner, privmsg)
        return

    for channel in bot.privileges:
        channel = Identifier(channel)
        if old in bot.privileges[channel]:
            value = bot.privileges[channel].pop(old)
            bot.privileges[channel][new] = value

    for channel in bot.channels.values():
        channel.rename_user(old, new)
    if old in bot.users:
        bot.users[new] = bot.users.pop(old)


@sopel.module.rule('(.*)')
@sopel.module.event('PART')
@sopel.module.priority('high')
@sopel.module.thread(False)
@sopel.module.unblockable
def track_part(bot, trigger):
    nick = trigger.nick
    channel = trigger.sender
    _remove_from_channel(bot, nick, channel)


@sopel.module.rule('.*')
@sopel.module.event('KICK')
@sopel.module.priority('high')
@sopel.module.thread(False)
@sopel.module.unblockable
def track_kick(bot, trigger):
    nick = Identifier(trigger.args[1])
    channel = trigger.sender
    _remove_from_channel(bot, nick, channel)


def _remove_from_channel(bot, nick, channel):
    if nick == bot.nick:
        bot.privileges.pop(channel, None)
        bot.channels.pop(channel, None)

        lost_users = []
        for nick_, user in bot.users.items():
            user.channels.pop(channel, None)
            if not user.channels:
                lost_users.append(nick_)
        for nick_ in lost_users:
            bot.users.pop(nick_, None)
    else:
        bot.privileges[channel].pop(nick, None)

        user = bot.users.get(nick)
        if user and channel in user.channels:
            bot.channels[channel].clear_user(nick)
            if not user.channels:
                bot.users.pop(nick, None)


def _whox_enabled(bot):
    # Either privilege tracking or away notification. For simplicity, both
    # account notify and extended join must be there for account tracking.
    return (('account-notify' in bot.enabled_capabilities and
             'extended-join' in bot.enabled_capabilities) or
            'away-notify' in bot.enabled_capabilities)


def _send_who(bot, channel):
    if _whox_enabled(bot):
        # WHOX syntax, see http://faerion.sourceforge.net/doc/irc/whox.var
        # Needed for accounts in who replies. The random integer is a param
        # to identify the reply as one from this command, because if someone
        # else sent it, we have no fucking way to know what the format is.
        rand = str(randint(0, 999))
        while rand in who_reqs:
            rand = str(randint(0, 999))
        who_reqs[rand] = channel
        bot.write(['WHO', channel, 'a%nuachtf,' + rand])
    else:
        # We might be on an old network, but we still care about keeping our
        # user list updated
        bot.write(['WHO', channel])


@sopel.module.rule('.*')
@sopel.module.event('JOIN')
@sopel.module.priority('high')
@sopel.module.thread(False)
@sopel.module.unblockable
def track_join(bot, trigger):
    if trigger.nick == bot.nick and trigger.sender not in bot.channels:
        bot.write(('TOPIC', trigger.sender))

        bot.privileges[trigger.sender] = dict()
        bot.channels[trigger.sender] = Channel(trigger.sender)
        _send_who(bot, trigger.sender)

    bot.privileges[trigger.sender][trigger.nick] = 0

    user = bot.users.get(trigger.nick)
    if user is None:
        user = User(trigger.nick, trigger.user, trigger.host)
        bot.users[trigger.nick] = user
    bot.channels[trigger.sender].add_user(user)

    if len(trigger.args) > 1 and trigger.args[1] != '*' and (
            'account-notify' in bot.enabled_capabilities and
            'extended-join' in bot.enabled_capabilities):
        user.account = trigger.args[1]


@sopel.module.rule('.*')
@sopel.module.event('QUIT')
@sopel.module.priority('high')
@sopel.module.thread(False)
@sopel.module.unblockable
def track_quit(bot, trigger):
    for chanprivs in bot.privileges.values():
        chanprivs.pop(trigger.nick, None)
    for channel in bot.channels.values():
        channel.clear_user(trigger.nick)
    bot.users.pop(trigger.nick, None)


@sopel.module.rule('.*')
@sopel.module.event('CAP')
@sopel.module.thread(False)
@sopel.module.priority('high')
@sopel.module.unblockable
def recieve_cap_list(bot, trigger):
    cap = trigger.strip('-=~')
    # Server is listing capabilites
    if trigger.args[1] == 'LS':
        recieve_cap_ls_reply(bot, trigger)
    # Server denied CAP REQ
    elif trigger.args[1] == 'NAK':
        entry = bot._cap_reqs.get(cap, None)
        # If it was requested with bot.cap_req
        if entry:
            for req in entry:
                # And that request was mandatory/prohibit, and a callback was
                # provided
                if req.prefix and req.failure:
                    # Call it.
                    req.failure(bot, req.prefix + cap)
    # Server is removing a capability
    elif trigger.args[1] == 'DEL':
        entry = bot._cap_reqs.get(cap, None)
        # If it was requested with bot.cap_req
        if entry:
            for req in entry:
                # And that request wasn't prohibit, and a callback was
                # provided
                if req.prefix != '-' and req.failure:
                    # Call it.
                    req.failure(bot, req.prefix + cap)
    # Server is adding new capability
    elif trigger.args[1] == 'NEW':
        entry = bot._cap_reqs.get(cap, None)
        # If it was requested with bot.cap_req
        if entry:
            for req in entry:
                # And that request wasn't prohibit
                if req.prefix != '-':
                    # Request it
                    bot.write(('CAP', 'REQ', req.prefix + cap))
    # Server is acknowledging a capability
    elif trigger.args[1] == 'ACK':
        caps = trigger.args[2].split()
        for cap in caps:
            cap.strip('-~= ')
            bot.enabled_capabilities.add(cap)
            entry = bot._cap_reqs.get(cap, [])
            for req in entry:
                if req.success:
                    req.success(bot, req.prefix + trigger)
            if cap == 'sasl':  # TODO why is this not done with bot.cap_req?
                recieve_cap_ack_sasl(bot)


def recieve_cap_ls_reply(bot, trigger):
    if bot.server_capabilities:
        # We've already seen the results, so someone sent CAP LS from a module.
        # We're too late to do SASL, and we don't want to send CAP END before
        # the module has done what it needs to, so just return
        return

    for cap in trigger.split():
        c = cap.split('=')
        if len(c) == 2:
            batched_caps[c[0]] = c[1]
        else:
            batched_caps[c[0]] = None

    # Not the last in a multi-line reply. First two args are * and LS.
    if trigger.args[2] == '*':
        return

    bot.server_capabilities = batched_caps

    # If some other module requests it, we don't need to add another request.
    # If some other module prohibits it, we shouldn't request it.
    core_caps = ['multi-prefix', 'away-notify', 'cap-notify', 'server-time']
    for cap in core_caps:
        if cap not in bot._cap_reqs:
            bot._cap_reqs[cap] = [_CapReq('', 'coretasks')]

    def acct_warn(bot, cap):
        LOGGER.info('Server does not support %s, or it conflicts with a custom '
                    'module. User account validation unavailable or limited.',
                    cap[1:])
        if bot.config.core.owner_account or bot.config.core.admin_accounts:
            LOGGER.warning(
                'Owner or admin accounts are configured, but %s is not '
                'supported by the server. This may cause unexpected behavior.',
                cap[1:])
    auth_caps = ['account-notify', 'extended-join', 'account-tag']
    for cap in auth_caps:
        if cap not in bot._cap_reqs:
            bot._cap_reqs[cap] = [_CapReq('', 'coretasks', acct_warn)]

    for cap, reqs in iteritems(bot._cap_reqs):
        # At this point, we know mandatory and prohibited don't co-exist, but
        # we need to call back for optionals if they're also prohibited
        prefix = ''
        for entry in reqs:
            if prefix == '-' and entry.prefix != '-':
                entry.failure(bot, entry.prefix + cap)
                continue
            if entry.prefix:
                prefix = entry.prefix

        # It's not required, or it's supported, so we can request it
        if prefix != '=' or cap in bot.server_capabilities:
            # REQs fail as a whole, so we send them one capability at a time
            bot.write(('CAP', 'REQ', entry.prefix + cap))
        # If it's required but not in server caps, we need to call all the
        # callbacks
        else:
            for entry in reqs:
                if entry.failure and entry.prefix == '=':
                    entry.failure(bot, entry.prefix + cap)

    # If we want to do SASL, we have to wait before we can send CAP END. So if
    # we are, wait on 903 (SASL successful) to send it.
    if bot.config.core.auth_method == 'sasl':
        bot.write(('CAP', 'REQ', 'sasl'))
    else:
        bot.write(('CAP', 'END'))


def recieve_cap_ack_sasl(bot):
    # Presumably we're only here if we said we actually *want* sasl, but still
    # check anyway.
    password = bot.config.core.auth_password
    if not password:
        return
    mech = bot.config.core.auth_target or 'PLAIN'
    bot.write(('AUTHENTICATE', mech))


def send_authenticate(bot, token):
    """Send ``AUTHENTICATE`` command to server with the given ``token``.

    :param bot: instance of IRC bot that must authenticate
    :param str token: authentication token

    In case the ``token`` is more than 400 bytes, we need to split it and send
    as many ``AUTHENTICATE`` commands as needed. If the last chunk is 400 bytes
    long, we must also send a last empty command (`AUTHENTICATE +` is for empty
    line), so the server knows we are done with ``AUTHENTICATE``.

    .. seealso::

        https://ircv3.net/specs/extensions/sasl-3.1.html#the-authenticate-command

    """
    # payload is a base64 encoded token
    payload = base64.b64encode(token.encode('utf-8'))

    # split the payload into chunks of at most 400 bytes
    chunk_size = 400
    for i in range(0, len(payload), chunk_size):
        offset = i + chunk_size
        chunk = payload[i:offset]
        bot.write(('AUTHENTICATE', chunk))

    # send empty (+) AUTHENTICATE when payload's length is a multiple of 400
    if len(payload) % chunk_size == 0:
        bot.write(('AUTHENTICATE', '+'))


@sopel.module.event('AUTHENTICATE')
@sopel.module.rule('.*')
def auth_proceed(bot, trigger):
    if trigger.args[0] != '+':
        # How did we get here? I am not good with computer.
        return
    # Is this right?
    sasl_username = bot.config.core.auth_username or bot.nick
    sasl_password = bot.config.core.auth_password
    sasl_token = '\0'.join((sasl_username, sasl_username, sasl_password))
    send_authenticate(bot, sasl_token)


@sopel.module.event(events.RPL_SASLSUCCESS)
@sopel.module.rule('.*')
def sasl_success(bot, trigger):
    bot.write(('CAP', 'END'))


# Live blocklist editing


@sopel.module.commands('blocks')
@sopel.module.priority('low')
@sopel.module.thread(False)
@sopel.module.unblockable
def blocks(bot, trigger):
    """
    Manage Sopel's blocking features.\
    See [ignore system documentation]({% link _usage/ignoring-people.md %}).

    """
    if not trigger.admin:
        return

    STRINGS = {
        "success_del": "Successfully deleted block: %s",
        "success_add": "Successfully added block: %s",
        "no_nick": "No matching nick block found for: %s",
        "no_host": "No matching hostmask block found for: %s",
        "invalid": "Invalid format for %s a block. Try: .blocks add (nick|hostmask) sopel",
        "invalid_display": "Invalid input for displaying blocks.",
        "nonelisted": "No %s listed in the blocklist.",
        'huh': "I could not figure out what you wanted to do.",
    }

    masks = set(s for s in bot.config.core.host_blocks if s != '')
    nicks = set(Identifier(nick)
                for nick in bot.config.core.nick_blocks
                if nick != '')
    text = trigger.group().split()

    if len(text) == 3 and text[1] == "list":
        if text[2] == "hostmask":
            if len(masks) > 0:
                blocked = ', '.join(unicode(mask) for mask in masks)
                bot.say("Blocked hostmasks: {}".format(blocked))
            else:
                bot.reply(STRINGS['nonelisted'] % ('hostmasks'))
        elif text[2] == "nick":
            if len(nicks) > 0:
                blocked = ', '.join(unicode(nick) for nick in nicks)
                bot.say("Blocked nicks: {}".format(blocked))
            else:
                bot.reply(STRINGS['nonelisted'] % ('nicks'))
        else:
            bot.reply(STRINGS['invalid_display'])

    elif len(text) == 4 and text[1] == "add":
        if text[2] == "nick":
            nicks.add(text[3])
            bot.config.core.nick_blocks = nicks
            bot.config.save()
        elif text[2] == "hostmask":
            masks.add(text[3].lower())
            bot.config.core.host_blocks = list(masks)
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
            bot.config.core.nick_blocks = [unicode(n) for n in nicks]
            bot.config.save()
            bot.reply(STRINGS['success_del'] % (text[3]))
        elif text[2] == "hostmask":
            mask = text[3].lower()
            if mask not in masks:
                bot.reply(STRINGS['no_host'] % (text[3]))
                return
            masks.remove(mask)
            bot.config.core.host_blocks = [unicode(m) for m in masks]
            bot.config.save()
            bot.reply(STRINGS['success_del'] % (text[3]))
        else:
            bot.reply(STRINGS['invalid'] % ("deleting"))
            return
    else:
        bot.reply(STRINGS['huh'])


@sopel.module.event('ACCOUNT')
@sopel.module.rule('.*')
def account_notify(bot, trigger):
    if trigger.nick not in bot.users:
        bot.users[trigger.nick] = User(trigger.nick, trigger.user, trigger.host)
    account = trigger.args[0]
    if account == '*':
        account = None
    bot.users[trigger.nick].account = account


@sopel.module.event(events.RPL_WHOSPCRPL)
@sopel.module.rule('.*')
@sopel.module.priority('high')
@sopel.module.unblockable
def recv_whox(bot, trigger):
    if len(trigger.args) < 2 or trigger.args[1] not in who_reqs:
        # Ignored, some module probably called WHO
        return
    if len(trigger.args) != 8:
        return LOGGER.warning('While populating `bot.accounts` a WHO response was malformed.')
    _, _, channel, user, host, nick, status, account = trigger.args
    away = 'G' in status
    modes = ''.join([c for c in status if c in '~&@%+'])
    _record_who(bot, channel, user, host, nick, account, away, modes)


def _record_who(bot, channel, user, host, nick, account=None, away=None, modes=None):
    nick = Identifier(nick)
    channel = Identifier(channel)
    if nick not in bot.users:
        bot.users[nick] = User(nick, user, host)
    user = bot.users[nick]
    if account == '0':
        user.account = None
    else:
        user.account = account
    user.away = away
    priv = 0
    if modes:
        mapping = {'+': sopel.module.VOICE,
           '%': sopel.module.HALFOP,
           '@': sopel.module.OP,
           '&': sopel.module.ADMIN,
           '~': sopel.module.OWNER}
        for c in modes:
            priv = priv | mapping[c]
    if channel not in bot.channels:
        bot.channels[channel] = Channel(channel)
    bot.channels[channel].add_user(user, privs=priv)
    if channel not in bot.privileges:
        bot.privileges[channel] = dict()
    bot.privileges[channel][nick] = priv


@sopel.module.event(events.RPL_WHOREPLY)
@sopel.module.rule('.*')
@sopel.module.priority('high')
@sopel.module.unblockable
def recv_who(bot, trigger):
    channel, user, host, _, nick, status = trigger.args[1:7]
    modes = ''.join([c for c in status if c in '~&@%+'])
    _record_who(bot, channel, user, host, nick, modes=modes)


@sopel.module.event(events.RPL_ENDOFWHO)
@sopel.module.rule('.*')
@sopel.module.priority('high')
@sopel.module.unblockable
def end_who(bot, trigger):
    if _whox_enabled(bot):
        who_reqs.pop(trigger.args[1], None)


@sopel.module.rule('.*')
@sopel.module.event('AWAY')
@sopel.module.priority('high')
@sopel.module.thread(False)
@sopel.module.unblockable
def track_notify(bot, trigger):
    if trigger.nick not in bot.users:
        bot.users[trigger.nick] = User(trigger.nick, trigger.user, trigger.host)
    user = bot.users[trigger.nick]
    user.away = bool(trigger.args)


@sopel.module.rule('.*')
@sopel.module.event('TOPIC')
@sopel.module.event(events.RPL_TOPIC)
@sopel.module.priority('high')
@sopel.module.thread(False)
@sopel.module.unblockable
def track_topic(bot, trigger):
    if trigger.event != 'TOPIC':
        channel = trigger.args[1]
    else:
        channel = trigger.args[0]
    if channel not in bot.channels:
        return
    bot.channels[channel].topic = trigger.args[-1]
