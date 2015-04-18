# coding=utf8
"""
bot.py - Willie IRC Bot
Copyright 2008, Sean B. Palmer, inamidst.com
Copyright 2012, Edward Powell, http://embolalia.net
Copyright © 2012, Elad Alfassa <elad@fedoraproject.org>

Licensed under the Eiffel Forum License 2.

http://willie.dftba.net/
"""
from __future__ import unicode_literals
from __future__ import print_function
from __future__ import absolute_import

import collections
import imp
import os
import re
import socket
import sys
import threading
import time

from datetime import datetime
from willie import tools
import willie.irc as irc
from willie.db import WillieDB
from willie.tools import (stderr, PriorityQueue, Identifier, released, get_command_regexp,
                          iteritems, itervalues)
from willie.trigger import Trigger
import willie.module as module
from willie.logger import get_logger
import willie.loader


LOGGER = get_logger(__name__)

if sys.version_info.major >= 3:
    unicode = str
    basestring = str
    py3 = True
else:
    py3 = False


class Willie(irc.Bot):
    NOLIMIT = module.NOLIMIT

    def __init__(self, config):
        irc.Bot.__init__(self, config.core)
        # `re.compile('.*') is re.compile('.*')` because of caching, so we need
        # to associate a list with each regex, since they are unexpectedly
        # indistinct.
        self._callables = {
            'high': collections.defaultdict(list),
            'medium': collections.defaultdict(list),
            'low': collections.defaultdict(list)
        }
        self.config = config
        """The ``Config`` for the current Willie instance."""
        self.doc = {}
        """
        A dictionary of command names to their docstring and example, if
        declared. The first item in a callable's commands list is used as the
        key in version *3.2* onward. Prior to *3.2*, the name of the function
        as declared in the source code was used.
        """
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

        self.server_capabilities = set()
        """A set containing the IRCv3 capabilities that the server supports.

        For servers that do not support IRCv3, this will be an empty set."""
        self.enabled_capabilities = set()
        """A set containing the IRCv3 capabilities that the bot has enabled."""
        self._cap_reqs = dict()
        """A dictionary of capability requests

        Maps the capability name to a list of tuples of the prefix ('-', '=',
        or ''), the name of the requesting module, and the function to call if
        the request is rejected."""

        self.privileges = dict()
        """A dictionary of channels to their users and privilege levels

        The value associated with each channel is a dictionary of Identifiers to a
        bitwise integer value, determined by combining the appropriate constants
        from `module`."""

        self.db = WillieDB(config)
        """The bot's database."""

        self.memory = tools.WillieMemory()
        """
        A thread-safe dict for storage of runtime data to be shared between
        modules. See `WillieMemory <#tools.Willie.WillieMemory>`_
        """

        self.scheduler = Willie.JobScheduler(self)
        self.scheduler.start()

        #Set up block lists
        #Default to empty
        if not self.config.core.nick_blocks:
            self.config.core.nick_blocks = []
        if not self.config.core.nick_blocks:
            self.config.core.host_blocks = []

        self.setup()

    class JobScheduler(threading.Thread):

        """Calls jobs assigned to it in steady intervals.

        JobScheduler is a thread that keeps track of Jobs and calls them every
        X seconds, where X is a property of the Job. It maintains jobs in a
        priority queue, where the next job to be called is always the first
        item.
        Thread safety is maintained with a mutex that is released during long
        operations, so methods add_job and clear_jobs can be safely called from
        the main thread.

        """

        min_reaction_time = 30.0  # seconds
        """How often should scheduler checks for changes in the job list."""

        def __init__(self, bot):
            """Requires bot as argument for logging."""
            threading.Thread.__init__(self)
            self.bot = bot
            self._jobs = PriorityQueue()
            # While PriorityQueue it self is thread safe, this mutex is needed
            # to stop old jobs being put into new queue after clearing the
            # queue.
            self._mutex = threading.Lock()
            # self.cleared is used for more fine grained locking.
            self._cleared = False

        def add_job(self, job):
            """Add a Job to the current job queue."""
            self._jobs.put(job)

        def clear_jobs(self):
            """Clear current Job queue and start fresh."""
            if self._jobs.empty():
                # Guards against getting stuck waiting for self._mutex when
                # thread is waiting for self._jobs to not be empty.
                return
            with self._mutex:
                self._cleared = True
                self._jobs = PriorityQueue()

        def run(self):
            """Run forever."""
            while True:
                try:
                    self._do_next_job()
                except Exception:
                    # Modules exceptions are caught earlier, so this is a bit
                    # more serious. Options are to either stop the main thread
                    # or continue this thread and hope that it won't happen
                    # again.
                    self.bot.error()
                    # Sleep a bit to guard against busy-looping and filling
                    # the log with useless error messages.
                    time.sleep(10.0)  # seconds

        def _do_next_job(self):
            """Wait until there is a job and do it."""
            with self._mutex:
                # Wait until the next job should be executed.
                # This has to be a loop, because signals stop time.sleep().
                while True:
                    job = self._jobs.peek()
                    difference = job.next_time - time.time()
                    duration = min(difference, self.min_reaction_time)
                    if duration <= 0:
                        break
                    with released(self._mutex):
                        time.sleep(duration)

                self._cleared = False
                job = self._jobs.get()
                with released(self._mutex):
                    if job.func.thread:
                        t = threading.Thread(
                            target=self._call, args=(job.func,)
                        )
                        t.start()
                    else:
                        self._call(job.func)
                    job.next()
                # If jobs were cleared during the call, don't put an old job
                # into the new job queue.
                if not self._cleared:
                    self._jobs.put(job)

        def _call(self, func):
            """Wrapper for collecting errors from modules."""
            # Willie.bot.call is way too specialized to be used instead.
            try:
                func(self.bot)
            except Exception:
                self.bot.error()

    class Job(object):

        """Hold information about when a function should be called next.

        Job is a simple structure that hold information about when a function
        should be called next.
        They can be put in a priority queue, in which case the Job that should
        be executed next is returned.

        Calling the method next modifies the Job object for the next time it
        should be executed. Current time is used to decide when the job should
        be executed next so it should only be called right after the function
        was called.

        """

        max_catchup = 5
        """
        This governs how much the scheduling of jobs is allowed
        to get behind before they are simply thrown out to avoid
        calling the same function too many times at once.
        """

        def __init__(self, interval, func):
            """Initialize Job.

            Args:
                interval: number of seconds between calls to func
                func: function to be called

            """
            self.next_time = time.time() + interval
            self.interval = interval
            self.func = func

        def next(self):
            """Update self.next_time with the assumption func was just called.

            Returns: A modified job object.

            """
            last_time = self.next_time
            current_time = time.time()
            delta = last_time + self.interval - current_time

            if last_time > current_time + self.interval:
                # Clock appears to have moved backwards. Reset
                # the timer to avoid waiting for the clock to
                # catch up to whatever time it was previously.
                self.next_time = current_time + self.interval
            elif delta < 0 and abs(delta) > self.interval * self.max_catchup:
                # Execution of jobs is too far behind. Give up on
                # trying to catch up and reset the time, so that
                # will only be repeated a maximum of
                # self.max_catchup times.
                self.next_time = current_time - \
                    self.interval * self.max_catchup
            else:
                self.next_time = last_time + self.interval

            return self

        def __cmp__(self, other):
            """Compare Job objects according to attribute next_time."""
            return self.next_time - other.next_time

        if py3:
            def __lt__(self, other):
                return self.next_time < other.next_time

            def __gt__(self, other):
                return self.next_time > other.next_time

        def __str__(self):
            """Return a string representation of the Job object.

            Example result:
                <Job(2013-06-14 11:01:36.884000, 20s, <function upper at 0x02386BF0>)>

            """
            iso_time = str(datetime.fromtimestamp(self.next_time))
            return "<Job(%s, %ss, %s)>" % \
                (iso_time, self.interval, self.func)

        def __iter__(self):
            """This is an iterator. Never stops though."""
            return self

    def setup(self):
        stderr("\nWelcome to Willie. Loading modules...\n\n")

        modules = willie.loader.enumerate_modules(self.config)

        error_count = 0
        success_count = 0
        for name in modules:
            path, type_ = modules[name]

            try:
                module, _ = willie.loader.load_module(name, path, type_)
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
                    relevant_parts = willie.loader.clean_module(
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

        if modules:
            stderr('\n\nRegistered %d modules,' % (success_count - 1))
            stderr('%d modules failed to load\n\n' % error_count)
        else:
            # TODO since this includes coretasks, this should probably be fatal
            stderr("Warning: Couldn't load any modules")

    def register(self, callables, jobs, shutdowns):
        self.shutdown_methods = shutdowns
        for callbl in callables:
            for rule in callbl.rule:
                self._callables[callbl.priority][rule].append(callbl)
        # TODO jobs

    class WillieWrapper(object):
        def __init__(self, willie, trigger):
            # The custom __setattr__ for this class sets the attribute on the
            # original bot object. We don't want that for these, so we set them
            # with the normal __setattr__.
            object.__setattr__(self, '_bot', willie)
            object.__setattr__(self, '_trigger', trigger)

        def __dir__(self):
            classattrs = [attr for attr in self.__class__.__dict__
                          if not attr.startswith('__')]
            return list(self.__dict__) + classattrs + dir(self._bot)

        def say(self, string, max_messages=1):
            self._bot.msg(self._trigger.sender, string, max_messages)

        def reply(self, string, notice=False):
            if isinstance(string, str) and not py3:
                string = string.decode('utf8')
            if notice:
                self.notice(
                    '%s: %s' % (self._trigger.nick, string),
                    self._trigger.sender
                )
            else:
                self._bot.msg(
                    self._trigger.sender,
                    '%s: %s' % (self._trigger.nick, string)
                )

        def action(self, string, recipient=None):
            if recipient is None:
                recipient = self._trigger.sender
            self._bot.msg(recipient, '\001ACTION %s\001' % string)

        def notice(self, string, recipient=None):
            if recipient is None:
                recipient = self._trigger.sender
            self.write(('NOTICE', recipient), string)

        def __getattr__(self, attr):
            return getattr(self._bot, attr)

        def __setattr__(self, attr, value):
            return setattr(self._bot, attr, value)

    def call(self, func, willie, trigger):
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
            exit_code = func(willie, trigger)
        except Exception:
            exit_code = None
            self.error(trigger)

        if exit_code != module.NOLIMIT:
            self.times[nick][func] = time.time()

    def limit(self, trigger, func):
        if trigger.sender and not trigger.sender.is_nick():
            if self.config.has_section('limit'):
                limits = self.config.limit.get(trigger.sender)
                if limits and (func.__module__ not in limits):
                    return True
        return False

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
                wrapper = self.WillieWrapper(self, trigger)

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
                    if self.limit(trigger, func):
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
        bad_masks = self.config.core.get_list('host_blocks')
        for bad_mask in bad_masks:
            bad_mask = bad_mask.strip()
            if not bad_mask:
                continue
            if (re.match(bad_mask + '$', host, re.IGNORECASE) or
                    bad_mask == host):
                return True
        return False

    def _nick_blocked(self, nick):
        bad_nicks = self.config.core.get_list('nick_blocks')
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

    def cap_req(self, module_name, capability, failure_callback):
        """Tell Willie to request a capability when it starts.

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
        The arguments will be a `Willie` object, and the capability which was
        rejected. This can be used to disable callables which rely on the
        capability.

        """
        #TODO raise better exceptions
        cap = capability[1:]
        prefix = capability[0]

        if prefix == '-':
            if self.connection_registered and cap in self.enabled_capabilities:
                raise Exception('Can not change capabilities after server '
                                'connection has been completed.')
            entry = self._cap_reqs.get(cap, [])
            if any((ent[0] != '-' for ent in entry)):
                raise Exception('Capability conflict')
            entry.append((prefix, module_name, failure_callback))
            self._cap_reqs[cap] = entry
        else:
            if prefix != '=':
                cap = capability
                prefix = ''
            if self.connection_registered and (cap not in
                                               self.enabled_capabilities):
                raise Exception('Can not change capabilities after server '
                                'connection has been completed.')
            entry = self._cap_reqs.get(cap, [])
            # Non-mandatory will callback at the same time as if the server
            # rejected it.
            if any((ent[0] == '-' for ent in entry)) and prefix == '=':
                raise Exception('Capability conflict')
            entry.append((prefix, module_name, failure_callback))
            self._cap_reqs[cap] = entry
