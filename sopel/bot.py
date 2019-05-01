# coding=utf-8
# Copyright 2008, Sean B. Palmer, inamidst.com
# Copyright © 2012, Elad Alfassa <elad@fedoraproject.org>
# Copyright 2012-2015, Elsie Powell, http://embolalia.com
#
# Licensed under the Eiffel Forum License 2.

from __future__ import unicode_literals, absolute_import, print_function, division

from ast import literal_eval
import collections
import itertools
import os
import re
import sys
import threading
import time

from sopel import irc, plugins, tools
from sopel.db import SopelDB
from sopel.tools import stderr, Identifier, deprecated
import sopel.tools.jobs
from sopel.trigger import Trigger
from sopel.module import NOLIMIT
from sopel.logger import get_logger
import sopel.loader


__all__ = ['Sopel', 'SopelWrapper']

LOGGER = get_logger(__name__)

if sys.version_info.major >= 3:
    unicode = str
    basestring = str
    py3 = True
else:
    py3 = False


class _CapReq(object):
    def __init__(self, prefix, module, failure=None, arg=None, success=None):
        def nop(bot, cap):
            pass
        # TODO at some point, reorder those args to be sane
        self.prefix = prefix
        self.module = module
        self.arg = arg
        self.failure = failure or nop
        self.success = success or nop


