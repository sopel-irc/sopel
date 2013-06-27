# coding=utf-8
"""
bot.py - Willie IRC Bot
Copyright 2008, Sean B. Palmer, inamidst.com
Copyright 2012, Edward Powell, http://embolalia.net
Copyright © 2012, Elad Alfassa <elad@fedoraproject.org>

Licensed under the Eiffel Forum License 2.

http://willie.dftba.net/
"""

import time
import os
import re
import threading
import imp
from datetime import datetime
from willie import tools
import irc
from db import WillieDB
from tools import (stderr, Nick, PriorityQueue, released,
        get_command_regexp)
import module


class Willie(irc.Bot):
    NOLIMIT = module.NOLIMIT

    def __init__(self, config):
        irc.Bot.__init__(self, config.core)
        self.config = config
        """The ``Config`` for the current Willie instance."""
        self.doc = {}
        """
        *Removed in 3.1.2*

        A dictionary of module functions to their docstring and example, if
        declared. As of 3.1.2, this dict will be empty, and not updated.
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

        self.db = WillieDB(config)
        if self.db.check_table('locales', ['name'], 'name'):
            self.settings = self.db.locales
            self.db.preferences = self.db.locales
        elif self.db.check_table('preferences', ['name'], 'name'):
            self.settings = self.db.preferences
        elif self.db.type is not None:
            self.db.add_table('preferences', ['name'], 'name')
            self.settings = self.db.preferences

        self.memory = tools.WillieMemory()
        """
        A thread-safe dict for storage of runtime data to be shared between
        modules. See `WillieMemory <#tools.Willie.WillieMemory>`_
        """

        self.scheduler = Willie.JobScheduler(self)
        self.scheduler.start()

        #Set up block lists
        #Default to empty
        if not self.config.has_option('core', 'nick_blocks') or not self.config.core.nick_blocks:
            self.config.core.nick_blocks = []
        if not self.config.has_option('core', 'host_blocks') or not self.config.core.nick_blocks:
            self.config.core.host_blocks = []
        #Add nicks blocked under old scheme, if present
        if self.config.has_option('core', 'other_bots') and self.config.core.other_bots:
            nicks = self.config.core.get_list('nick_blocks')
            bots = self.config.core.get_list('other_bots')
            nicks.extend(bots)
            self.config.core.nick_blocks = nicks
            self.config.core.other_bots = False
            self.config.save()

        self.setup()

    class JobScheduler(threading.Thread):
        """Calls jobs assigned to it in steady intervals.

        JobScheduler is a thread that keeps track of Jobs and calls them
        every X seconds, where X is a property of the Job. It maintains jobs
        in a priority queue, where the next job to be called is always the
        first item. Thread safety is maintained with a mutex that is released
        during long operations, so methods add_job and clear_jobs can be
        safely called from the main thread.
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
                                target=self._call, args=(job.func,))
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
        """Job is a simple structure that hold information about when a function
        should be called next. They can be put in a priority queue, in which case
        the Job that should be executed next is returned.

        Calling the method next modifies the Job object for the next time it should
        be executed. Current time is used to decide when the job should be executed
        next so it should only be called right after the function was called.
        """

        max_catchup = 5
        """This governs how much the scheduling of jobs is allowed to get behind
        before they are simply thrown out to avoid calling the same function too
        many times at once.
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
                # Clock appears to have moved backwards. Reset the timer to avoid
                # waiting for the clock to catch up to whatever time it was
                # previously.
                self.next_time = current_time + self.interval
            elif delta < 0 and abs(delta) > self.interval * self.max_catchup:
                # Execution of jobs is too far behind. Give up on trying to catch
                # up and reset the time, so that will only be repeated a maximum
                # of self.max_catchup times.
                self.next_time = current_time - self.interval * self.max_catchup
            else:
                self.next_time = last_time + self.interval

            return self

        def __cmp__(self, other):
            """Compare Job objects according to attribute next_time."""
            return self.next_time - other.next_time

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
        self.callables = set()

        filenames = self.config.enumerate_modules()
        # Coretasks is special. No custom user coretasks.
        this_dir = os.path.dirname(os.path.abspath(__file__))
        filenames['coretasks'] = os.path.join(this_dir, 'coretasks.py')

        modules = []
        error_count = 0
        for name, filename in filenames.iteritems():
            try:
                module = imp.load_source(name, filename)
            except Exception, e:
                error_count = error_count + 1
                stderr("Error loading %s: %s (in bot.py)" % (name, e))
            else:
                try:
                    if hasattr(module, 'setup'):
                        module.setup(self)
                    self.register(vars(module))
                    modules.append(name)
                except Exception, e:
                    error_count = error_count + 1
                    stderr("Error in %s setup procedure: %s (in bot.py)"
                           % (name, e))

        if modules:
            stderr('\n\nRegistered %d modules,' % (len(modules) - 1))
            stderr('%d modules failed to load\n\n' % error_count)
        else:
            stderr("Warning: Couldn't find any modules")

        self.bind_commands()

    @staticmethod
    def is_callable(obj):
        """Return true if object is a willie callable.

        Object must be both be callable and have hashable. Furthermore, it must
        have either "commands", "rule" or "interval" as attributes to mark it
        as a willie callable.
        """
        if not callable(obj):
            # Check is to help distinguish between willie callables and objects
            # which just happen to have parameter commands or rule.
            return False
        if (hasattr(obj, 'commands') or
                hasattr(obj, 'rule') or
                hasattr(obj, 'interval')):
            return True
        return False

    def register(self, variables):
        """
        With the ``__dict__`` attribute from a Willie module, update or add the
        trigger commands and rules to allow the function to be triggered.
        """
        # This is used by reload.py, hence it being methodised
        for obj in variables.itervalues():
            if self.is_callable(obj):
                self.callables.add(obj)

    def unregister(self, variables):
        """Unregister all willie callables in variables, and their bindings.

        When unloading a module, this ensures that the unloaded modules will
        not get called and that the objects can be garbage collected. Objects
        that have not been registered are ignored.

        Args:
        variables -- A list of callable objects from a willie module.
        """
        def remove_func(func, commands):
            """Remove all traces of func from commands."""
            for func_list in commands.itervalues():
                if func in func_list:
                    func_list.remove(func)
        
        for obj in variables.itervalues():
            if not self.is_callable(obj):
                continue
            if obj in self.callables:
                self.callables.remove(obj)
                for commands in self.commands.itervalues():
                    remove_func(obj, commands)

    def bind_commands(self):
        self.commands = {'high': {}, 'medium': {}, 'low': {}}
        self.scheduler.clear_jobs()

        def bind(self, priority, regexp, func):
            # Function name is no longer used for anything, as far as I know,
            # but we're going to keep it around anyway.
            if not hasattr(func, 'name'):
                func.name = func.__name__
            # At least for now, only account for the first command listed.
            if func.__doc__ and hasattr(func, 'commands') and func.commands[0]:
                if hasattr(func, 'example'):
                    if isinstance(func.example, basestring):
                        # Support old modules that add the attribute directly.
                        example = func.example
                    else:
                        # The new format is a list of dicts.
                        example = func.example[0]["example"]
                    example = example.replace('$nickname', str(self.nick))
                else:
                    example = None
                self.doc[func.commands[0]] = (func.__doc__, example)
            self.commands[priority].setdefault(regexp, []).append(func)

        def sub(pattern, self=self):
            # These replacements have significant order
            pattern = pattern.replace('$nickname', r'%s' % re.escape(self.nick))
            return pattern.replace('$nick', r'%s[,:] +' % re.escape(self.nick))

        for func in self.callables:
            if not hasattr(func, 'priority'):
                func.priority = 'medium'

            if not hasattr(func, 'thread'):
                func.thread = True

            if not hasattr(func, 'event'):
                func.event = 'PRIVMSG'
            else:
                func.event = func.event.upper()

            if not hasattr(func, 'rate'):
                if hasattr(func, 'commands'):
                    func.rate = 0
                else:
                    func.rate = 0

            if hasattr(func, 'rule'):
                rules = func.rule
                if isinstance(rules, basestring):
                    rules = [func.rule]

                if isinstance(rules, list):
                    for rule in rules:
                        pattern = sub(rule)
                        flags = re.IGNORECASE
                        if rule.find("\n") != -1:
                            flags |= re.VERBOSE
                        regexp = re.compile(pattern, flags)
                        bind(self, func.priority, regexp, func)

                elif isinstance(func.rule, tuple):
                    # 1) e.g. ('$nick', '(.*)')
                    if len(func.rule) == 2 and isinstance(func.rule[0], str):
                        prefix, pattern = func.rule
                        prefix = sub(prefix)
                        regexp = re.compile(prefix + pattern, re.I)
                        bind(self, func.priority, regexp, func)

                    # 2) e.g. (['p', 'q'], '(.*)')
                    elif len(func.rule) == 2 and isinstance(func.rule[0], list):
                        prefix = self.config.prefix
                        commands, pattern = func.rule
                        for command in commands:
                            command = r'(%s)\b(?: +(?:%s))?' % (command, pattern)
                            regexp = re.compile(prefix + command, re.I)
                            bind(self, func.priority, regexp, func)

                    # 3) e.g. ('$nick', ['p', 'q'], '(.*)')
                    elif len(func.rule) == 3:
                        prefix, commands, pattern = func.rule
                        prefix = sub(prefix)
                        for command in commands:
                            command = r'(%s) +' % command
                            regexp = re.compile(prefix + command + pattern, re.I)
                            bind(self, func.priority, regexp, func)

            if hasattr(func, 'commands'):
                for command in func.commands:
                    prefix = self.config.prefix
                    regexp = get_command_regexp(prefix, command)
                    bind(self, func.priority, regexp, func)

            if hasattr(func, 'interval'):
                for interval in func.interval:
                    job = Willie.Job(interval, func)
                    self.scheduler.add_job(job)

    class WillieWrapper(object):
        def __init__(self, willie, origin):
            self.bot = willie
            self.origin = origin

        def say(self, string, max_messages=1):
            self.bot.msg(self.origin.sender, string, max_messages=1)

        def reply(self, string):
            if isinstance(string, str):
                string = string.decode('utf8')
            self.bot.msg(self.origin.sender, u'%s: %s' % (self.origin.nick, string))

        def action(self, string, recipient=None):
            if recipient is None:
                recipient = self.origin.sender
            self.bot.msg(recipient, '\001ACTION %s\001' % string)

        def __getattr__(self, attr):
            return getattr(self.bot, attr)

    class Trigger(unicode):
        def __new__(cls, text, origin, bytes, match, event, args, self):
            s = unicode.__new__(cls, text)
            s.sender = origin.sender
            """
            The channel (or nick, in a private message) from which the
            message was sent.
            """
            s.hostmask = origin.hostmask
            """
            Hostmask of the person who sent the message in the form
            <nick>!<user>@<host>
            """
            s.user = origin.user
            """Local username of the person who sent the message"""
            s.nick = origin.nick
            """The ``Nick`` of the person who sent the message."""
            s.event = event
            """
            The IRC event (e.g. ``PRIVMSG`` or ``MODE``) which triggered the
            message."""
            s.bytes = bytes
            """
            The text which triggered the message. Equivalent to
            ``Trigger.group(0)``.
            """
            s.match = match
            """
            The regular expression ``MatchObject_`` for the triggering line.
            .. _MatchObject: http://docs.python.org/library/re.html#match-objects
            """
            s.group = match.group
            """The ``group`` function of the ``match`` attribute.

            See Python ``re_`` documentation for details."""
            s.groups = match.groups
            """The ``groups`` function of the ``match`` attribute.

            See Python ``re_`` documentation for details."""
            s.args = args
            """
            A tuple containing each of the arguments to an event. These are the
            strings passed between the event name and the colon. For example,
            setting ``mode -m`` on the channel ``#example``, args would be
            ``('#example', '-m')``
            """
            if len(self.config.core.get_list('admins')) > 0:
                s.admin = (origin.nick in
                           [Nick(n) for n in
                            self.config.core.get_list('admins')])
            else:
                s.admin = False

            """
            True if the nick which triggered the command is in Willie's admin
            list as defined in the config file.
            """

            # Support specifying admins by hostnames
            if not s.admin and len(self.config.core.get_list('admins')) > 0:
                for each_admin in self.config.core.get_list('admins'):
                    re_admin = re.compile(each_admin)
                    if re_admin.findall(origin.host):
                        s.admin = True
                    elif '@' in each_admin:
                        temp = each_admin.split('@')
                        re_host = re.compile(temp[1])
                        if re_host.findall(origin.host):
                            s.admin = True
            s.owner = origin.nick + '@' + origin.host == self.config.owner
            if not s.owner:
                s.owner = (origin.nick == Nick(self.config.owner))

            # Bot owner inherits all the admin rights, therefore is considered
            # admin
            s.admin = s.admin or s.owner

            s.host = origin.host
            if s.sender is not s.nick:  # no ops in PM
                s.ops = self.ops.get(s.sender, [])
                """
                List of channel operators in the channel the message was
                recived in
                """
                s.halfplus = self.halfplus.get(s.sender, [])
                """
                List of channel half-operators in the channel the message was
                recived in
                """
                s.isop = (s.nick in s.ops or
                          s.nick in s.halfplus)
                """True if the user is half-op or an op"""
                s.voices = self.voices.get(s.sender, [])
                """
                List of channel operators in the channel the message was
                recived in
                """
                s.isvoice = (s.nick in s.ops or
                             s.nick in s.halfplus or
                             s.nick in s.voices)
                """True if the user is voiced, has op, or has half-op"""
            else:
                s.isop = False
                s.isvoice = False
                s.ops = []
                s.halfplus = []
                s.voices = []
            return s

    def call(self, func, origin, willie, trigger):
        nick = trigger.nick
        if nick in self.times:
            if func in self.times[nick]:
                if not trigger.admin:
                    timediff = time.time() - self.times[nick][func]
                    if timediff < func.rate:
                        self.times[nick][func] = time.time()
                        self.debug('bot.py',
                                   "%s prevented from using %s in %s: %d < %d"
                                   % (trigger.nick, func.__name__,
                                      trigger.sender, timediff, func.rate),
                                   "warning")
                        return
        else:
            fail = self.times[nick] = dict()

        exit_code = None
        try:
            exit_code = func(willie, trigger)
        except Exception, e:
            self.error(origin, trigger)
        if exit_code != module.NOLIMIT:
            self.times[nick][func] = time.time()

    def limit(self, origin, func):
        if origin.sender and origin.sender.startswith('#'):
            if hasattr(self.config, 'limit'):
                limits = self.config.limit.get(origin.sender)
                if limits and (func.__module__ not in limits):
                    return True
        return False

    def dispatch(self, origin, text, args):
        bytes = text
        event = args[0]
        args = args[1:]

        for priority in ('high', 'medium', 'low'):
            items = self.commands[priority].items()
            for regexp, funcs in items:
                for func in funcs:
                    if event != func.event:
                        continue

                    match = regexp.match(text)
                    if match:
                        if self.limit(origin, func):
                            continue

                        willie = self.WillieWrapper(self, origin)
                        trigger = self.Trigger(text, origin, bytes, match,
                                               event, args, self)

                        nick = (trigger.nick).lower()

                        ## blocking ability
                        bad_nicks = self.config.core.get_list('nick_blocks')
                        bad_masks = self.config.core.get_list('host_blocks')

                        if len(bad_masks) > 0:
                            for hostmask in bad_masks:
                                hostmask = hostmask.replace("\n", "")
                                if len(hostmask) < 1:
                                    continue
                                re_temp = re.compile(hostmask)
                                host = origin.host
                                host = host.lower()
                                if re_temp.findall(host) or hostmask in host:
                                    return
                        if len(bad_nicks) > 0:
                            for nick in bad_nicks:
                                nick = nick.replace("\n", "")
                                if len(nick) < 1:
                                    continue
                                re_temp = re.compile(nick)
                                #RFC-lowercasing the regex is impractical. So
                                #we'll just specify to use RFC-lowercase in the
                                #regex, which means we'll have to be in RFC-
                                #lowercase here.
                                if (re_temp.findall(trigger.nick.lower())
                                        or Nick(nick).lower() in trigger.nick.lower()):
                                    return

                        if func.thread:
                            targs = (func, origin, willie, trigger)
                            t = threading.Thread(target=self.call, args=targs)
                            t.start()
                        else:
                            self.call(func, origin, willie, trigger)

    def debug(self, tag, text, level):
        """
        Sends an error to Willie's configured ``debug_target``.
        """
        if not hasattr(self.config, 'verbose') or not self.config.verbose:
            self.config.verbose = 'warning'
        if (not hasattr(self.config, 'debug_target')
                or not (self.config.debug_target == 'stdio'
                        or self.config.debug_target.startswith('#'))):
            debug_target = 'stdio'
        else:
            debug_target = self.config.debug_target
        debug_msg = "[%s] %s" % (tag, text)
        if level == 'verbose':
            if self.config.verbose == 'verbose':
                if (debug_target == 'stdio'):
                    print debug_msg
                else:
                    self.msg(debug_target, debug_msg)
                return True
        elif level == 'warning':
            if (self.config.verbose == 'verbose'
                    or self.config.verbose == 'warning'):
                if (debug_target == 'stdio'):
                    print debug_msg
                else:
                    self.msg(debug_target, debug_msg)
                return True
        elif level == 'always':
            if (debug_target == 'stdio'):
                print debug_msg
            else:
                self.msg(self.config.debug_target, debug_msg)
            return True

        return False

if __name__ == '__main__':
    print __doc__
