# coding=utf-8
"""
reload.py - Sopel Module Reloader Module
Copyright 2008, Sean B. Palmer, inamidst.com
Licensed under the Eiffel Forum License 2.

https://sopel.chat
"""
from __future__ import unicode_literals, absolute_import, print_function, division

import logging
import subprocess

import sopel.module
from sopel import plugins


LOGGER = logging.getLogger(__name__)


def _load(bot, plugin):
    # handle errors while loading (if any)
    try:
        plugin.load()
        if plugin.has_setup():
            plugin.setup(bot)
        plugin.register(bot)
    except Exception as e:
        LOGGER.exception('Error loading %s: %s', plugin.name, e)
        raise


@sopel.module.nickname_commands("reload")
@sopel.module.priority("low")
@sopel.module.thread(False)
@sopel.module.require_admin
def f_reload(bot, trigger):
    """Reloads a module (for use by admins only)."""
    name = trigger.group(2)

    if not name or name == '*' or name.upper() == 'ALL THE THINGS':
        bot.reload_plugins()
        return bot.reply('done')

    if not bot.has_plugin(name):
        return bot.reply('"%s" not loaded, try the `load` command' % name)

    bot.reload_plugin(name)
    plugin_meta = bot.get_plugin_meta(name)
    return bot.reply('done: %s reloaded (%s from %s)' %
                     (name, plugin_meta['type'], plugin_meta['source']))


@sopel.module.nickname_commands('update')
@sopel.module.require_admin
def f_update(bot, trigger):
    """Pulls the latest versions of all modules from Git (for use by admins only)."""
    proc = subprocess.Popen('/usr/bin/git pull',
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, shell=True)
    bot.reply(proc.communicate()[0])

    f_reload(bot, trigger)


@sopel.module.nickname_commands("load")
@sopel.module.priority("low")
@sopel.module.thread(False)
@sopel.module.require_admin
def f_load(bot, trigger):
    """Loads a module (for use by admins only)."""
    name = trigger.group(2)
    if not name:
        return bot.reply('Load what?')

    if bot.has_plugin(name):
        return bot.reply('Plugin already loaded, use reload')

    usable_plugins = plugins.get_usable_plugins(bot.config)
    if name not in usable_plugins:
        bot.reply('Plugin %s not found' % name)
        return

    plugin, is_enabled = usable_plugins[name]
    if not is_enabled:
        bot.reply('Plugin %s is disabled' % name)
        return

    try:
        _load(bot, plugin)
    except Exception as error:
        bot.reply('Could not load plugin %s: %s' % (name, error))
    else:
        meta = bot.get_plugin_meta(name)
        bot.reply('Plugin %s loaded (%s from %s)' %
                  (name, meta['type'], meta['source']))


# Catch private messages
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
