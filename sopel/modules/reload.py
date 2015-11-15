# coding=utf-8
"""
reload.py - Sopel Module Reloader Module
Copyright 2008, Sean B. Palmer, inamidst.com
Licensed under the Eiffel Forum License 2.

http://sopel.chat
"""
from __future__ import unicode_literals, absolute_import, print_function, division

import collections
import sys
import time
from sopel.tools import iteritems
import sopel.loader
import sopel.module
import subprocess


@sopel.module.nickname_commands("reload")
@sopel.module.priority("low")
@sopel.module.thread(False)
def f_reload(bot, trigger):
    """Reloads a module, for use by admins only."""
    if not trigger.admin:
        return

    name = trigger.group(2)
    if name == bot.config.core.owner:
        return bot.reply('What?')

    if not name or name == '*' or name.upper() == 'ALL THE THINGS':
        bot._callables = {
            'high': collections.defaultdict(list),
            'medium': collections.defaultdict(list),
            'low': collections.defaultdict(list)
        }
        bot.command_groups = collections.defaultdict(list)
        bot.setup()
        return bot.reply('done')

    if name not in sys.modules:
        return bot.reply('%s: not loaded, try the `load` command' % name)

    old_module = sys.modules[name]

    old_callables = {}
    for obj_name, obj in iteritems(vars(old_module)):
        bot.unregister(obj)

    # Also remove all references to sopel callables from top level of the
    # module, so that they will not get loaded again if reloading the
    # module does not override them.
    for obj_name in old_callables.keys():
        delattr(old_module, obj_name)

    # Also delete the setup function
    if hasattr(old_module, "setup"):
        delattr(old_module, "setup")

    modules = sopel.loader.enumerate_modules(bot.config)
    path, type_ = modules[name]
    load_module(bot, name, path, type_)


def load_module(bot, name, path, type_):
    module, mtime = sopel.loader.load_module(name, path, type_)
    relevant_parts = sopel.loader.clean_module(module, bot.config)

    bot.register(*relevant_parts)

    # TODO sys.modules[name] = module
    if hasattr(module, 'setup'):
        module.setup(bot)

    modified = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(mtime))

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
    if name == bot.config.core.owner:
        return bot.reply('What?')

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
