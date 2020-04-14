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
# Copyright 2019, Florian Strzelecki <florian.strzelecki@gmail.com>
#
# Licensed under the Eiffel Forum License 2.
from __future__ import unicode_literals, absolute_import, print_function, division

import base64
import collections
import datetime
import functools
import logging
import re
import sys
import time
from random import randint

from sopel import loader, module
from sopel.irc import isupport
from sopel.irc.utils import CapReq, MyInfo
from sopel.tools import Identifier, events, iteritems, jobs, target, web


if sys.version_info.major >= 3:
    unicode = str

LOGGER = logging.getLogger(__name__)

batched_caps = {}
who_reqs = {}  # Keeps track of reqs coming from this module, rather than others


def setup(bot):
    bot.memory['join_events_queue'] = collections.deque()

    # Manage JOIN flood protection
    if bot.settings.core.throttle_join:
        wait_interval = max(bot.settings.core.throttle_wait, 1)

        @module.interval(wait_interval)
        def processing_job(bot):
            _join_event_processing(bot)

        loader.clean_callable(processing_job, bot.settings)
        bot.scheduler.add_job(jobs.Job(wait_interval, processing_job))


def shutdown(bot):
    try:
        bot.memory['join_events_queue'].clear()
    except KeyError:
        pass


def _join_event_processing(bot):
    """Process a batch of JOIN event from the ``join_events_queue`` queue.

    Every time this function is executed, it processes at most
    ``throttle_join`` JOIN events. For each JOIN, it sends a WHO request to
    know more about the channel. This will prevent an excess of flood when
    there are too many channels to join at once.
    """
    batch_size = max(bot.settings.core.throttle_join, 1)
    for _ in range(batch_size):
        try:
            channel = bot.memory['join_events_queue'].popleft()
        except IndexError:
            break
        LOGGER.debug('Sending WHO after channel JOIN: %s', channel)
        _send_who(bot, channel)


def auth_after_register(bot):
    """Do NickServ/AuthServ auth"""
    if bot.config.core.auth_method:
        auth_method = bot.config.core.auth_method
        auth_username = bot.config.core.auth_username
        auth_password = bot.config.core.auth_password
        auth_target = bot.config.core.auth_target
    elif bot.config.core.nick_auth_method:
        auth_method = bot.config.core.nick_auth_method
        auth_username = (bot.config.core.nick_auth_username or
                         bot.config.core.nick)
        auth_password = bot.config.core.nick_auth_password
        auth_target = bot.config.core.nick_auth_target
    else:
        return

    if auth_method == 'nickserv':
        bot.say('IDENTIFY %s' % auth_password, auth_target or 'NickServ')
    elif auth_method == 'authserv':
        bot.write(('AUTHSERV auth', auth_username + ' ' + auth_password))
    elif auth_method == 'Q':
        bot.write(('AUTH', auth_username + ' ' + auth_password))
    elif auth_method == 'userserv':
        bot.say("LOGIN %s %s" % (auth_username, auth_password),
                auth_target or 'UserServ')


def _execute_perform(bot):
    """Execute commands specified to perform on IRC server connect."""
    if not bot.connection_registered:
        # How did you even get this command, bot?
        raise Exception('Bot must be connected to server to perform commands.')

    LOGGER.debug('{} commands to execute:'.format(len(bot.config.core.commands_on_connect)))
    for i, command in enumerate(bot.config.core.commands_on_connect):
        command = command.replace('$nickname', bot.config.core.nick)
        LOGGER.debug(command)
        bot.write((command,))


@module.require_privmsg("This command only works as a private message.")
@module.require_admin("This command requires admin privileges.")
@module.commands('execute')
def execute_perform(bot, trigger):
    """Execute commands specified to perform on IRC server connect."""
    _execute_perform(bot)


