# coding=utf-8
"""Core Sopel plugin that handles IRC protocol functions.

This plugin allows the bot to run without user-facing functionality:

* it handles client capability negotiation
* it handles client auth (both nick auth and server auth)
* it handles connection registration (RPL_WELCOME, RPL_LUSERCLIENT), dealing
  with error cases such as nick already in use
* it tracks known channels & users (join, quit, nick change and other events)
* it manages blocked (ignored) users

This is written as a plugin to make it easier to extend to support more
responses to standard IRC codes without having to shove them all into the
dispatch function in :class:`sopel.bot.Sopel` and making it easier to maintain.
"""
# Copyright 2008-2011, Sean B. Palmer (inamidst.com) and Michael Yanovich
# (yanovich.net)
# Copyright © 2012, Elad Alfassa <elad@fedoraproject.org>
# Copyright 2012-2015, Elsie Powell embolalia.com
# Copyright 2019, Florian Strzelecki <florian.strzelecki@gmail.com>
#
# Licensed under the Eiffel Forum License 2.
from __future__ import absolute_import, division, print_function, unicode_literals

import base64
import collections
import datetime
import functools
import logging
import re
import sys
import time

from sopel import loader, module, plugin
from sopel.config import ConfigurationError
from sopel.irc import isupport
from sopel.irc.utils import CapReq, MyInfo
from sopel.tools import events, Identifier, iteritems, SopelMemory, target, web


if sys.version_info.major >= 3:
    unicode = str

LOGGER = logging.getLogger(__name__)

CORE_QUERYTYPE = '999'
"""WHOX querytype to indicate requests/responses from coretasks.

Other plugins should use a different querytype.
"""

batched_caps = {}


def setup(bot):
    """Set up the coretasks plugin.

    The setup phase is used to activate the throttle feature to prevent a flood
    of JOIN commands when there are too many channels to join.
    """
    bot.memory['join_events_queue'] = collections.deque()

    # Manage JOIN flood protection
    if bot.settings.core.throttle_join:
        wait_interval = max(bot.settings.core.throttle_wait, 1)

        @module.interval(wait_interval)
        @plugin.label('throttle_join')
        def processing_job(bot):
            _join_event_processing(bot)

        loader.clean_callable(processing_job, bot.settings)
        processing_job.plugin_name = 'coretasks'

        bot.register_jobs([processing_job])


def shutdown(bot):
    """Clean up coretasks-related values in the bot's memory."""
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
        LOGGER.debug("Sending MODE and WHO after channel JOIN: %s", channel)
        bot.write(["MODE", channel])
        _send_who(bot, channel)


def auth_after_register(bot):
    """Do NickServ/AuthServ auth.

    :param bot: a connected Sopel instance
    :type bot: :class:`sopel.bot.Sopel`

    This function can be used, **after** the bot is connected, to handle one of
    these auth methods:

    * ``nickserv``: send a private message to the NickServ service
    * ``authserv``: send an ``AUTHSERV`` command
    * ``Q``: send an ``AUTH`` command
    * ``userserv``: send a private message to the UserServ service

    .. important::

        If ``core.auth_method`` is set, then ``core.nick_auth_method`` will be
        ignored. If none is set, then this function does nothing.

    """
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

    # nickserv-based auth method needs to check for current nick
    if auth_method == 'nickserv':
        if bot.nick != bot.settings.core.nick:
            LOGGER.warning("Sending nickserv GHOST command.")
            bot.say(
                'GHOST %s %s' % (bot.settings.core.nick, auth_password),
                auth_target or 'NickServ')
        else:
            bot.say('IDENTIFY %s' % auth_password, auth_target or 'NickServ')

    # other methods use account instead of nick
    elif auth_method == 'authserv':
        bot.write(('AUTHSERV', 'auth', auth_username, auth_password))
    elif auth_method == 'Q':
        bot.write(('AUTH', auth_username, auth_password))
    elif auth_method == 'userserv':
        bot.say("LOGIN %s %s" % (auth_username, auth_password),
                auth_target or 'UserServ')


