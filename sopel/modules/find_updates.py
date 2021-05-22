# coding=utf-8
"""
find_updates.py - Sopel Update Check Plugin
This is separated from version.py, so that it can be easily overridden by
distribution packagers, and they can check their repositories rather than the
Sopel website.
Copyright 2014, Elsie Powell, embolalia.com
Licensed under the Eiffel Forum License 2.

https://sopel.chat
"""
from __future__ import absolute_import, division, print_function, unicode_literals

import requests

from sopel import (
    __version__ as current_version,
    _version_info,
    plugin,
    tools,
    version_info,
)


wait_time = 24 * 60 * 60  # check once per day
max_failures = 4
version_url = 'https://sopel.chat/latest.json'
stable_message = (
    'A new Sopel version, {}, is available; I am running {}. Please update '
    'me. Full release notes at {}'
)
unstable_message = (
    'A new pre-release version, {}, is available; I am running {}. Please '
    'update me.{}'
)


@plugin.event(tools.events.RPL_LUSERCLIENT)
def startup_version_check(bot, trigger):
    if not bot.memory.get('update_startup_check_run', False):
        bot.memory['update_startup_check_run'] = True
        check_version(bot)


def _check_succeeded(bot):
    bot.memory['update_failures'] = 0


def _check_failed(bot):
    bot.memory['update_failures'] = 1 + bot.memory.get('update_failures', 0)


@plugin.interval(wait_time)
def check_version(bot):
    version = version_info
    success = False

    try:
        r = requests.get(version_url, timeout=(5, 5))
    except requests.exceptions.RequestException:
        _check_failed(bot)
    else:
        success = True

    try:
        if success:
            info = r.json()
    except ValueError:
        # TODO: use JSONDecodeError when dropping Pythons < 3.5
        _check_failed(bot)
        success = False

    if not success:
        if bot.memory.get('update_failures', 0) <= max_failures:
            # not enough failures to worry; silently ignore this one
            return

        # too many failures to ignore; notify owner
        bot.say(
            "[update] I haven't been able to check for updates in a while. "
            "Please verify that {} is working and I can reach it."
            .format(version_url), bot.config.core.owner)
        bot.say(
            "[update] If this issue persists, please alert the Sopel dev team "
            "in #sopel on Libera Chat, or open a GitHub issue: "
            "https://github.com/sopel-irc/sopel/issues",
            bot.config.core.owner)
        return

    _check_succeeded(bot)

    if version.releaselevel == 'final':
        latest = info['version']
        notes = info['release_notes']
        message = stable_message
    else:
        latest = info['unstable']
        notes = info.get('unstable_notes', '')
        if notes:
            notes = ' Full release notes at ' + notes
        message = unstable_message
    latest_version = _version_info(latest)

    if version < latest_version:
        msg = message.format(latest, current_version, notes)
        bot.say('[update] ' + msg, bot.config.core.owner)
