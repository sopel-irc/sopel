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
import sys
import os
import re
import threading
import imp
import irc
from db import WillieDB
from tools import stderr, stdout

this_dir = os.path.dirname(os.path.abspath(__file__))
modules_dir = os.path.join(this_dir, 'modules')


def decode(string):
    try:
        text = string.decode('utf-8')
    except UnicodeDecodeError:
        try:
            text = string.decode('iso-8859-1')
        except UnicodeDecodeError:
            text = string.decode('cp1252')
    return text


def enumerate_modules(config):
    filenames = []
    if not hasattr(config, 'enable') or not config.enable:
        for fn in os.listdir(modules_dir):
            if fn.endswith('.py') and not fn.startswith('_'):
                filenames.append(os.path.join(modules_dir, fn))
    else:
        for fn in config.enable.split(','):
            filenames.append(os.path.join(modules_dir, fn + '.py'))

    if hasattr(config, 'extra') and config.extra is not None:
        extra = config.extra.split(',')
        for fn in extra:
            if os.path.isfile(fn):
                filenames.append(fn)
            elif os.path.isdir(fn):
                for n in os.listdir(fn):
                    if n.endswith('.py') and not n.startswith('_'):
                        filenames.append(os.path.join(fn, n))
    return filenames


class Willie(irc.Bot):
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
        A dictionary which maps a tuple of a function name and where it was used
        to the nuber of times it was used there.
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

        self.memory = self.WillieMemory()
        """
        A thread-safe dict for storage of runtime data to be shared between
        modules. See `WillieMemory <#bot.Willie.WillieMemory>`_
        """

        #Set up block lists
        #Default to empty
        if not self.config.has_option('core', 'nick_blocks'):
            self.config.core.nick_blocks = ''
        if not self.config.has_option('core', 'host_blocks'):
            self.config.core.host_blocks = ''
        #Make into lists
        if not isinstance(self.config.core.nick_blocks, list):
            self.config.core.nick_blocks = self.config.core.nick_blocks.split(',')
        if not isinstance(self.config.core.host_blocks, list):
            self.config.core.host_blocks = self.config.core.host_blocks.split(',')
        #Add nicks blocked under old scheme, if present
        if self.config.has_option('core', 'other_bots'):
            nicks = self.config.core.nick_blocks
            bots = self.config.core.other_bots
            if isinstance(bots, basestring):
                bots = bots.split(',')
            nicks.extend(bots)
            self.config.core.nick_blocks = nicks

        self.setup()

    class WillieMemory(dict):
        """
        Availability: 3.1+

        A simple thread-safe dict implementation. In order to prevent exceptions
        when iterating over the values and changing them at the same time from
        different threads, we use a blocking lock on ``__setitem__`` and
        ``contains``.
        """
        def __init__(self, *args):
            dict.__init__(self, *args)
            self.lock = threading.Lock()

        def __setitem__(self, key, value):
            self.lock.acquire()
            result = dict.__setitem__(self, key, value)
            self.lock.release()
            return result

        def contains(self, key):
            """
            Check if a key is in the dict. Use this instead of the ``in``
            keyword if you want to be thread-safe.
            """
            self.lock.acquire()
            result = (key in self)
            self.lock.release()
            return result

    def setup(self):
        stderr("\nWelcome to Willie. Loading modules...\n\n")
        self.variables = {}

        filenames = enumerate_modules(self.config)
        filenames.append(os.path.join(this_dir, 'coretasks.py'))
        self.enumerate_modules = enumerate_modules

        modules = []
        excluded_modules = getattr(self.config, 'exclude', [])
        error_count = 0
        for filename in filenames:
            name = os.path.basename(filename)[:-3]
            if name in excluded_modules:
                continue
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
                    stderr("Error in %s setup procedure: %s (in bot.py)" % (name, e))

        if modules:
            stderr('\n\nRegistered %d modules,' % (len(modules) - 1))
            stderr('%d modules failed to load\n\n' % error_count)
        else:
            stderr("Warning: Couldn't find any modules")

        self.bind_commands()

    def register(self, variables):
        """
        With the ``__dict__`` attribute from a Willie module, update or add the
        trigger commands and rules to allow the function to be triggered.
        """
        # This is used by reload.py, hence it being methodised
        for name, obj in variables.iteritems():
            if hasattr(obj, 'commands') or hasattr(obj, 'rule'):
                self.variables[name] = obj

    def bind_commands(self):
        self.commands = {'high': {}, 'medium': {}, 'low': {}}

        def bind(self, priority, regexp, func):
            # register documentation
            if not hasattr(func, 'name'):
                func.name = func.__name__
            # At least for now, only account for the first command listed.
            if func.__doc__ and hasattr(func, 'commands') and func.commands[0]:
                if hasattr(func, 'example'):
                    example = func.example
                    example = example.replace('$nickname', self.nick)
                else:
                    example = None
                self.doc[func.commands[0]] = (func.__doc__, example)
            self.commands[priority].setdefault(regexp, []).append(func)

        def sub(pattern, self=self):
            # These replacements have significant order
            pattern = pattern.replace('$nickname', r'%s' % re.escape(self.nick))
            return pattern.replace('$nick', r'%s[,:] +' % re.escape(self.nick))

        for name, func in self.variables.iteritems():
            # print name, func
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
                if isinstance(func.rule, str):
                    pattern = sub(func.rule)
                    regexp = re.compile(pattern, re.I)
                    bind(self, func.priority, regexp, func)

                if isinstance(func.rule, tuple):
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
                    template = r'^%s(%s)(?: +(.*))?$'
                    pattern = template % (self.config.prefix, command)
                    regexp = re.compile(pattern, re.I)
                    bind(self, func.priority, regexp, func)

    class WillieWrapper(object):
        def __init__(self, willie, origin):
            self.bot = willie
            self.origin = origin

        def say(self, string):
            self.bot.msg(self.origin.sender, string)

        def reply(self, string):
            self.bot.msg(self.origin.sender, self.origin.nick + ': ' + string)

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
            s.nick = origin.nick
            """The nick of the person who sent the message."""
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
            s.admin = ((origin.nick in self.config.admins.split(','))
                       or origin.nick.lower() == self.config.owner.lower())
            """
            True if the nick which triggered the command is in Willie's admin
            list as defined in the config file.
            """

            if not s.admin:
                for each_admin in self.config.admins.split(','):
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
                s.owner = (origin.nick == self.config.owner)

            s.host = origin.host
            if s.sender is not s.nick:  # no ops in PM
                try:
                    s.ops = self.ops[s.sender]
                except:
                    s.ops = []
                """
                List of channel operators in the channel the message was
                recived in
                """
                try:
                    s.halfplus = self.halfplus[s.sender]
                except:
                    s.halfplus = []
                """
                List of channel half-operators in the channel the message was
                recived in
                """
                s.isop = (s.nick.lower() in s.ops or s.nick.lower() in s.halfplus)
                """True if the user is half-op or an op"""
            else:
                s.isop = False
                s.ops = []
                s.halfplus = []
            return s

    def call(self, func, origin, willie, trigger):
        nick = (trigger.nick).lower()
        if nick in self.times:
            if func in self.times[nick]:
                if not trigger.admin:
                    timediff = time.time() - self.times[nick][func]
                    if timediff < func.rate:
                        self.times[nick][func] = time.time()
                        self.debug('bot.py', "%s prevented from using %s in %s: %d < %d" % (trigger.nick, func.__name__, trigger.sender, timediff, func.rate), "warning")
                        return
        else:
            self.times[nick] = dict()
        self.times[nick][func] = time.time()

        try:
            func(willie, trigger)
        except Exception, e:
            self.error(origin, trigger)

    def limit(self, origin, func):
        if origin.sender and origin.sender.startswith('#'):
            if hasattr(self.config, 'limit'):
                limits = self.config.limit.get(origin.sender)
                if limits and (func.__module__ not in limits):
                    return True
        return False

    def dispatch(self, origin, text, args):
        bytes = text
        text = decode(text)
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
                        trigger = self.Trigger(text, origin, bytes, match, event, args, self)

                        if self.config.core.other_bots is not None:
                            if trigger.nick in self.config.other_bots.split(','):
                                continue

                        nick = (trigger.nick).lower()

                        ## blocking ability
                        bad_nicks = self.config.core.nick_blocks
                        bad_masks = self.config.core.host_blocks

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
                                if (re_temp.findall(trigger.nick)
                                    or nick in trigger.nick):
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
            if self.config.verbose == 'verbose' or self.config.verbose == 'warning':
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