def _execute_perform(bot):
    """Execute commands specified to perform on IRC server connect.

    This function executes the list of commands that can be found in the
    ``core.commands_on_connect`` setting. It automatically replaces any
    ``$nickname`` placeholder in the command with the bot's configured nick.
    """
    if not bot.connection_registered:
        # How did you even get this command, bot?
        raise Exception('Bot must be connected to server to perform commands.')

    commands = bot.config.core.commands_on_connect
    count = len(commands)

    if not count:
        LOGGER.info("No custom command to execute.")
        return

    LOGGER.info("Executing %d custom commands.", count)
    for i, command in enumerate(commands, 1):
        command = command.replace('$nickname', bot.config.core.nick)
        LOGGER.debug("Executing custom command [%d/%d]: %s", i, count, command)
        bot.write((command,))


@plugin.event(events.ERR_NICKNAMEINUSE)
@plugin.thread(False)
@plugin.unblockable
@plugin.priority('medium')
def on_nickname_in_use(bot, trigger):
    """Change the bot's nick when the current one is already in use.

    This can be triggered when the bot disconnects then reconnects before the
    server can notice a client timeout. Other reasons include mischief,
    trolling, and obviously, PEBKAC.

    This will change the current nick by adding a trailing ``_``. If the bot
    sees that a user with its configured nick disconnects (see ``QUIT`` event
    handling), the bot will try to regain it.
    """
    LOGGER.error(
        "Nickname already in use! (Nick: %s; Sender: %s; Args: %r)",
        trigger.nick,
        trigger.sender,
        trigger.args,
    )
    bot.change_current_nick(bot.nick + '_')


@module.require_privmsg("This command only works as a private message.")
@module.require_admin("This command requires admin privileges.")
@module.commands('execute')
def execute_perform(bot, trigger):
    """Execute commands specified to perform on IRC server connect.

    This allows a bot owner or admin to force the execution of commands
    that are automatically performed when the bot connects.
    """
    _execute_perform(bot)


@module.event(events.RPL_WELCOME, events.RPL_LUSERCLIENT)
@module.thread(False)
@module.unblockable
@plugin.priority('medium')
def startup(bot, trigger):
    """Do tasks related to connecting to the network.

    ``001 RPL_WELCOME`` is from RFC2812 and is the first message that is sent
    after the connection has been registered on the network.

    ``251 RPL_LUSERCLIENT`` is a mandatory message that is sent after the
    client connects to the server in RFC1459. RFC2812 does not require it and
    all networks might not send it. We support both.

    If ``sopel.irc.AbstractBot.connection_registered`` is set, this function
    does nothing and returns immediately. Otherwise, the flag is set and the
    function proceeds normally to:

    1. trigger auth method
    2. set bot's ``MODE`` (from ``core.modes``)
    3. join channels (or queue them to join later)
    4. check for security when the ``account-tag`` capability is enabled
    5. execute custom commands
    """
    if bot.connection_registered:
        return

    # set flag
    bot.connection_registered = True

    # handle auth method
    auth_after_register(bot)

    # set bot's MODE
    modes = bot.config.core.modes
    if modes:
        if not modes.startswith(('+', '-')):
            # Assume "+" by default.
            modes = '+' + modes
        bot.write(('MODE', bot.nick, modes))

    # join channels
    bot.memory['retry_join'] = SopelMemory()

    channels = bot.config.core.channels
    if not channels:
        LOGGER.info("No initial channels to JOIN.")
    elif bot.config.core.throttle_join:
        throttle_rate = int(bot.config.core.throttle_join)
        throttle_wait = max(bot.config.core.throttle_wait, 1)
        channels_joined = 0

        LOGGER.info(
            "Joining %d channels (with JOIN throttle ON); "
            "this may take a moment.",
            len(channels))

        for channel in channels:
            channels_joined += 1
            if not channels_joined % throttle_rate:
                LOGGER.debug(
                    "Waiting %ds before next JOIN batch.",
                    throttle_wait)
                time.sleep(throttle_wait)
            bot.join(channel)
    else:
        LOGGER.info(
            "Joining %d channels (with JOIN throttle OFF); "
            "this may take a moment.",
            len(channels))

        for channel in bot.config.core.channels:
            bot.join(channel)

    # warn for insecure auth method if necessary
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

    # execute custom commands
    _execute_perform(bot)


