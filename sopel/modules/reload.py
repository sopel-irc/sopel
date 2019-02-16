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

import sopel.module
from sopel import plugins, tools


def _load(bot, plugin):
    # handle loading's errors (if any)
    try:
        plugin.load()
        if plugin.has_setup():
            plugin.setup(bot)
        plugin.register(bot)
    except Exception as e:
        filename, lineno = tools.get_raising_file_and_line()
        rel_path = os.path.relpath(filename, os.path.dirname(__file__))
        raising_stmt = "%s:%d" % (rel_path, lineno)
        tools.stderr(
            "Error loading %s: %s (%s)" % (plugin.name, e, raising_stmt))
        raise


@sopel.module.nickname_commands("reload")
@sopel.module.priority("low")
@sopel.module.thread(False)
def f_reload(bot, trigger):
    """Reloads a module, for use by admins only."""
    if not trigger.admin:
        return

    name = trigger.group(2)

    if not name or name == '*' or name.upper() == 'ALL THE THINGS':
        bot.reload_plugins()
        return bot.reply('done')

    if not bot.has_plugin(name):
        return bot.reply('"%s" not loaded, try the `load` command' % name)

    bot.reload_plugin(name)
    return bot.reply('done: %s reloaded' % name)


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
    if not name:
        return bot.reply('Load what?')

    if bot.has_plugin(name):
        return bot.reply('Module already loaded, use reload')

    for plugin, is_enabled in plugins.enumerate_plugins(bot.config):
        if plugin.name == name:
            if is_enabled:
                try:
                    _load(bot, plugin)
                    bot.reply('Module %s loaded' % name)
                except Exception as error:
                    bot.reply(
                        'Module %s can not be loaded: %s' % (name, error))
            else:
                bot.reply('Module %s is disabled' % name)

            break
    else:
        # Will be triggered only if "break" is not found
        bot.reply('Module %s not found' % name)


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
