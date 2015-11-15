# coding=utf-8
"""
bot.py - Sopel IRC Bot
Copyright 2008, Sean B. Palmer, inamidst.com
Copyright 2012, Edward Powell, http://embolalia.net
Copyright © 2012, Elad Alfassa <elad@fedoraproject.org>

Licensed under the Eiffel Forum License 2.

http://sopel.chat/
"""
from __future__ import unicode_literals, absolute_import, print_function, division

import collections
import os
import re
import sys
import threading
import time

from sopel import tools
from sopel import irc
from sopel.db import SopelDB
from sopel.tools import stderr, Identifier
import sopel.tools.jobs
from sopel.trigger import Trigger
from sopel.module import NOLIMIT
from sopel.logger import get_logger
import sopel.loader


LOGGER = get_logger(__name__)

if sys.version_info.major >= 3:
    unicode = str
    basestring = str
    py3 = True
else:
    py3 = False


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
        self.config = config
        """The ``Config`` for the current Sopel instance."""
        self.doc = {}
        """
        A dictionary of command names to their docstring and example, if
        declared. The first item in a callable's commands list is used as the
        key in version *3.2* onward. Prior to *3.2*, the name of the function
        as declared in the source code was used.
        """
        self.command_groups = collections.defaultdict(list)
        """A mapping of module names to a list of commands in it."""
        self.stats = {}
        """
        A dictionary which maps a tuple of a function name and where it was
        used to the nuber of times it was used there.
        """
        self.times = {}
        """
        A dictionary mapping lower-case'd nicks to dictionaries which map
        funtion names to the time which they were last used by that nick.
        """
        self.acivity = {}

        self.server_capabilities = {}
        """A dict mapping supported IRCv3 capabilities to their options.

        For example, if the server specifies the capability ``sasl=EXTERNAL``,
        it will be here as ``{"sasl": "EXTERNAL"}``. Capabilities specified
        without any options will have ``None`` as the value.

        For servers that do not support IRCv3, this will be an empty set."""
        self.enabled_capabilities = set()
        """A set containing the IRCv3 capabilities that the bot has enabled."""
        self._cap_reqs = dict()
        """A dictionary of capability requests

        Maps the capability name to a list of tuples of the prefix ('-', '=',
        or ''), the name of the requesting module, the function to call if the
        the request is rejected, and the argument to the capability (or None).
        """

        self.privileges = dict()
        """A dictionary of channels to their users and privilege levels

        The value associated with each channel is a dictionary of Identifiers to a
        bitwise integer value, determined by combining the appropriate constants
        from `module`."""

        self.db = SopelDB(config)
        """The bot's database."""

        self.memory = tools.SopelMemory()
        """
        A thread-safe dict for storage of runtime data to be shared between
        modules. See `SopelMemory <#tools.Sopel.SopelMemory>`_
        """

        self.scheduler = sopel.tools.jobs.JobScheduler(self)
        self.scheduler.start()

        # Set up block lists
        # Default to empty
        if not self.config.core.nick_blocks:
            self.config.core.nick_blocks = []
        if not self.config.core.nick_blocks:
            self.config.core.host_blocks = []
        self.setup()

    def setup(self):
        stderr("\nWelcome to Sopel. Loading modules...\n\n")

        modules = sopel.loader.enumerate_modules(self.config)

        error_count = 0
        success_count = 0
        for name in modules:
            path, type_ = modules[name]

            try:
                module, _ = sopel.loader.load_module(name, path, type_)
            except Exception as e:
                error_count = error_count + 1
                filename, lineno = tools.get_raising_file_and_line()
                rel_path = os.path.relpath(filename, os.path.dirname(__file__))
                raising_stmt = "%s:%d" % (rel_path, lineno)
                stderr("Error loading %s: %s (%s)" % (name, e, raising_stmt))
            else:
                try:
                    if hasattr(module, 'setup'):
                        module.setup(self)
                    relevant_parts = sopel.loader.clean_module(
                        module, self.config)
                except Exception as e:
                    error_count = error_count + 1
                    filename, lineno = tools.get_raising_file_and_line()
                    rel_path = os.path.relpath(
                        filename, os.path.dirname(__file__)
                    )
                    raising_stmt = "%s:%d" % (rel_path, lineno)
                    stderr("Error in %s setup procedure: %s (%s)"
                           % (name, e, raising_stmt))
                else:
                    self.register(*relevant_parts)
                    success_count += 1

        if len(modules) > 2:  # coretasks is counted
            stderr('\n\nRegistered %d modules,' % (success_count - 1))
            stderr('%d modules failed to load\n\n' % error_count)
        else:
            stderr("Warning: Couldn't load any modules")

    def unregister(self, obj):
        if not callable(obj):
            return
        if hasattr(obj, 'rule'):  # commands and intents have it added
            for rule in obj.rule:
                callb_list = self._callables[obj.priority][rule]
                if obj in callb_list:
                    callb_list.remove(obj)
        if hasattr(obj, 'interval'):
            # TODO this should somehow find the right job to remove, rather than
            # clearing the entire queue. Issue #831
            self.scheduler.clear_jobs()
        if (getattr(obj, '__name__', None) == 'shutdown'
                and obj in self.shutdown_methods):
            self.shutdown_methods.remove(obj)

    def register(self, callables, jobs, shutdowns):
        self.shutdown_methods = shutdowns
        for callbl in callables:
            for rule in callbl.rule:
                self._callables[callbl.priority][rule].append(callbl)
            if hasattr(callbl, 'commands'):
                module_name = callbl.__module__.rsplit('.', 1)[-1]
                # TODO doc and make decorator for this. Not sure if this is how
                # it should work yet, so not making it public for 6.0.
                category = getattr(callbl, 'category', module_name)
                self.command_groups[category].append(callbl.commands[0])
            for command, docs in callbl._docs.items():
                self.doc[command] = docs
        for func in jobs:
            for interval in func.interval:
                job = sopel.tools.jobs.Job(interval, func)
                self.scheduler.add_job(job)

    class SopelWrapper(object):
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
            if destination is None:
                destination = self._trigger.sender
            self._bot.say(message, destination, max_messages)

        def action(self, message, destination=None):
            if destination is None:
                destination = self._trigger.sender
            self._bot.action(message, destination)

        def notice(self, message, destination=None):
            if destination is None:
                destination = self._trigger.sender
            self._bot.notice(message, destination)

        def reply(self, message, destination=None, reply_to=None, notice=False):
            if destination is None:
                destination = self._trigger.sender
            if reply_to is None:
                reply_to = self._trigger.nick
            self._bot.reply(message, destination, reply_to, notice)

    def call(self, func, sopel, trigger):
        nick = trigger.nick
        if nick not in self.times:
            self.times[nick] = dict()

        if not trigger.admin and \
                not func.unblockable and \
                func.rate > 0 and \
                func in self.times[nick]:
            timediff = time.time() - self.times[nick][func]
            if timediff < func.rate:
                self.times[nick][func] = time.time()
                LOGGER.info(
                    "%s prevented from using %s in %s: %d < %d",
                    trigger.nick, func.__name__, trigger.sender, timediff,
                    func.rate
                )
                return

        try:
            exit_code = func(sopel, trigger)
        except Exception:
            exit_code = None
            self.error(trigger)

        if exit_code != NOLIMIT:
            self.times[nick][func] = time.time()

    def dispatch(self, pretrigger):
        args = pretrigger.args
        event, args, text = pretrigger.event, args, args[-1]

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
                trigger = Trigger(self.config, pretrigger, match)
                wrapper = self.SopelWrapper(self, trigger)

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
                    if (hasattr(func, 'intents') and
                            trigger.tags.get('intent') not in func.intents):
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

    def cap_req(self, module_name, capability, arg=None, failure_callback=None):
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
        capability. In future versions

        If ``arg`` is given, and does not exactly match what the server
        provides or what other modules have requested for that capability, it is
        considered a conflict.
        """
        # TODO raise better exceptions
        cap = capability[1:]
        prefix = capability[0]

        entry = self._cap_reqs.get(cap, [])
        if any((ent[3] != arg for ent in entry)):
            raise Exception('Capability conflict')

        if prefix == '-':
            if self.connection_registered and cap in self.enabled_capabilities:
                raise Exception('Can not change capabilities after server '
                                'connection has been completed.')
            if any((ent[0] != '-' for ent in entry)):
                raise Exception('Capability conflict')
            entry.append((prefix, module_name, failure_callback, arg))
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
            if any((ent[0] == '-' for ent in entry)) and prefix == '=':
                raise Exception('Capability conflict')
            entry.append((prefix, module_name, failure_callback, arg))
            self._cap_reqs[cap] = entry