@module.event(events.RPL_ISUPPORT)
@module.thread(False)
@module.unblockable
@module.rule('are supported by this server')
@plugin.priority('medium')
def handle_isupport(bot, trigger):
    """Handle ``RPL_ISUPPORT`` events."""
    # remember if NAMESX is known to be supported, before parsing RPL_ISUPPORT
    namesx_support = 'NAMESX' in bot.isupport

    # parse ISUPPORT message from server
    parameters = {}
    for arg in trigger.args:
        try:
            key, value = isupport.parse_parameter(arg)
            parameters[key] = value
        except ValueError:
            # ignore malformed parameter: log a warning and continue
            LOGGER.warning("Unable to parse ISUPPORT parameter: %r", arg)

    bot._isupport = bot._isupport.apply(**parameters)

    # was NAMESX support status updated?
    if not namesx_support and 'NAMESX' in bot.isupport:
        # yes it was!
        if 'multi-prefix' not in bot.server_capabilities:
            # and the server doesn't have the multi-prefix capability
            # so we can ask the server to use the NAMESX feature
            bot.write(('PROTOCTL', 'NAMESX'))


@module.event(events.RPL_MYINFO)
@module.thread(False)
@module.unblockable
@plugin.priority('medium')
def parse_reply_myinfo(bot, trigger):
    """Handle ``RPL_MYINFO`` events."""
    # keep <client> <servername> <version> only
    # the trailing parameters (mode types) should be read from ISUPPORT
    bot._myinfo = MyInfo(*trigger.args[0:3])

    LOGGER.info(
        "Received RPL_MYINFO from server: %s, %s, %s",
        bot._myinfo.client,
        bot._myinfo.servername,
        bot._myinfo.version,
    )


@module.require_privmsg()
@module.require_owner()
@module.commands('useserviceauth')
def enable_service_auth(bot, trigger):
    """Set owner's account from an authenticated owner.

    This command can be used to automatically configure ``core.owner_account``
    when the owner is known and has a registered account, but the bot doesn't
    have ``core.owner_account`` configured.

    This doesn't work if the ``account-tag`` capability is not available.
    """
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
    LOGGER.info(
        "User %s set %s as owner account.",
        trigger.nick,
        trigger.account,
    )


@module.event(events.ERR_NOCHANMODES)
@plugin.priority('medium')
def retry_join(bot, trigger):
    """Give NickServ enough time to identify on a +R channel.

    Give NickServ enough time to identify, and retry rejoining an
    identified-only (+R) channel. Maximum of ten rejoin attempts.
    """
    channel = trigger.args[1]
    if channel in bot.memory['retry_join'].keys():
        bot.memory['retry_join'][channel] += 1
        if bot.memory['retry_join'][channel] > 10:
            LOGGER.warning("Failed to join %s after 10 attempts.", channel)
            return
        LOGGER.info(
            "Rejoining channel %r failed, will retry in 6s.",
            str(channel))
        time.sleep(6)
    else:
        bot.memory['retry_join'][channel] = 0

    attempt = bot.memory['retry_join'][channel] + 1
    LOGGER.info(
        "Trying to rejoin channel %r (attempt %d/10)",
        str(channel), attempt)
    bot.join(channel)


@module.rule('(.*)')
@module.event(events.RPL_NAMREPLY)
@module.thread(False)
@module.unblockable
@plugin.priority('medium')
def handle_names(bot, trigger):
    """Handle NAMES responses.

    This function keeps track of users' privileges when Sopel joins channels.
    """
    names = trigger.split()

    # TODO specific to one channel type. See issue 281.
    channels = re.search(r'(#\S*)', trigger.raw)
    if not channels:
        return
    channel = Identifier(channels.group(1))
    if channel not in bot.privileges:
        bot.privileges[channel] = {}
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
@module.thread(False)
@module.unblockable
@plugin.priority('medium')
def track_modes(bot, trigger):
    """Track changes from received MODE commands."""
    _parse_modes(bot, trigger.args)