@module.priority('high')
@module.event(events.RPL_WELCOME, events.RPL_LUSERCLIENT)
@module.thread(False)
@module.unblockable
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
    bot.write(('MODE', '%s +%s' % (bot.nick, modes)))

    bot.memory['retry_join'] = dict()

    channels = bot.config.core.channels
    if not channels:
        LOGGER.info('No initial channels to JOIN.')
    elif bot.config.core.throttle_join:
        throttle_rate = int(bot.config.core.throttle_join)
        throttle_wait = max(bot.config.core.throttle_wait, 1)
        channels_joined = 0

        LOGGER.info(
            'Joining %d channels (with JOIN throttle ON); '
            'this may take a moment.',
            len(channels))

        for channel in channels:
            channels_joined += 1
            if not channels_joined % throttle_rate:
                LOGGER.debug(
                    'Waiting %ds before next JOIN batch.',
                    throttle_wait)
                time.sleep(throttle_wait)
            bot.join(channel)
    else:
        LOGGER.info(
            'Joining %d channels (with JOIN throttle OFF); '
            'this may take a moment.',
            len(channels))

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
        bot.say(msg, bot.config.core.owner)

    _execute_perform(bot)


@module.priority('high')
@module.event(events.RPL_ISUPPORT)
@module.thread(False)
@module.unblockable
@module.rule('are supported by this server')
def handle_isupport(bot, trigger):
    """Handle ``RPL_ISUPPORT`` events."""
    parameters = {}
    for arg in trigger.args:
        try:
            key, value = isupport.parse_parameter(arg)
            parameters[key] = value
        except ValueError:
            # ignore malformed parameter: log a warning and continue
            LOGGER.warning('Unable to parse ISUPPORT parameter: %r', arg)

    bot._isupport = bot._isupport.apply(**parameters)


@module.priority('high')
@module.event(events.RPL_MYINFO)
@module.thread(False)
@module.unblockable
def parse_reply_myinfo(bot, trigger):
    """Handle ``RPL_MYINFO`` events."""
    # keep <client> <servername> <version> only
    # the trailing parameters (mode types) should be read from ISUPPORT
    bot._myinfo = MyInfo(*trigger.args[0:3])


@module.require_privmsg()
@module.require_owner()
@module.commands('useserviceauth')
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