class Sopel(irc.Bot):
    def __init__(self, config, daemon=False):
        irc.Bot.__init__(self, config)
        self._daemon = daemon  # Used for iPython. TODO something saner here
        # `re.compile('.*') is re.compile('.*')` because of caching, so we need
        # to associate a list with each regex, since they are unexpectedly
        # indistinct.
        self._callables = {
            'high': collections.defaultdict(list),
            'medium': collections.defaultdict(list),
            'low': collections.defaultdict(list)
        }
        self._plugins = {}
        self.config = config
        """The :class:`sopel.config.Config` for the current Sopel instance."""
        self.doc = {}
        """
        A dictionary of command names to their docstring and example, if
        declared. The first item in a callable's commands list is used as the
        key in version *3.2* onward. Prior to *3.2*, the name of the function
        as declared in the source code was used.
        """
        self._command_groups = collections.defaultdict(list)
        """A mapping of module names to a list of commands in it."""
        self.stats = {}  # deprecated, remove in 7.0
        self._times = {}
        """
        A dictionary mapping lower-case'd nicks to dictionaries which map
        funtion names to the time which they were last used by that nick.
        """

        self.server_capabilities = {}
        """A dict mapping supported IRCv3 capabilities to their options.

        For example, if the server specifies the capability ``sasl=EXTERNAL``,
        it will be here as ``{"sasl": "EXTERNAL"}``. Capabilities specified
        without any options will have ``None`` as the value.

        For servers that do not support IRCv3, this will be an empty set."""
        self.enabled_capabilities = set()
        """A set containing the IRCv3 capabilities that the bot has enabled."""
        self._cap_reqs = dict()
        """A dictionary of capability names to a list of requests"""

        self.privileges = dict()
        """A dictionary of channels to their users and privilege levels

        The value associated with each channel is a dictionary of
        :class:`sopel.tools.Identifier`\\s to
        a bitwise integer value, determined by combining the appropriate
        constants from :mod:`sopel.module`.

        .. deprecated:: 6.2.0
            Use :attr:`channels` instead. Will be removed in Sopel 8.
        """

        self.channels = tools.SopelMemory()  # name to chan obj
        """A map of the channels that Sopel is in.

        The keys are Identifiers of the channel names, and map to
        :class:`sopel.tools.target.Channel` objects which contain the users in
        the channel and their permissions.
        """
        self.users = tools.SopelMemory()  # name to user obj
        """A map of the users that Sopel is aware of.

        The keys are Identifiers of the nicknames, and map to
        :class:`sopel.tools.target.User` instances. In order for Sopel to be
        aware of a user, it must be in at least one channel which they are also
        in.
        """

        self.db = SopelDB(config)
        """The bot's database, as a :class:`sopel.db.SopelDB` instance."""

        self.memory = tools.SopelMemory()
        """
        A thread-safe dict for storage of runtime data to be shared between
        modules. See :class:`sopel.tools.Sopel.SopelMemory`
        """

        self.shutdown_methods = []
        """List of methods to call on shutdown"""

        self.scheduler = sopel.tools.jobs.JobScheduler(self)
        self.scheduler.start()

        # Set up block lists
        # Default to empty
        if not self.config.core.nick_blocks:
            self.config.core.nick_blocks = []
        if not self.config.core.host_blocks:
            self.config.core.host_blocks = []
        self.setup()

    @property
    def hostmask(self):
        """str: the current hostmask for the bot :class:`sopel.tools.target.User`

        Bot must be connected and in at least one channel.
        """
        if not self.users or self.nick not in self.users:
            raise KeyError("'hostmask' not available: bot must be connected and in at least one channel.")

        return self.users.get(self.nick).hostmask

    # Backwards-compatibility aliases to attributes made private in 6.2. Remove
    # these in 7.0
    times = property(lambda self: getattr(self, '_times'))
    command_groups = property(lambda self: getattr(self, '_command_groups'))

    def write(self, args, text=None):  # Shim this in here for autodocs
        """Send a command to the server.

        ``args`` is an iterable of strings, which are joined by spaces.
        ``text`` is treated as though it were the final item in ``args``, but
        is preceeded by a ``:``. This is a special case which  means that
        ``text``, unlike the items in ``args`` may contain spaces (though this
        constraint is not checked by ``write``).

        In other words, both ``sopel.write(('PRIVMSG',), 'Hello, world!')``
        and ``sopel.write(('PRIVMSG', ':Hello, world!'))`` will send
        ``PRIVMSG :Hello, world!`` to the server.

        Newlines and carriage returns ('\\n' and '\\r') are removed before
        sending. Additionally, if the message (after joining) is longer than
        than 510 characters, any remaining characters will not be sent.
        """
        irc.Bot.write(self, args, text=text)

    def setup(self):
        load_success = 0
        load_error = 0
        load_disabled = 0

        stderr("Welcome to Sopel. Loading modules...")
        usable_plugins = plugins.get_usable_plugins(self.config)
        for name, info in usable_plugins.items():
            plugin, is_enabled = info
            if not is_enabled:
                load_disabled = load_disabled + 1
                continue

            try:
                plugin.load()
            except Exception as e:
                load_error = load_error + 1
                filename, lineno = tools.get_raising_file_and_line()
                rel_path = os.path.relpath(filename, os.path.dirname(__file__))
                raising_stmt = "%s:%d" % (rel_path, lineno)
                stderr("Error loading %s: %s (%s)" % (name, e, raising_stmt))
            else:
                try:
                    if plugin.has_setup():
                        plugin.setup(self)
                    plugin.register(self)
                except Exception as e:
                    load_error = load_error + 1
                    filename, lineno = tools.get_raising_file_and_line()
                    rel_path = os.path.relpath(
                        filename, os.path.dirname(__file__)
                    )
                    raising_stmt = "%s:%d" % (rel_path, lineno)
                    stderr("Error in %s setup procedure: %s (%s)"
                           % (name, e, raising_stmt))
                else:
                    load_success = load_success + 1
                    print('Loaded: %s' % name)

        total = sum([load_success, load_error, load_disabled])
        if total and load_success:
            stderr('Registered %d modules' % (load_success - 1))
            stderr('%d modules failed to load' % load_error)
            stderr('%d modules disabled' % load_disabled)
        else:
            stderr("Warning: Couldn't load any modules")

    def reload_plugin(self, name):
        """Reload a plugin

        :param str name: name of the plugin to reload
        :raise PluginNotRegistered: when there is no ``name`` plugin registered

        It runs the plugin's shutdown routine and unregisters it. Then it
        reloads it, runs its setup routines, and registers it again.
        """
        if not self.has_plugin(name):
            raise plugins.exceptions.PluginNotRegistered(name)

        plugin = self._plugins[name]
        # tear down
        plugin.shutdown(self)
        plugin.unregister(self)
        print('Unloaded: %s' % name)
        # reload & setup
        plugin.reload()
        plugin.setup(self)
        plugin.register(self)
        print('Reloaded: %s' % name)

    def reload_plugins(self):
        """Reload all plugins

        First, run all plugin shutdown routines and unregister all plugins.
        Then reload all plugins, run their setup routines, and register them
        again.
        """
        registered = list(self._plugins.items())
        # tear down all plugins
        for name, plugin in registered:
            plugin.shutdown(self)
            plugin.unregister(self)
            print('Unloaded: %s' % name)

        # reload & setup all plugins
        for name, plugin in registered:
            plugin.reload()
            plugin.setup(self)
            plugin.register(self)
            print('Reloaded: %s' % name)

    def add_plugin(self, plugin, callables, jobs, shutdowns, urls):
        """Add a loaded plugin to the bot's registry"""
        self._plugins[plugin.name] = plugin
        self.register(callables, jobs, shutdowns, urls)

    def remove_plugin(self, plugin, callables, jobs, shutdowns, urls):
        """Remove a loaded plugin from the bot's registry"""
        name = plugin.name
        if not self.has_plugin(name):
            raise plugins.exceptions.PluginNotRegistered(name)

        try:
            # remove commands, jobs, and shutdown functions
            for func in itertools.chain(callables, jobs, shutdowns):
                self.unregister(func)

            # remove URL callback handlers
            if self.memory.contains('url_callbacks'):
                for func in urls:
                    regex = func.url_regex
                    if func == self.memory['url_callbacks'].get(regex):
                        self.unregister_url_callback(regex)
        except:  # noqa
            # TODO: consider logging?
            raise  # re-raised
        else:
            # remove plugin from registry
            del self._plugins[name]

    def has_plugin(self, name):
        """Tell if the bot has registered this plugin by its name"""
        return name in self._plugins

    def unregister(self, obj):
        if not callable(obj):
            return
        if hasattr(obj, 'rule'):  # commands and intents have it added
            for rule in obj.rule:
                callb_list = self._callables[obj.priority][rule]
                if obj in callb_list:
                    callb_list.remove(obj)
        if hasattr(obj, 'interval'):
            self.scheduler.remove_callable_job(obj)
        if (
                getattr(obj, "__name__", None) == "shutdown" and
                obj in self.shutdown_methods
        ):
            self.shutdown_methods.remove(obj)

    def register(self, callables, jobs, shutdowns, urls):
        # Append module's shutdown function to the bot's list of functions to
        # call on shutdown
        self.shutdown_methods += shutdowns
        for callbl in callables:
            if hasattr(callbl, 'rule'):
                for rule in callbl.rule:
                    self._callables[callbl.priority][rule].append(callbl)
            else:
                self._callables[callbl.priority][re.compile('.*')].append(callbl)
            if hasattr(callbl, 'commands'):
                module_name = callbl.__module__.rsplit('.', 1)[-1]
                # TODO doc and make decorator for this. Not sure if this is how
                # it should work yet, so not making it public for 6.0.
                category = getattr(callbl, 'category', module_name)
                self._command_groups[category].append(callbl.commands[0])
            for command, docs in callbl._docs.items():
                self.doc[command] = docs
        for func in jobs:
            for interval in func.interval:
                job = sopel.tools.jobs.Job(interval, func)
                self.scheduler.add_job(job)

        for func in urls:
            self.register_url_callback(func.url_regex, func)

    def part(self, channel, msg=None):
        """Part a channel."""
        self.write(['PART', channel], msg)

    def join(self, channel, password=None):
        """Join a channel

        If `channel` contains a space, and no `password` is given, the space is
        assumed to split the argument into the channel to join and its
        password.  `channel` should not contain a space if `password` is given.

        """
        if password is None:
            self.write(('JOIN', channel))
        else:
            self.write(['JOIN', channel, password])

    @deprecated
    def msg(self, recipient, text, max_messages=1):
        """
        .. deprecated:: 6.0
            Use :meth:`say` instead. Will be removed in Sopel 8.
        """
        self.say(text, recipient, max_messages)

    def say(self, text, recipient, max_messages=1):
        """Send ``text`` as a PRIVMSG to ``recipient``.

        In the context of a triggered callable, the ``recipient`` defaults to
        the channel (or nickname, if a private message) from which the message
        was received.

        By default, this will attempt to send the entire ``text`` in one
        message. If the text is too long for the server, it may be truncated.
        If ``max_messages`` is given, the ``text`` will be split into at most
        that many messages, each no more than 400 bytes. The split is made at
        the last space character before the 400th byte, or at the 400th byte if
        no such space exists. If the ``text`` is too long to fit into the
        specified number of messages using the above splitting, the final
        message will contain the entire remainder, which may be truncated by
        the server.
        """
        excess = ''
        if not isinstance(text, unicode):
            # Make sure we are dealing with unicode string
            text = text.decode('utf-8')

        if max_messages > 1:
            # Manage multi-line only when needed
            text, excess = tools.get_sendable_message(text)

        try:
            self.sending.acquire()

            recipient_id = Identifier(recipient)
            recipient_stack = self.stack.setdefault(recipient_id, {
                'messages': [],
                'flood_left': self.config.core.flood_burst_lines,
            })

            if recipient_stack['messages']:
                elapsed = time.time() - recipient_stack['messages'][-1][0]
            else:
                # Default to a high enough value that we won't care.
                # Five minutes should be enough not to matter anywhere below.
                elapsed = 300

            # If flood bucket is empty, refill the appropriate number of lines
            # based on how long it's been since our last message to recipient
            if not recipient_stack['flood_left']:
                recipient_stack['flood_left'] = min(
                    self.config.core.flood_burst_lines,
                    int(elapsed) * self.config.core.flood_refill_rate)

            # If it's too soon to send another message, wait
            if not recipient_stack['flood_left']:
                penalty = float(max(0, len(text) - 50)) / 70
                wait = min(self.config.core.flood_empty_wait + penalty, 2)  # Maximum wait time is 2 sec
                if elapsed < wait:
                    time.sleep(wait - elapsed)

            # Loop detection
            messages = [m[1] for m in recipient_stack['messages'][-8:]]

            # If what we're about to send repeated at least 5 times in the last
            # two minutes, replace it with '...'
            if messages.count(text) >= 5 and elapsed < 120:
                text = '...'
                if messages.count('...') >= 3:
                    # If we've already said '...' 3 times, discard message
                    return

            self.write(('PRIVMSG', recipient), text)
            recipient_stack['flood_left'] = max(0, recipient_stack['flood_left'] - 1)
            recipient_stack['messages'].append((time.time(), self.safe(text)))
            recipient_stack['messages'] = recipient_stack['messages'][-10:]
        finally:
            self.sending.release()
        # Now that we've sent the first part, we need to send the rest. Doing
        # this recursively seems easier to me than iteratively
        if excess:
            self.say(excess, max_messages - 1, recipient)

    def notice(self, text, dest):
        """Send an IRC NOTICE to a user or a channel.

        Within the context of a triggered callable, ``dest`` will default to
        the channel (or nickname, if a private message), in which the trigger
        happened.
        """
        self.write(('NOTICE', dest), text)

    def action(self, text, dest):
        """Send ``text`` as a CTCP ACTION PRIVMSG to ``dest``.

        The same loop detection and length restrictions apply as with
        :func:`say`, though automatic message splitting is not available.

        Within the context of a triggered callable, ``dest`` will default to
        the channel (or nickname, if a private message), in which the trigger
        happened.
        """
        self.say('\001ACTION {}\001'.format(text), dest)

    def reply(self, text, dest, reply_to, notice=False):
        """Prepend ``reply_to`` to ``text``, and send as a PRIVMSG to ``dest``.

        If ``notice`` is ``True``, send a NOTICE rather than a PRIVMSG.

        The same loop detection and length restrictions apply as with
        :func:`say`, though automatic message splitting is not available.

        Within the context of a triggered callable, ``reply_to`` will default to
        the nickname of the user who triggered the call, and ``dest`` to the
        channel (or nickname, if a private message), in which the trigger
        happened.
        """
        text = '%s: %s' % (reply_to, text)
        if notice:
            self.notice(text, dest)
        else:
            self.say(text, dest)

    def kick(self, nick, channel, text=None):
        """Send an IRC KICK command.
        Within the context of a triggered callable, ``channel`` will default to the
        channel in which the call was triggered. If triggered from a private message,
        ``channel`` is required (or the call to ``kick()`` will be ignored).
        The bot must be a channel operator in specified channel for this to work.
        .. versionadded:: 7.0
        """
        self.write(['KICK', channel, nick], text)

    def call(self, func, sopel, trigger):
        nick = trigger.nick
        current_time = time.time()
        if nick not in self._times:
            self._times[nick] = dict()
        if self.nick not in self._times:
            self._times[self.nick] = dict()
        if not trigger.is_privmsg and trigger.sender not in self._times:
            self._times[trigger.sender] = dict()

        if not trigger.admin and not func.unblockable:
            if func in self._times[nick]:
                usertimediff = current_time - self._times[nick][func]
                if func.rate > 0 and usertimediff < func.rate:
                    LOGGER.info(
                        "%s prevented from using %s in %s due to user limit: %d < %d",
                        trigger.nick, func.__name__, trigger.sender, usertimediff,
                        func.rate
                    )
                    return
            if func in self._times[self.nick]:
                globaltimediff = current_time - self._times[self.nick][func]
                if func.global_rate > 0 and globaltimediff < func.global_rate:
                    LOGGER.info(
                        "%s prevented from using %s in %s due to global limit: %d < %d",
                        trigger.nick, func.__name__, trigger.sender, globaltimediff,
                        func.global_rate
                    )
                    return

            if not trigger.is_privmsg and func in self._times[trigger.sender]:
                chantimediff = current_time - self._times[trigger.sender][func]
                if func.channel_rate > 0 and chantimediff < func.channel_rate:
                    LOGGER.info(
                        "%s prevented from using %s in %s due to channel limit: %d < %d",
                        trigger.nick, func.__name__, trigger.sender, chantimediff,
                        func.channel_rate
                    )
                    return

        # if channel has its own config section, check for excluded modules/modules methods
        if trigger.sender in self.config:
            channel_config = self.config[trigger.sender]

            # disable listed modules completely on provided channel
            if 'disable_modules' in channel_config:
                disabled_modules = channel_config.disable_modules.split(',')

                # if "*" is used, we are disabling all modules on provided channel
                if '*' in disabled_modules:
                    return
                if func.__module__ in disabled_modules:
                    return

            # disable chosen methods from modules
            if 'disable_commands' in channel_config:
                disabled_commands = literal_eval(channel_config.disable_commands)

                if func.__module__ in disabled_commands:
                    if func.__name__ in disabled_commands[func.__module__]:
                        return

        try:
            exit_code = func(sopel, trigger)
        except Exception:  # TODO: Be specific
            exit_code = None
            self.error(trigger)

        if exit_code != NOLIMIT:
            self._times[nick][func] = current_time
            self._times[self.nick][func] = current_time
            if not trigger.is_privmsg:
                self._times[trigger.sender][func] = current_time

    def dispatch(self, pretrigger):
        args = pretrigger.args
        event, args, text = pretrigger.event, args, args[-1] if args else ''

        if self.config.core.nick_blocks or self.config.core.host_blocks:
            nick_blocked = self._nick_blocked(pretrigger.nick)
            host_blocked = self._host_blocked(pretrigger.host)
        else:
            nick_blocked = host_blocked = None

        list_of_blocked_functions = []
        for priority in ('high', 'medium', 'low'):
            items = self._callables[priority].items()

            for regexp, funcs in items:
                match = regexp.match(text)
                if not match:
                    continue
                user_obj = self.users.get(pretrigger.nick)
                account = user_obj.account if user_obj else None
                trigger = Trigger(self.config, pretrigger, match, account)
                wrapper = SopelWrapper(self, trigger)

                for func in funcs:
                    if (not trigger.admin and
                            not func.unblockable and
                            (nick_blocked or host_blocked)):
                        function_name = "%s.%s" % (
                            func.__module__, func.__name__
                        )
                        list_of_blocked_functions.append(function_name)
                        continue

                    if event not in func.event:
                        continue
                    if hasattr(func, 'intents'):
                        if not trigger.tags.get('intent'):
                            continue
                        match = False
                        for intent in func.intents:
                            if intent.match(trigger.tags.get('intent')):
                                match = True
                        if not match:
                            continue
                    if (trigger.nick.lower() == self.nick.lower() and
                            not func.echo):
                        continue
                    if func.thread:
                        targs = (func, wrapper, trigger)
                        t = threading.Thread(target=self.call, args=targs)
                        t.start()
                    else:
                        self.call(func, wrapper, trigger)

        if list_of_blocked_functions:
            if nick_blocked and host_blocked:
                block_type = 'both'
            elif nick_blocked:
                block_type = 'nick'
            else:
                block_type = 'host'
            LOGGER.info(
                "[%s]%s prevented from using %s.",
                block_type,
                trigger.nick,
                ', '.join(list_of_blocked_functions)
            )

    def _host_blocked(self, host):
        bad_masks = self.config.core.host_blocks
        for bad_mask in bad_masks:
            bad_mask = bad_mask.strip()
            if not bad_mask:
                continue
            if (re.match(bad_mask + '$', host, re.IGNORECASE) or
                    bad_mask == host):
                return True
        return False

    def _nick_blocked(self, nick):
        bad_nicks = self.config.core.nick_blocks
        for bad_nick in bad_nicks:
            bad_nick = bad_nick.strip()
            if not bad_nick:
                continue
            if (re.match(bad_nick + '$', nick, re.IGNORECASE) or
                    Identifier(bad_nick) == nick):
                return True
        return False

    def _shutdown(self):
        # Stop Job Scheduler
        stderr('Stopping the Job Scheduler.')
        self.scheduler.stop()

        try:
            self.scheduler.join(timeout=15)
        except RuntimeError:
            stderr('Unable to stop the Job Scheduler.')
        else:
            stderr('Job Scheduler stopped.')

        self.scheduler.clear_jobs()

        # Shutdown plugins
        stderr(
            'Calling shutdown for %d modules.' % (len(self.shutdown_methods),)
        )
        for shutdown_method in self.shutdown_methods:
            try:
                stderr(
                    "calling %s.%s" % (
                        shutdown_method.__module__, shutdown_method.__name__,
                    )
                )
                shutdown_method(self)
            except Exception as e:
                stderr(
                    "Error calling shutdown method for module %s:%s" % (
                        shutdown_method.__module__, e
                    )
                )
        # Avoid calling shutdown methods if we already have.
        self.shutdown_methods = []

    def cap_req(self, module_name, capability, arg=None, failure_callback=None,
                success_callback=None):
        """Tell Sopel to request a capability when it starts.

        By prefixing the capability with `-`, it will be ensured that the
        capability is not enabled. Simmilarly, by prefixing the capability with
        `=`, it will be ensured that the capability is enabled. Requiring and
        disabling is "first come, first served"; if one module requires a
        capability, and another prohibits it, this function will raise an
        exception in whichever module loads second. An exception will also be
        raised if the module is being loaded after the bot has already started,
        and the request would change the set of enabled capabilities.

        If the capability is not prefixed, and no other module prohibits it, it
        will be requested.  Otherwise, it will not be requested. Since
        capability requests that are not mandatory may be rejected by the
        server, as well as by other modules, a module which makes such a
        request should account for that possibility.

        The actual capability request to the server is handled after the
        completion of this function. In the event that the server denies a
        request, the `failure_callback` function will be called, if provided.
        The arguments will be a `Sopel` object, and the capability which was
        rejected. This can be used to disable callables which rely on the
        capability. It will be be called either if the server NAKs the request,
        or if the server enabled it and later DELs it.

        The `success_callback` function will be called upon acknowledgement of
        the capability from the server, whether during the initial capability
        negotiation, or later.

        If ``arg`` is given, and does not exactly match what the server
        provides or what other modules have requested for that capability, it is
        considered a conflict.
        """
        # TODO raise better exceptions
        cap = capability[1:]
        prefix = capability[0]

        entry = self._cap_reqs.get(cap, [])
        if any((ent.arg != arg for ent in entry)):
            raise Exception('Capability conflict')

        if prefix == '-':
            if self.connection_registered and cap in self.enabled_capabilities:
                raise Exception('Can not change capabilities after server '
                                'connection has been completed.')
            if any((ent.prefix != '-' for ent in entry)):
                raise Exception('Capability conflict')
            entry.append(_CapReq(prefix, module_name, failure_callback, arg,
                                 success_callback))
            self._cap_reqs[cap] = entry
        else:
            if prefix != '=':
                cap = capability
                prefix = ''
            if self.connection_registered and (cap not in
                                               self.enabled_capabilities):
                raise Exception('Can not change capabilities after server '
                                'connection has been completed.')
            # Non-mandatory will callback at the same time as if the server
            # rejected it.
            if any((ent.prefix == '-' for ent in entry)) and prefix == '=':
                raise Exception('Capability conflict')
            entry.append(_CapReq(prefix, module_name, failure_callback, arg,
                                 success_callback))
            self._cap_reqs[cap] = entry

    def register_url_callback(self, pattern, callback):
        """Register a ``callback`` for URLs matching the regex ``pattern``

        :param pattern: compiled regex pattern to register
        :param callback: callable object to handle matching URLs

        .. versionadded:: 7.0

            This method replaces manual management of ``url_callbacks`` in
            Sopel's plugins, so instead of doing this in ``setup()``::

                if 'url_callbacks' not in bot.memory:
                    bot.memory['url_callbacks'] = tools.SopelMemory()

                regex = re.compile(r'http://example.com/path/.*')
                bot.memory['url_callbacks'][regex] = callback

            use this much more concise pattern::

                regex = re.compile(r'http://example.com/path/.*')
                bot.register_url_callback(regex, callback)

        """
        if 'url_callbacks' not in self.memory:
            self.memory['url_callbacks'] = tools.SopelMemory()

        if isinstance(pattern, basestring):
            pattern = re.compile(pattern)

        self.memory['url_callbacks'][pattern] = callback

    def unregister_url_callback(self, pattern):
        """Unregister the callback for URLs matching the regex ``pattern``

        :param pattern: compiled regex pattern to unregister callback

        .. versionadded:: 7.0

            This method replaces manual management of ``url_callbacks`` in
            Sopel's plugins, so instead of doing this in ``shutdown()``::

                regex = re.compile(r'http://example.com/path/.*')
                try:
                    del bot.memory['url_callbacks'][regex]
                except KeyError:
                    pass

            use this much more concise pattern::

                regex = re.compile(r'http://example.com/path/.*')
                bot.unregister_url_callback(regex)

        """
        if 'url_callbacks' not in self.memory:
            # nothing to unregister
            return

        if isinstance(pattern, basestring):
            pattern = re.compile(pattern)

        try:
            del self.memory['url_callbacks'][pattern]
        except KeyError:
            pass

    def search_url_callbacks(self, url):
        """Yield callbacks found for ``url`` matching their regex pattern

        :param str url: URL found in a trigger
        :return: yield 2-value tuples of ``(callback, match)``

        For each pattern that matches the ``url`` parameter, it yields a
        2-value tuple of ``(callable, match)`` for that pattern.

        The ``callable`` is the one registered with
        :meth:`register_url_callback`, and the ``match`` is the result of
        the regex pattern's ``search`` method.

        .. versionadded:: 7.0

        .. seealso::

            The Python documentation for the `re.search`__ function and
            the `match object`__.

        .. __: https://docs.python.org/3.6/library/re.html#re.search
        .. __: https://docs.python.org/3.6/library/re.html#match-objects

        """
        if 'url_callbacks' not in self.memory:
            # nothing to search
            return

        for regex, function in tools.iteritems(self.memory['url_callbacks']):
            match = regex.search(url)
            if match:
                yield function, match