@module.priority('high')
@module.event(events.RPL_CHANNELMODEIS)
@module.thread(False)
@module.unblockable
def initial_modes(bot, trigger):
    """Populate channel modes from response to MODE request sent after JOIN."""
    _parse_modes(bot, trigger.args[1:], clear=True)


def _parse_modes(bot, args, clear=False):
    """Parse MODE message and apply changes to internal state."""
    channel_name = Identifier(args[0])
    if channel_name.is_nick():
        # We don't do anything with user modes
        LOGGER.debug("Ignoring user modes: %r", args)
        return

    channel = bot.channels[channel_name]

    # Unreal 3 sometimes sends an extraneous trailing space. If we're short an
    # arg, we'll find out later.
    if args[-1] == "":
        args.pop()
    # If any args are still empty, that's something we may not be prepared for,
    # but let's continue anyway hoping they're trailing / not important.
    if len(args) < 2 or not all(args):
        LOGGER.debug(
            "The server sent a possibly malformed MODE message: %r", args)

    modestring = args[1]
    params = args[2:]

    mapping = {
        "v": module.VOICE,
        "h": module.HALFOP,
        "o": module.OP,
        "a": module.ADMIN,
        "q": module.OWNER,
        "y": module.OPER,
        "Y": module.OPER,
    }

    modes = {}
    if not clear:
        # Work on a copy for some thread safety
        modes.update(channel.modes)

    # Process modes
    sign = ""
    param_idx = 0
    chanmodes = bot.isupport.CHANMODES
    for char in modestring:
        # Are we setting or unsetting
        if char in "+-":
            sign = char
            continue

        if char in chanmodes["A"]:
            # Type A (beI, etc) have a nick or address param to add/remove
            if char not in modes:
                modes[char] = set()
            if sign == "+":
                modes[char].add(params[param_idx])
            elif params[param_idx] in modes[char]:
                modes[char].remove(params[param_idx])
            param_idx += 1
        elif char in chanmodes["B"]:
            # Type B (k, etc) always have a param
            if sign == "+":
                modes[char] = params[param_idx]
            elif char in modes:
                modes.pop(char)
            param_idx += 1
        elif char in chanmodes["C"]:
            # Type C (l, etc) have a param only when setting
            if sign == "+":
                modes[char] = params[param_idx]
                param_idx += 1
            elif char in modes:
                modes.pop(char)
        elif char in chanmodes["D"]:
            # Type D (aciLmMnOpqrRst, etc) have no params
            if sign == "+":
                modes[char] = True
            elif char in modes:
                modes.pop(char)
        elif char in mapping and (
            "PREFIX" not in bot.isupport or char in bot.isupport.PREFIX
        ):
            # User privs modes, always have a param
            nick = Identifier(params[param_idx])
            priv = channel.privileges.get(nick, 0)
            # Log a warning if the two privilege-tracking data structures
            # get out of sync. That should never happen.
            # This is a good place to verify that bot.channels is doing
            # what it's supposed to do before ultimately removing the old,
            # deprecated bot.privileges structure completely.
            ppriv = bot.privileges[channel_name].get(nick, 0)
            if priv != ppriv:
                LOGGER.warning(
                    (
                        "Privilege data error! Please share Sopel's "
                        "raw log with the developers, if enabled. "
                        "(Expected %s == %s for %r in %r)"
                    ),
                    priv,
                    ppriv,
                    nick,
                    channel,
                )
            value = mapping.get(char)
            if value is not None:
                if sign == "+":
                    priv = priv | value
                else:
                    priv = priv & ~value
                bot.privileges[channel_name][nick] = priv
                channel.privileges[nick] = priv
            param_idx += 1
        else:
            # Might be in a mode block past A/B/C/D, but we don't speak those.
            # Send a WHO to ensure no user priv modes we're skipping are lost.
            LOGGER.warning(
                "Unknown MODE message, sending WHO. Message was: %r",
                args,
            )
            _send_who(bot, channel_name)
            return

    if param_idx != len(params):
        LOGGER.warning(
            "Too many arguments received for MODE: args=%r chanmodes=%r",
            args,
            chanmodes,
        )

    channel.modes = modes

    LOGGER.info("Updated mode for channel: %s", channel.name)
    LOGGER.debug("Channel %r mode: %r", str(channel.name), channel.modes)


