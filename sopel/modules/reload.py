# coding=utf-8
"""
reload.py - Sopel Plugin Reloader Plugin
Copyright 2008, Sean B. Palmer, inamidst.com
Licensed under the Eiffel Forum License 2.

https://sopel.chat
"""
from __future__ import absolute_import, division, print_function, unicode_literals

import logging
import subprocess

from sopel import plugin, plugins


LOGGER = logging.getLogger(__name__)
PLUGIN_OUTPUT_PREFIX = '[reload] '


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


@plugin.nickname_command("reload")
@plugin.priority("low")
@plugin.thread(False)
@plugin.require_admin
@plugin.output_prefix(PLUGIN_OUTPUT_PREFIX)
def f_reload(bot, trigger):
    """Reloads a plugin (for use by admins only)."""
    name = trigger.group(2)

    if not name or name == '*' or name.upper() == 'ALL THE THINGS':
        bot.reload_plugins()
        bot.say('done')
        return

    if not bot.has_plugin(name):
        bot.reply('"%s" not loaded; try the `load` command.' % name)
        return

    bot.reload_plugin(name)
    plugin_meta = bot.get_plugin_meta(name)
    bot.say('done: %s reloaded (%s from %s)' % (
        name,
        plugin_meta['type'],
        plugin_meta['source'],
    ))


@plugin.nickname_command('update')
@plugin.require_admin
@plugin.output_prefix(PLUGIN_OUTPUT_PREFIX)
def f_update(bot, trigger):
    """Pulls the latest versions of all plugins from Git (for use by admins only)."""
    proc = subprocess.Popen('/usr/bin/git pull',
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, shell=True)
    bot.reply(proc.communicate()[0])

    f_reload(bot, trigger)


@plugin.nickname_command("load")
@plugin.priority("low")
@plugin.thread(False)
@plugin.require_admin
@plugin.output_prefix(PLUGIN_OUTPUT_PREFIX)
def f_load(bot, trigger):
    """Loads a plugin (for use by admins only)."""
    name = trigger.group(2)
    if not name:
        bot.reply('Load what?')
        return

    if bot.has_plugin(name):
        bot.reply('Plugin already loaded; use the `reload` command.')
        return

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
        bot.say('Plugin %s loaded (%s from %s)' % (
            name,
            meta['type'],
            meta['source'],
        ))


# Catch private messages
@plugin.command("reload")
@plugin.priority("low")
@plugin.thread(False)
@plugin.require_privmsg
@plugin.output_prefix(PLUGIN_OUTPUT_PREFIX)
def pm_f_reload(bot, trigger):
    """Wrapper for allowing delivery of .reload command via PM"""
    f_reload(bot, trigger)


@plugin.command('update')
@plugin.require_privmsg
@plugin.output_prefix(PLUGIN_OUTPUT_PREFIX)
def pm_f_update(bot, trigger):
    """Wrapper for allowing delivery of .update command via PM"""
    f_update(bot, trigger)


@plugin.command("load")
@plugin.priority("low")
@plugin.thread(False)
@plugin.require_privmsg
@plugin.output_prefix(PLUGIN_OUTPUT_PREFIX)
def pm_f_load(bot, trigger):
    """Wrapper for allowing delivery of .load command via PM"""
    f_load(bot, trigger)
