# coding=utf8
"""
reload.py - Willie Module Reloader Module
Copyright 2008, Sean B. Palmer, inamidst.com
Licensed under the Eiffel Forum License 2.

http://willie.dftba.net
"""
from __future__ import unicode_literals

import sys
import os.path
import time
import imp
from willie.tools import iteritems
import willie.module
import subprocess


@willie.module.nickname_commands("reload")
@willie.module.priority("low")
@willie.module.thread(False)
def f_reload(bot, trigger):
    """Reloads a module, for use by admins only."""
    if not trigger.admin:
        return

    name = trigger.group(2)
    if name == bot.config.owner:
        return bot.reply('What?')

    if not name or name == '*' or name.upper() == 'ALL THE THINGS':
        bot.callables = None
        bot.commands = None
        bot.setup()
        return bot.reply('done')

    if name not in sys.modules:
        return bot.reply('%s: not loaded, try the `load` command' % name)

    old_module = sys.modules[name]

    old_callables = {}
    for obj_name, obj in iteritems(vars(old_module)):
        if bot.is_callable(obj) or bot.is_shutdown(obj):
            old_callables[obj_name] = obj

    bot.unregister(old_callables)
    # Also remove all references to willie callables from top level of the
    # module, so that they will not get loaded again if reloading the
    # module does not override them.
    for obj_name in old_callables.keys():
        delattr(old_module, obj_name)

    # Also delete the setup function
    if hasattr(old_module, "setup"):
        delattr(old_module, "setup")

    # Thanks to moot for prodding me on this
    path = old_module.__file__
    if path.endswith('.pyc') or path.endswith('.pyo'):
        path = path[:-1]
    if not os.path.isfile(path):
        return bot.reply('Found %s, but not the source file' % name)

    module = imp.load_source(name, path)
    sys.modules[name] = module
    if hasattr(module, 'setup'):
        module.setup(bot)

    mtime = os.path.getmtime(module.__file__)
    modified = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(mtime))

    bot.register(vars(module))
    bot.bind_commands()

    bot.reply('%r (version: %s)' % (module, modified))


@willie.module.nickname_commands('update')
def f_update(bot, trigger):
    if not trigger.admin:
        return

    """Pulls the latest versions of all modules from Git"""
    proc = subprocess.Popen('/usr/bin/git pull',
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, shell=True)
    bot.reply(proc.communicate()[0])

    f_reload(bot, trigger)


@willie.module.nickname_commands("load")
@willie.module.priority("low")
@willie.module.thread(False)
def f_load(bot, trigger):
    """Loads a module, for use by admins only."""
    if not trigger.admin:
        return

    module_name = trigger.group(2)
    path = ''
    if module_name == bot.config.owner:
        return bot.reply('What?')

    if module_name in sys.modules:
        return bot.reply('Module already loaded, use reload')

    mods = bot.config.enumerate_modules()
    for name in mods:
        if name == trigger.group(2):
            path = mods[name]
    if not os.path.isfile(path):
        return bot.reply('Module %s not found' % module_name)

    module = imp.load_source(module_name, path)
    mtime = os.path.getmtime(module.__file__)
    modified = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(mtime))
    if hasattr(module, 'setup'):
        module.setup(bot)
    bot.register(vars(module))
    bot.bind_commands()

    bot.reply('%r (version: %s)' % (module, modified))


# Catch PM based messages
@willie.module.commands("reload")
@willie.module.priority("low")
@willie.module.thread(False)
def pm_f_reload(bot, trigger):
    """Wrapper for allowing delivery of .reload command via PM"""
    if trigger.is_privmsg:
        f_reload(bot, trigger)


@willie.module.commands('update')
def pm_f_update(bot, trigger):
    """Wrapper for allowing delivery of .update command via PM"""
    if trigger.is_privmsg:
        f_update(bot, trigger)


@willie.module.commands("load")
@willie.module.priority("low")
@willie.module.thread(False)
def pm_f_load(bot, trigger):
    """Wrapper for allowing delivery of .load command via PM"""
    if trigger.is_privmsg:
        f_load(bot, trigger)