@module.event('NICK')
@module.thread(False)
@module.unblockable
@plugin.priority('medium')
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

    LOGGER.info("User named %r is now known as %r.", old, str(new))


@module.rule('(.*)')
@module.event('PART')
@module.thread(False)
@module.unblockable
@plugin.priority('medium')
def track_part(bot, trigger):
    """Track users leaving channels."""
    nick = trigger.nick
    channel = trigger.sender
    _remove_from_channel(bot, nick, channel)
    LOGGER.info("User %r left a channel: %s", str(nick), channel)


@module.event('KICK')
@module.thread(False)
@module.unblockable
@plugin.priority('medium')
def track_kick(bot, trigger):
    """Track users kicked from channels."""
    nick = Identifier(trigger.args[1])
    channel = trigger.sender
    _remove_from_channel(bot, nick, channel)
    LOGGER.info(
        "User %r got kicked by %r from a channel: %s",
        str(nick),
        str(trigger.nick),
        channel,
    )


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


def _send_who(bot, channel):
    if 'WHOX' in bot.isupport:
        # WHOX syntax, see http://faerion.sourceforge.net/doc/irc/whox.var
        # Needed for accounts in WHO replies. The `CORE_QUERYTYPE` parameter
        # for WHO is used to identify the reply from the server and confirm
        # that it has the requested format. WHO replies with different
        # querytypes in the response were initiated elsewhere and will be
        # ignored.
        bot.write(['WHO', channel, 'a%nuachtf,' + CORE_QUERYTYPE])
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
        LOGGER.debug("Sending WHO for channel: %s", selected_channel)
        _send_who(bot, selected_channel)


@module.event('JOIN')
@module.thread(False)
@module.unblockable
@plugin.priority('medium')
def track_join(bot, trigger):
    """Track users joining channels.

    When a user joins a channel, the bot will send (or queue) a ``WHO`` command
    to know more about said user (privileges, modes, etc.).
    """
    channel = trigger.sender

    # is it a new channel?
    if channel not in bot.channels:
        bot.privileges[channel] = {}
        bot.channels[channel] = target.Channel(channel)

    # did *we* just join?
    if trigger.nick == bot.nick:
        LOGGER.info("Channel joined: %s", channel)
        if bot.settings.core.throttle_join:
            LOGGER.debug("JOIN event added to queue for channel: %s", channel)
            bot.memory['join_events_queue'].append(channel)
        else:
            LOGGER.debug("Send MODE and direct WHO for channel: %s", channel)
            bot.write(["MODE", channel])
            _send_who(bot, channel)
    else:
        LOGGER.info(
            "Channel %r joined by user: %s",
            str(channel), trigger.nick)

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
@module.thread(False)
@module.unblockable
@plugin.priority('medium')
def track_quit(bot, trigger):
    """Track when users quit channels."""
    for chanprivs in bot.privileges.values():
        chanprivs.pop(trigger.nick, None)
    for channel in bot.channels.values():
        channel.clear_user(trigger.nick)
    bot.users.pop(trigger.nick, None)

    LOGGER.info("User quit: %s", trigger.nick)

    if trigger.nick == bot.settings.core.nick and trigger.nick != bot.nick:
        # old nick is now available, let's change nick again
        bot.change_current_nick(bot.settings.core.nick)
        auth_after_register(bot)


@module.event('CAP')
@module.thread(False)
@module.unblockable
@plugin.priority('medium')
def receive_cap_list(bot, trigger):
    """Handle client capability negotiation."""
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
                try:
                    receive_cap_ack_sasl(bot)
                except ConfigurationError as error:
                    LOGGER.error(str(error))
                    bot.quit('Wrong SASL configuration.')