@module.event(events.ERR_NOCHANMODES)
@module.priority('high')
def retry_join(bot, trigger):
    """Give NickServ enough time to identify on a +R channel.

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


@module.rule('(.*)')
@module.event(events.RPL_NAMREPLY)
@module.priority('high')
@module.thread(False)
@module.unblockable
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
        bot.channels[channel] = target.Channel(channel)

    # This could probably be made flexible in the future, but I don't think
    # it'd be worth it.
    # If this ever needs to be updated, remember to change the mode handling in
    # the WHO-handler functions below, too.
    mapping = {
        "+": module.VOICE,
        "%": module.HALFOP,
        "@": module.OP,
        "&": module.ADMIN,
        "~": module.OWNER,
        "!": module.OPER,
    }

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
            user = target.User(nick, None, None)
            bot.users[nick] = user
        bot.channels[channel].add_user(user, privs=priv)


@module.rule('(.*)')
@module.event('MODE')
@module.priority('high')
@module.thread(False)
@module.unblockable
def track_modes(bot, trigger):
    """Track usermode changes and keep our lists of ops up to date."""
    # Mode message format: <channel> *( ( "-" / "+" ) *<modes> *<modeparams> )
    if len(trigger.args) < 3:
        # We need at least [channel, mode, nickname] to do anything useful
        # MODE messages with fewer args won't help us
        LOGGER.debug("Received an apparently useless MODE message: {}"
                     .format(trigger.raw))
        return
    # Our old MODE parsing code checked if any of the args was empty.
    # Somewhere around here would be a good place to re-implement that if it's
    # actually necessary to guard against some non-compliant IRCd. But for now
    # let's just log malformed lines to the debug log.
    if not all(trigger.args):
        LOGGER.debug("The server sent a possibly malformed MODE message: {}"
                     .format(trigger.raw))

    # From here on, we will make a (possibly dangerous) assumption that the
    # received MODE message is more-or-less compliant
    channel = Identifier(trigger.args[0])
    # If the first character of where the mode is being set isn't a #
    # then it's a user mode, not a channel mode, so we'll ignore it.
    # TODO: Handle CHANTYPES from ISUPPORT numeric (005)
    # (Actually, most of this function should be rewritten again when we parse
    # ISUPPORT...)
    if channel.is_nick():
        return

    modestring = trigger.args[1]
    nicks = [Identifier(nick) for nick in trigger.args[2:]]

    mapping = {
        "v": module.VOICE,
        "h": module.HALFOP,
        "o": module.OP,
        "a": module.ADMIN,
        "q": module.OWNER,
        "y": module.OPER,
        "Y": module.OPER,
    }

    # Parse modes before doing anything else
    modes = []
    sign = ''
    for char in modestring:
        # There was a comment claiming IRC allows e.g. MODE +aB-c foo, but it
        # doesn't seem to appear in any RFCs. But modern.ircdocs.horse shows
        # it, so we'll leave in the extra parsing for now.
        if char in '+-':
            sign = char
        elif char in mapping:
            # Filter out unexpected modes and hope they don't have parameters
            modes.append(sign + char)

    # Try to map modes to arguments, after sanity-checking
    if len(modes) != len(nicks) or not all([nick.is_nick() for nick in nicks]):
        # Something fucky happening, like unusual batching of non-privilege
        # modes together with the ones we expect. Way easier to just re-WHO
        # than try to account for non-standard parameter-taking modes.
        LOGGER.debug('Sending WHO for channel: %s', channel)
        _send_who(bot, channel)
        return

    for (mode, nick) in zip(modes, nicks):
        priv = bot.channels[channel].privileges.get(nick, 0)
        # Log a warning if the two privilege-tracking data structures
        # get out of sync. That should never happen.
        # This is a good place to verify that bot.channels is doing
        # what it's supposed to do before ultimately removing the old,
        # deprecated bot.privileges structure completely.
        ppriv = bot.privileges[channel].get(nick, 0)
        if priv != ppriv:
            LOGGER.warning("Privilege data error! Please share Sopel's"
                           "raw log with the developers, if enabled. "
                           "(Expected {} == {} for {} in {}.)"
                           .format(priv, ppriv, nick, channel))
        value = mapping.get(mode[1])
        if value is not None:
            if mode[0] == '+':
                priv = priv | value
            else:
                priv = priv & ~value
            bot.privileges[channel][nick] = priv
            bot.channels[channel].privileges[nick] = priv


@module.event('NICK')
@module.priority('high')
@module.thread(False)
@module.unblockable
def track_nicks(bot, trigger):
    """Track nickname changes and maintain our chanops list accordingly."""
    old = trigger.nick
    new = Identifier(trigger)

    # Give debug mssage, and PM the owner, if the bot's own nick changes.
    if old == bot.nick and new != bot.nick:
        privmsg = (
            "Hi, I'm your bot, %s. Something has made my nick change. This "
            "can cause some problems for me, and make me do weird things. "
            "You'll probably want to restart me, and figure out what made "
            "that happen so you can stop it happening again. (Usually, it "
            "means you tried to give me a nick that's protected by NickServ.)"
        ) % bot.nick
        debug_msg = (
            "Nick changed by server. This can cause unexpected behavior. "
            "Please restart the bot."
        )
        LOGGER.critical(debug_msg)
        bot.say(privmsg, bot.config.core.owner)
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


@module.rule('(.*)')
@module.event('PART')
@module.priority('high')
@module.thread(False)
@module.unblockable
def track_part(bot, trigger):
    nick = trigger.nick
    channel = trigger.sender
    _remove_from_channel(bot, nick, channel)


@module.event('KICK')
@module.priority('high')
@module.thread(False)
@module.unblockable
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
    bot.channels[Identifier(channel)].last_who = datetime.datetime.utcnow()


@module.interval(30)
def _periodic_send_who(bot):
    """Periodically send a WHO request to keep user information up-to-date."""
    if 'away-notify' in bot.enabled_capabilities:
        # WHO not needed to update 'away' status
        return

    # Loops through the channels to find the one that has the longest time since the last WHO
    # request, and issues a WHO request only if the last request for the channel was more than
    # 120 seconds ago.
    who_trigger_time = datetime.datetime.utcnow() - datetime.timedelta(seconds=120)
    selected_channel = None
    for channel_name, channel in bot.channels.items():
        if channel.last_who is None:
            # WHO was never sent yet to this channel: stop here
            selected_channel = channel_name
            break
        if channel.last_who < who_trigger_time:
            # this channel's last who request is the most outdated one at the moment
            selected_channel = channel_name
            who_trigger_time = channel.last_who

    if selected_channel is not None:
        # selected_channel's last who is either none or the oldest valid
        LOGGER.debug('Sending WHO for channel: %s', selected_channel)
        _send_who(bot, selected_channel)


@module.event('JOIN')
@module.priority('high')
@module.thread(False)
@module.unblockable
def track_join(bot, trigger):
    channel = trigger.sender

    # is it a new channel?
    if channel not in bot.channels:
        LOGGER.info('Channel joined: %s', channel)
        bot.privileges[channel] = dict()
        bot.channels[channel] = target.Channel(channel)

    # did *we* just join?
    if trigger.nick == bot.nick:
        if bot.settings.core.throttle_join:
            LOGGER.debug('JOIN event added to queue for channel: %s', channel)
            bot.memory['join_events_queue'].append(channel)
        else:
            LOGGER.debug('Send direct WHO for channel: %s', channel)
            _send_who(bot, channel)

    # set initial values
    bot.privileges[channel][trigger.nick] = 0

    user = bot.users.get(trigger.nick)
    if user is None:
        user = target.User(trigger.nick, trigger.user, trigger.host)
        bot.users[trigger.nick] = user
    bot.channels[channel].add_user(user)

    if len(trigger.args) > 1 and trigger.args[1] != '*' and (
            'account-notify' in bot.enabled_capabilities and
            'extended-join' in bot.enabled_capabilities):
        user.account = trigger.args[1]


@module.event('QUIT')
@module.priority('high')
@module.thread(False)
@module.unblockable
def track_quit(bot, trigger):
    for chanprivs in bot.privileges.values():
        chanprivs.pop(trigger.nick, None)
    for channel in bot.channels.values():
        channel.clear_user(trigger.nick)
    bot.users.pop(trigger.nick, None)


@module.event('CAP')
@module.thread(False)
@module.priority('high')
@module.unblockable
def receive_cap_list(bot, trigger):
    cap = trigger.strip('-=~')
    # Server is listing capabilities
    if trigger.args[1] == 'LS':
        receive_cap_ls_reply(bot, trigger)
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
                receive_cap_ack_sasl(bot)


def receive_cap_ls_reply(bot, trigger):
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
    core_caps = [
        'echo-message',
        'multi-prefix',
        'away-notify',
        'cap-notify',
        'server-time',
    ]
    for cap in core_caps:
        if cap not in bot._cap_reqs:
            bot._cap_reqs[cap] = [CapReq('', 'coretasks')]

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
            bot._cap_reqs[cap] = [CapReq('', 'coretasks', acct_warn)]

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
    if bot.config.core.auth_method == 'sasl' or bot.config.core.server_auth_method == 'sasl':
        bot.write(('CAP', 'REQ', 'sasl'))
    else:
        bot.write(('CAP', 'END'))


def receive_cap_ack_sasl(bot):
    # Presumably we're only here if we said we actually *want* sasl, but still
    # check anyway.
    password = None
    mech = None
    if bot.config.core.auth_method == 'sasl':
        password = bot.config.core.auth_password
        mech = bot.config.core.auth_target
    elif bot.config.core.server_auth_method == 'sasl':
        password = bot.config.core.server_auth_password
        mech = bot.config.core.server_auth_sasl_mech
    if not password:
        return
    mech = mech or 'PLAIN'
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


@module.event('AUTHENTICATE')
def auth_proceed(bot, trigger):
    if trigger.args[0] != '+':
        # How did we get here? I am not good with computer.
        return
    # Is this right?
    if bot.config.core.auth_method == 'sasl':
        sasl_username = bot.config.core.auth_username
        sasl_password = bot.config.core.auth_password
    elif bot.config.core.server_auth_method == 'sasl':
        sasl_username = bot.config.core.server_auth_username
        sasl_password = bot.config.core.server_auth_password
    else:
        return
    sasl_username = sasl_username or bot.nick
    sasl_token = '\0'.join((sasl_username, sasl_username, sasl_password))
    send_authenticate(bot, sasl_token)


@module.event(events.RPL_SASLSUCCESS)
def sasl_success(bot, trigger):
    bot.write(('CAP', 'END'))


# Live blocklist editing


@module.commands('blocks')
@module.priority('low')
@module.thread(False)
@module.unblockable
@module.require_admin
def blocks(bot, trigger):
    """
    Manage Sopel's blocking features.\
    See [ignore system documentation]({% link _usage/ignoring-people.md %}).

    """
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


@module.event('ACCOUNT')
def account_notify(bot, trigger):
    if trigger.nick not in bot.users:
        bot.users[trigger.nick] = target.User(
            trigger.nick, trigger.user, trigger.host)
    account = trigger.args[0]
    if account == '*':
        account = None
    bot.users[trigger.nick].account = account


@module.event(events.RPL_WHOSPCRPL)
@module.priority('high')
@module.unblockable
def recv_whox(bot, trigger):
    if len(trigger.args) < 2 or trigger.args[1] not in who_reqs:
        # Ignored, some module probably called WHO
        return
    if len(trigger.args) != 8:
        return LOGGER.warning('While populating `bot.accounts` a WHO response was malformed.')
    _, _, channel, user, host, nick, status, account = trigger.args
    away = 'G' in status
    modes = ''.join([c for c in status if c in '~&@%+!'])
    _record_who(bot, channel, user, host, nick, account, away, modes)


def _record_who(bot, channel, user, host, nick, account=None, away=None, modes=None):
    nick = Identifier(nick)
    channel = Identifier(channel)
    if nick not in bot.users:
        usr = target.User(nick, user, host)
        bot.users[nick] = usr
    else:
        usr = bot.users[nick]
        # check for & fill in sparse User added by handle_names()
        if usr.host is None and host:
            usr.host = host
        if usr.user is None and user:
            usr.user = user
    if account == '0':
        usr.account = None
    else:
        usr.account = account
    if away is not None:
        usr.away = away
    priv = 0
    if modes:
        mapping = {
            "+": module.VOICE,
            "%": module.HALFOP,
            "@": module.OP,
            "&": module.ADMIN,
            "~": module.OWNER,
            "!": module.OPER,
        }
        for c in modes:
            priv = priv | mapping[c]
    if channel not in bot.channels:
        bot.channels[channel] = target.Channel(channel)
    bot.channels[channel].add_user(usr, privs=priv)
    if channel not in bot.privileges:
        bot.privileges[channel] = dict()
    bot.privileges[channel][nick] = priv


@module.event(events.RPL_WHOREPLY)
@module.priority('high')
@module.unblockable
def recv_who(bot, trigger):
    channel, user, host, _, nick, status = trigger.args[1:7]
    away = 'G' in status
    modes = ''.join([c for c in status if c in '~&@%+!'])
    _record_who(bot, channel, user, host, nick, away=away, modes=modes)


@module.event(events.RPL_ENDOFWHO)
@module.priority('high')
@module.unblockable
def end_who(bot, trigger):
    if _whox_enabled(bot):
        who_reqs.pop(trigger.args[1], None)


@module.event('AWAY')
@module.priority('high')
@module.thread(False)
@module.unblockable
def track_notify(bot, trigger):
    if trigger.nick not in bot.users:
        bot.users[trigger.nick] = target.User(
            trigger.nick, trigger.user, trigger.host)
    user = bot.users[trigger.nick]
    user.away = bool(trigger.args)


@module.event('TOPIC')
@module.event(events.RPL_TOPIC)
@module.priority('high')
@module.thread(False)
@module.unblockable
def track_topic(bot, trigger):
    if trigger.event != 'TOPIC':
        channel = trigger.args[1]
    else:
        channel = trigger.args[0]
    if channel not in bot.channels:
        return
    bot.channels[channel].topic = trigger.args[-1]


@module.rule(r'(?u).*(.+://\S+).*')
def handle_url_callbacks(bot, trigger):
    """Dispatch callbacks on URLs

    For each URL found in the trigger, trigger the URL callback registered by
    the ``@url`` decorator.
    """
    schemes = bot.config.core.auto_url_schemes
    # find URLs in the trigger
    for url in web.search_urls(trigger, schemes=schemes):
        # find callbacks for said URL
        for function, match in bot.search_url_callbacks(url):
            # trigger callback defined by the `@url` decorator
            if hasattr(function, 'url_regex'):
                # bake the `match` argument in before passing the callback on
                @functools.wraps(function)
                def decorated(bot, trigger):
                    return function(bot, trigger, match=match)

                bot.call(decorated, bot, trigger)
