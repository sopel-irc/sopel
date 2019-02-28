# coding=utf-8
"""
reload.py - Sopel Module Reloader Module
Copyright 2008, Sean B. Palmer, inamidst.com
Licensed under the Eiffel Forum License 2.

https://sopel.chat
"""
from __future__ import unicode_literals, absolute_import, print_function, division

import collections
import sys
import time
from sopel.tools import stderr, iteritems
import sopel.loader
import sopel.module
import subprocess

try:
    from importlib import reload
except ImportError:
    try:
        from imp import reload
    except ImportError:
        pass  # fallback to builtin if neither module is available


@sopel.module.nickname_commands("reload")
@sopel.module.priority("low")
@sopel.module.thread(False)
def f_reload(bot, trigger):
    """Reloads a module, for use by admins only."""
    if not trigger.admin:
        return

    name = trigger.group(2)

    if not name or name == '*' or name.upper() == 'ALL THE THINGS':
        bot._callables = {
            'high': collections.defaultdict(list),
            'medium': collections.defaultdict(list),
            'low': collections.defaultdict(list)
        }
        bot._command_groups = collections.defaultdict(list)

        for m in sopel.loader.enumerate_modules(bot.config):
            reload_module_tree(bot, m, silent=True)

        return bot.reply('done')

    if (name not in sys.modules and name not in sopel.loader.enumerate_modules(bot.config)):
        return bot.reply('"%s" not loaded, try the `load` command' % name)

    reload_module_tree(bot, name)


def reload_module_tree(bot, name, seen=None, silent=False):
    from types import ModuleType

    old_module = sys.modules[name]

    if seen is None:
        seen = {}
    if name not in seen:
        seen[name] = []

    old_callables = {}
    for obj_name, obj in iteritems(vars(old_module)):
        if callable(obj):
            if (getattr(obj, '__name__', None) == 'shutdown' and
                        obj in bot.shutdown_methods):
                # If this is a shutdown method, call it first.
                try:
                    stderr(
                        "calling %s.%s" % (
                            obj.__module__, obj.__name__,
                        )
                    )
                    obj(bot)
                except Exception as e:
                    stderr(
                        "Error calling shutdown method for module %s:%s" % (
                            obj.__module__, e
                        )
                    )
            bot.unregister(obj)
        elif (type(obj) is ModuleType and
              obj.__name__.startswith(name + '.') and
              obj.__name__ not in sys.builtin_module_names):
            # recurse into submodules, see issue 1056
            if obj not in seen[name]:
                seen[name].append(obj)
                reload(obj)
                reload_module_tree(bot, obj.__name__, seen, silent)

    modules = sopel.loader.enumerate_modules(bot.config)
    if name not in modules:
        return  # Only reload the top-level module, once recursion is finished

    # Also remove all references to sopel callables from top level of the
    # module, so that they will not get loaded again if reloading the
    # module does not override them.
    for obj_name in old_callables.keys():
        delattr(old_module, obj_name)

    # Also delete the setup function
    # Sub-modules shouldn't have setup functions, so do after the recursion check
    if hasattr(old_module, "setup"):
        delattr(old_module, "setup")

    path, type_ = modules[name]
    load_module(bot, name, path, type_, silent)


def load_module(bot, name, path, type_, silent=False):
    module, mtime = sopel.loader.load_module(name, path, type_)
    relevant_parts = sopel.loader.clean_module(module, bot.config)

    bot.register(*relevant_parts)

    # TODO sys.modules[name] = module
    if hasattr(module, 'setup'):
        module.setup(bot)

    modified = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(mtime))

    if not silent:
        bot.reply('%r (version: %s)' % (module, modified))


@sopel.module.nickname_commands('update')
def f_update(bot, trigger):
    if not trigger.admin:
        return

    """Pulls the latest versions of all modules from Git"""
    proc = subprocess.Popen('/usr/bin/git pull',
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, shell=True)
    bot.reply(proc.communicate()[0])

    f_reload(bot, trigger)


@sopel.module.nickname_commands("load")
@sopel.module.priority("low")
@sopel.module.thread(False)
def f_load(bot, trigger):
    """Loads a module, for use by admins only."""
    if not trigger.admin:
        return

    name = trigger.group(2)
    path = ''
    if not name:
        return bot.reply('Load what?')

    if name in sys.modules:
        return bot.reply('Module already loaded, use reload')

    mods = sopel.loader.enumerate_modules(bot.config)
    if name not in mods:
        return bot.reply('Module %s not found' % name)
    path, type_ = mods[name]
    load_module(bot, name, path, type_)


# Catch PM based messages
@sopel.module.commands("reload")
@sopel.module.priority("low")
@sopel.module.thread(False)
def pm_f_reload(bot, trigger):
    """Wrapper for allowing delivery of .reload command via PM"""
    if trigger.is_privmsg:
        f_reload(bot, trigger)


@sopel.module.commands('update')
def pm_f_update(bot, trigger):
    """Wrapper for allowing delivery of .update command via PM"""
    if trigger.is_privmsg:
        f_update(bot, trigger)


@sopel.module.commands("load")
@sopel.module.priority("low")
@sopel.module.thread(False)
def pm_f_load(bot, trigger):
    """Wrapper for allowing delivery of .load command via PM"""
    if trigger.is_privmsg:
        f_load(bot, trigger)