def receive_cap_ls_reply(bot, trigger):
    if bot.server_capabilities:
        # We've already seen the results, so someone sent CAP LS from a plugin.
        # We're too late to do SASL, and we don't want to send CAP END before
        # the plugin has done what it needs to, so just return
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

    LOGGER.info(
        "Client capability negotiation list: %s",
        ', '.join(batched_caps.keys()),
    )
    bot.server_capabilities = batched_caps

    # If some other plugin requests it, we don't need to add another request.
    # If some other plugin prohibits it, we shouldn't request it.
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
        LOGGER.info("Server does not support %s, or it conflicts with a custom "
                    "plugin. User account validation unavailable or limited.",
                    cap[1:])
        if bot.config.core.owner_account or bot.config.core.admin_accounts:
            LOGGER.warning(
                "Owner or admin accounts are configured, but %s is not "
                "supported by the server. This may cause unexpected behavior.",
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
        LOGGER.info("End of client capability negotiation requests.")


def receive_cap_ack_sasl(bot):
    # Presumably we're only here if we said we actually *want* sasl, but still
    # check anyway in case the server glitched.
    password, mech = _get_sasl_pass_and_mech(bot)
    if not password:
        return

    mech = mech or 'PLAIN'
    available_mechs = bot.server_capabilities.get('sasl', '')
    available_mechs = available_mechs.split(',') if available_mechs else []

    if available_mechs and mech not in available_mechs:
        """
        Raise an error if configured to use an unsupported SASL mechanism,
        but only if the server actually advertised supported mechanisms,
        i.e. this network supports SASL 3.2

        SASL 3.1 failure is handled (when possible) by the sasl_mechs() function

        See https://github.com/sopel-irc/sopel/issues/1780 for background
        """
        raise ConfigurationError(
            "SASL mechanism '{}' is not advertised by this server.".format(mech))

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
@plugin.thread(False)
@module.unblockable
@plugin.priority('medium')
def auth_proceed(bot, trigger):
    """Handle client-initiated SASL auth.

    If the chosen mechanism is client-first, the server sends an empty
    response (``AUTHENTICATE +``). In that case, Sopel will handle SASL auth
    that uses a token.

    .. important::

        If ``core.auth_method`` is set, then ``core.server_auth_method`` will
        be ignored. If none is set, then this function does nothing.

    """
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
    sasl_token = _make_sasl_plain_token(sasl_username, sasl_password)
    LOGGER.info("Sending SASL Auth token.")
    send_authenticate(bot, sasl_token)


def _make_sasl_plain_token(account, password):
    return '\x00'.join((account, account, password))


@module.event(events.RPL_SASLSUCCESS)
@plugin.thread(False)
@module.unblockable
@plugin.priority('medium')
def sasl_success(bot, trigger):
    """End CAP request on successful SASL auth.

    If SASL is configured, then the bot won't send ``CAP END`` once it gets
    all the capability responses; it will wait for SASL auth result.

    In this case, the SASL auth is a success, so we can close the negotiation.
    """
    LOGGER.info("Successful SASL Auth.")
    bot.write(('CAP', 'END'))
    LOGGER.info("End of client capability negotiation requests.")


@plugin.event(events.ERR_SASLFAIL)
@plugin.event(events.ERR_SASLTOOLONG)
@plugin.event(events.ERR_SASLABORTED)
@plugin.event(events.ERR_NICKLOCKED)
@plugin.thread(False)
@plugin.unblockable
@plugin.priority('medium')
def sasl_fail(bot, trigger):
    """SASL Auth Failed: log the error and quit."""
    LOGGER.error(
        "SASL Auth Failed; check your configuration: %s",
        str(trigger))
    bot.quit('SASL Auth Failed')


@module.event(events.RPL_SASLMECHS)
@plugin.thread(False)
@module.unblockable
@plugin.priority('low')
def sasl_mechs(bot, trigger):
    # Presumably we're only here if we said we actually *want* sasl, but still
    # check anyway in case the server glitched.
    password, mech = _get_sasl_pass_and_mech(bot)
    if not password:
        return

    supported_mechs = trigger.args[1].split(',')
    if mech not in supported_mechs:
        """
        How we get here:

        1. Sopel connects to a network advertising SASL 3.1
        2. SASL 3.1 doesn't advertise supported mechanisms up front, so Sopel
           blindly goes ahead with whatever SASL config it's set to use
        3. The server doesn't support the mechanism Sopel used, and is a good
           IRC citizen, so it sends this optional numeric, 908 RPL_SASLMECHS

        Note that misconfigured SASL 3.1 will just silently fail when connected
        to an IRC server NOT implementing the optional 908 reply.

        A network with SASL 3.2 should theoretically never get this far because
        Sopel should catch the unadvertised mechanism in receive_cap_ack_sasl().

        See https://github.com/sopel-irc/sopel/issues/1780 for background
        """
        LOGGER.error(
            "Configured SASL mechanism '%s' is not advertised by this server. "
            "Advertised values: %s",
            mech,
            ', '.join(supported_mechs),
        )
        bot.quit('Wrong SASL configuration.')
    else:
        LOGGER.info(
            "Selected SASL mechanism is %s, advertised: %s",
            mech,
            ', '.join(supported_mechs),
        )


def _get_sasl_pass_and_mech(bot):
    password = None
    mech = None
    if bot.config.core.auth_method == 'sasl':
        password = bot.config.core.auth_password
        mech = bot.config.core.auth_target
    elif bot.config.core.server_auth_method == 'sasl':
        password = bot.config.core.server_auth_password
        mech = bot.config.core.server_auth_sasl_mech
    return password, mech


# Live blocklist editing


@module.commands('blocks')
@module.thread(False)
@module.unblockable
@module.priority('low')
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
@plugin.thread(False)
@plugin.unblockable
@plugin.priority('medium')
def account_notify(bot, trigger):
    """Track users' accounts."""
    if trigger.nick not in bot.users:
        bot.users[trigger.nick] = target.User(
            trigger.nick, trigger.user, trigger.host)
    account = trigger.args[0]
    if account == '*':
        account = None
    bot.users[trigger.nick].account = account
    LOGGER.info("Update account for nick %r: %s", trigger.nick, account)


@module.event(events.RPL_WHOSPCRPL)
@plugin.thread(False)
@module.unblockable
@plugin.priority('medium')
def recv_whox(bot, trigger):
    """Track ``WHO`` responses when ``WHOX`` is enabled."""
    if len(trigger.args) < 2 or trigger.args[1] != CORE_QUERYTYPE:
        # Ignored, some plugin probably called WHO
        LOGGER.debug("Ignoring WHO reply for channel '%s'; not queried by coretasks", trigger.args[1])
        return
    if len(trigger.args) != 8:
        LOGGER.warning(
            "While populating `bot.accounts` a WHO response was malformed.")
        return
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
        bot.privileges[channel] = {}
    bot.privileges[channel][nick] = priv


@module.event(events.RPL_WHOREPLY)
@plugin.thread(False)
@module.unblockable
@plugin.priority('medium')
def recv_who(bot, trigger):
    """Track ``WHO`` responses when ``WHOX`` is not enabled."""
    channel, user, host, _, nick, status = trigger.args[1:7]
    away = 'G' in status
    modes = ''.join([c for c in status if c in '~&@%+!'])
    _record_who(bot, channel, user, host, nick, away=away, modes=modes)


@module.event('AWAY')
@module.thread(False)
@module.unblockable
@plugin.priority('medium')
def track_notify(bot, trigger):
    """Track users going away or coming back."""
    if trigger.nick not in bot.users:
        bot.users[trigger.nick] = target.User(
            trigger.nick, trigger.user, trigger.host)
    user = bot.users[trigger.nick]
    user.away = bool(trigger.args)
    state_change = 'went away' if user.away else 'came back'
    LOGGER.info("User %s: %s", state_change, trigger.nick)


@module.event('TOPIC')
@module.event(events.RPL_TOPIC)
@module.thread(False)
@module.unblockable
@plugin.priority('medium')
def track_topic(bot, trigger):
    """Track channels' topics."""
    if trigger.event != 'TOPIC':
        channel = trigger.args[1]
    else:
        channel = trigger.args[0]
    if channel not in bot.channels:
        return
    bot.channels[channel].topic = trigger.args[-1]
    LOGGER.info("Channel's topic updated: %s", channel)


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