class SopelWrapper(object):
    """Wrapper around a Sopel instance and a Trigger

    :param sopel: Sopel instance
    :type sopel: :class:`sopel.bot.Sopel`
    :param trigger: IRC Trigger line
    :type trigger: :class:`sopel.trigger.Trigger`

    This wrapper will be used to call Sopel's triggered commands and rules as
    their ``bot`` argument. It acts as a proxy to :meth:`send messages<say>` to
    the sender (either a channel or in a private message) and even to
    :meth:`reply to someone<reply>` in a channel.
    """
    def __init__(self, sopel, trigger):
        # The custom __setattr__ for this class sets the attribute on the
        # original bot object. We don't want that for these, so we set them
        # with the normal __setattr__.
        object.__setattr__(self, '_bot', sopel)
        object.__setattr__(self, '_trigger', trigger)

    def __dir__(self):
        classattrs = [attr for attr in self.__class__.__dict__
                      if not attr.startswith('__')]
        return list(self.__dict__) + classattrs + dir(self._bot)

    def __getattr__(self, attr):
        return getattr(self._bot, attr)

    def __setattr__(self, attr, value):
        return setattr(self._bot, attr, value)

    def say(self, message, destination=None, max_messages=1):
        """Override :meth:`sopel.bot.Sopel.say` to send message to sender

        :param str message: message to say
        :param str destination: channel or person; defaults to trigger's sender
        :param int max_messages: max number of message splits
        """
        if destination is None:
            destination = self._trigger.sender
        self._bot.say(message, destination, max_messages)

    def action(self, message, destination=None):
        """Override :meth:`sopel.bot.Sopel.action` to send action to sender

        :param str message: action message
        :param str destination: channel or person; defaults to trigger's sender
        """
        if destination is None:
            destination = self._trigger.sender
        self._bot.action(message, destination)

    def notice(self, message, destination=None):
        """Override :meth:`sopel.bot.Sopel.notice` to send a notice to sender

        :param str message: notice message
        :param str destination: channel or person; defaults to trigger's sender
        """
        if destination is None:
            destination = self._trigger.sender
        self._bot.notice(message, destination)

    def reply(self, message, destination=None, reply_to=None, notice=False):
        """Override :meth:`sopel.bot.Sopel.reply` to reply to someone

        :param str message: reply message
        :param str destination: channel or person; defaults to trigger's sender
        :param str reply_to: person to reply to; defaults to trigger's nick
        :param bool notice: reply as an IRC notice or with a simple message
        """
        if destination is None:
            destination = self._trigger.sender
        if reply_to is None:
            reply_to = self._trigger.nick
        self._bot.reply(message, destination, reply_to, notice)

    def kick(self, nick, channel=None, message=None):
        if channel is None:
            if self._trigger.is_privmsg:
                raise RuntimeError('Error: KICK requires a channel.')
            else:
                channel = self._trigger.sender
        if nick is None:
            raise RuntimeError('Error: KICK requires a nick.')
        self._bot.kick(nick, channel, message)
