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
from sopel.tools import iteritems
import sopel.loader
import sopel.module
import subprocess


@sopel.module.commands("reload")
@sopel.module.priority("low")
@sopel.module.thread(False)
@sopel.module.require_admin()
def f_reload(bot, trigger):
    """Reloads a module, for use by admins only."""
    name = trigger.group(2)

    if not name or name == '*' or name.upper() == 'ALL THE THINGS':
        bot._callables = {
            'high': collections.defaultdict(list),
            'medium': collections.defaultdict(list),
            'low': collections.defaultdict(list)
        }
        bot.shutdown_methods.clear()
        bot.scheduler.clear_jobs()
        bot._command_groups = collections.defaultdict(list)
        bot.setup()
        return bot.reply('done')

    if name not in sys.modules:
        return bot.reply('"%s" not loaded, try the `load` command' % name)

    old_module = bot._modules[name]
    bot.unregister_module(old_module)

    modules = sopel.loader.enumerate_modules(bot.config)
    if name not in modules:
        return bot.reply('"%s" not loaded, try the `load` command' % name)
    path, type_ = modules[name]
    load_module(bot, name, path, type_)


def load_module(bot, name, path, type_):
    try:
        module, mtime = sopel.loader.load_module(name, path, type_)
        bot.register_module(module)
    except Exception as e:
        filename, lineno = tools.get_raising_file_and_line()
        rel_path = os.path.relpath(filename, os.path.dirname(__file__))
        raising_stmt = "%s:%d" % (rel_path, lineno)
        return bot.reply("Error loading %s: %s (%s)" % (name, e, raising_stmt))
    else:
        modified = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(mtime))
        bot.reply('%r (version: %s)' % (module, modified))


@sopel.module.commands('update')
@sopel.module.require_admin()
def f_update(bot, trigger):
    """Pulls the latest versions of all modules from Git"""
    proc = subprocess.Popen('/usr/bin/git pull',
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, shell=True)
    bot.reply(proc.communicate()[0])

    f_reload(bot, trigger)


@sopel.module.commands("load")
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

@sopel.module.commands("unload")
@sopel.module.priority("low")
@sopel.module.thread(False)
@sopel.module.require_admin()
def f_unload(bot, trigger):
    """"Unloads" a module, for use by admins only."""
    name = trigger.group(2)
    path = ''
    if name == bot.config.core.owner:
        return bot.reply('What?')

    if name not in bot._modules:
        return bot.reply('%s: not loaded, try the `load` command' % name)

    old_module = bot._modules[name]
    bot.unregister_module(old_module)
    bot.reply('done.')
