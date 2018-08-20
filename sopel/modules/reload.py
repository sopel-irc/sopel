# coding=utf-8
"""
reload.py - Sopel Module Reloader Module
Copyright 2008, Sean B. Palmer, inamidst.com
Licensed under the Eiffel Forum License 2.

https://sopel.chat
"""
from __future__ import unicode_literals, absolute_import, print_function, division

import os
import subprocess
import sys
import time

import sopel.loader
from sopel.loader import reload_all
import sopel.module
from sopel.tools import get_raising_file_and_line


@sopel.module.nickname_commands("reload")
@sopel.module.priority("low")
@sopel.module.thread(False)
@sopel.module.require_admin()
def f_reload(bot, trigger):
    """Reloads one or more modules, for use by admins only."""
    name = trigger.group(2)

    if not name or name == '*' or name.upper() == 'ALL THE THINGS':
        names = set(bot._modules)
        names.pop('__init__', None)
    else:
        names = [s.strip() for s in name.split()]

    modules = sopel.loader.enumerate_modules(bot.config)
    ok_names = []
    failed_names = []

    for name in names:
        module = bot._modules.get(name)

        if module is None:
            bot.reply('"%s" is not loaded, load it first with `load`.' % name)
            continue

        def reload_check(module, depth):
            # reload everything in the top level or any n-deep submodules
            return (depth < 2 or
                    module.__name__ == name or
                    module.__name__.startswith(name + '.')) \
                and module.__name__ not in sys.builtin_module_names

        def pre_reload(module):
            if module.__name__ == name or module.__name__.startswith(name + '.'):
                bot.unregister_module(module)

                try:
                    del sys.modules[module.__name__]
                except Exception:
                    pass

        try:
            bot.unregister_module(module)
            reload_all(module, pre_reload=pre_reload, reload_if=reload_check)
        except Exception as e:
            filename, lineno = get_raising_file_and_line()
            rel_path = os.path.relpath(filename, os.path.dirname(__file__))
            raising_stmt = "%s:%d" % (rel_path, lineno)
            bot.reply("Error unloading %s: %s (%s)" % (name, e, raising_stmt))
            failed_names.append(name)
            continue

        if name not in modules:
            bot.reply('Module %s not found, was it deleted?' % name)
            continue

        path, type_ = modules[name]

        if load_module(bot, name, path, type_):
            ok_names.append(name)
        else:
            failed_names.append(name)

    if ok_names:
        bot.say('Reloaded: %s' % (', '.join(ok_names)))
    if failed_names:
        bot.say('Failed to reload: %s' % ', '.join(failed_names))


def load_module(bot, name, path, type_):
    try:
        module, mtime = sopel.loader.load_module(name, path, type_)
        bot.register_module(module)
    except Exception as e:
        filename, lineno = get_raising_file_and_line()
        rel_path = os.path.relpath(filename, os.path.dirname(__file__))
        raising_stmt = "%s:%d" % (rel_path, lineno)
        bot.reply("Error loading %s: %s (%s)" % (name, e, raising_stmt))
        return False
    else:
        modified = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(mtime))
        bot.reply('%r (version: %s)' % (module, modified))
        return module


@sopel.module.nickname_commands('update')
@sopel.module.require_admin()
def f_update(bot, trigger):
    """Pulls the latest versions of all modules from Git"""
    proc = subprocess.Popen('/usr/bin/git pull',
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, shell=True)
    bot.reply(proc.communicate()[0])

    f_reload(bot, trigger)


@sopel.module.nickname_commands("load")
@sopel.module.priority("low")
@sopel.module.thread(False)
@sopel.module.require_admin()
def f_load(bot, trigger):
    """Loads one or more modules, for use by admins only."""
    name = trigger.group(2)
    ok_names = []
    failed_names = []
    modules = sopel.loader.enumerate_modules(bot.config)

    if not name:
        return bot.reply('Load what?')

    for name in name.split():
        if name in bot._modules:
            bot.reply("Module '%s' already loaded, use reload" % name)
        elif name not in modules:
            bot.reply("Module '%s' not found." % name)
        else:
            path, type_ = modules[name]

            if load_module(bot, name, path, type_):
                ok_names.append(name)
            else:
                failed_names.append(name)

    if ok_names:
        bot.say('Loaded: %s' % (', '.join(ok_names)))
    if failed_names:
        bot.say('Failed to load: %s' % ', '.join(failed_names))


@sopel.module.nickname_commands("unload")
@sopel.module.priority("low")
@sopel.module.thread(False)
@sopel.module.require_admin()
def f_unload(bot, trigger):
    """"Unloads" one or more modules, for use by admins only."""
    name = trigger.group(2)
    ok_names = []
    failed_names = []

    if not name:
        return bot.reply('Unload what?')
    elif name == bot.config.core.owner:
        return bot.reply('What?')

    for name in name.split():
        module = bot._modules.get(name)
        if module is None:
            bot.reply("Module '%s' is not loaded, try the `load` command" % name)
        else:
            try:
                bot.unregister_module(module)
                ok_names.append(name)
            except Exception as e:
                filename, lineno = get_raising_file_and_line()
                rel_path = os.path.relpath(filename, os.path.dirname(__file__))
                raising_stmt = "%s:%d" % (rel_path, lineno)
                bot.reply("Error unloading %s: %s (%s)" % (name, e, raising_stmt))
                failed_names.append(name)
                continue

    if ok_names:
        bot.say('Unloaded: %s' % (', '.join(ok_names)))
    if failed_names:
        bot.say('Failed to unload: %s' % ', '.join(failed_names))


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


@sopel.module.commands("unload")
@sopel.module.priority("low")
@sopel.module.thread(False)
def pm_f_unload(bot, trigger):
    """Wrapper for allowing delivery of .unload command via PM"""
    if trigger.is_privmsg:
        f_unload(bot, trigger)
