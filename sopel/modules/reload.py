# coding=utf-8
"""
reload.py - Sopel Module Reloader Module
Copyright 2008, Sean B. Palmer, inamidst.com
Licensed under the Eiffel Forum License 2.

https://sopel.chat
"""
from __future__ import unicode_literals, absolute_import, print_function, division

import time
from sopel.tools import get_raising_file_and_line
import sopel.loader
import sopel.module
import subprocess
import os


@sopel.module.nickname_commands("reload")
@sopel.module.priority("low")
@sopel.module.thread(False)
@sopel.module.require_admin()
def f_reload(bot, trigger):
    """Reloads a module, for use by admins only."""
    name = trigger.group(2)

    if not name or name == '*' or name.upper() == 'ALL THE THINGS':
        modules = sopel.loader.enumerate_modules(bot.config)
        names = []
        ok_names = []
        failed_names = []

        for name, module in bot._modules.items():
            names.append(name)
            try:
                bot.unregister_module(module)
            except Exception:
                failed_names.append(name)
                continue

            if name not in modules:
                failed_names.append(name)
                continue

            path, type_ = modules[name]
            load_module(bot, name, path, type_)
            ok_names.append(name)

        return bot.say('Reloaded: %s\nFailed to reload: %s'
                       % (','.join(l) for l in (ok_names, failed_names)))
    else:
        if name not in bot._modules:
            return bot.reply('"%s" not loaded, try the `load` command' % name)

        old_module = bot._modules[name]
        bot.unregister_module(old_module)

        modules = sopel.loader.enumerate_modules(bot.config)
        if name not in modules:
            return bot.reply('Module %s not found, was it deleted?' % name)
        path, type_ = modules[name]
        load_module(bot, name, path, type_)


def load_module(bot, name, path, type_):
    try:
        module, mtime = sopel.loader.load_module(name, path, type_)
        bot.register_module(module)
    except Exception as e:
        filename, lineno = get_raising_file_and_line()
        rel_path = os.path.relpath(filename, os.path.dirname(__file__))
        raising_stmt = "%s:%d" % (rel_path, lineno)
        return bot.reply("Error loading %s: %s (%s)" % (name, e, raising_stmt))
    else:
        modified = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(mtime))
        bot.reply('%r (version: %s)' % (module, modified))


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
    """Loads a module, for use by admins only."""
    name = trigger.group(2)
    path = ''
    if not name:
        return bot.reply('Load what?')

    if name in bot._modules:
        return bot.reply('Module already loaded, use reload')

    mods = sopel.loader.enumerate_modules(bot.config)
    if name not in mods:
        return bot.reply('Module %s not found' % name)
    path, type_ = mods[name]
    load_module(bot, name, path, type_)


@sopel.module.nickname_commands("unload")
@sopel.module.priority("low")
@sopel.module.thread(False)
@sopel.module.require_admin()
def f_unload(bot, trigger):
    """"Unloads" a module, for use by admins only."""
    name = trigger.group(2)
    if name == bot.config.core.owner:
        return bot.reply('What?')

    if name not in bot._modules:
        return bot.reply('%s: not loaded, try the `load` command' % name)

    old_module = bot._modules[name]
    bot.unregister_module(old_module)
    bot.reply('done.')


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
