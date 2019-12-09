# coding=utf-8
"""
find_updates.py - Sopel Update Check Module
This is separated from version.py, so that it can be easily overridden by
distribution packagers, and they can check their repositories rather than the
Sopel website.
Copyright 2014, Elsie Powell, embolalia.com
Licensed under the Eiffel Forum License 2.

https://sopel.chat
"""
from __future__ import unicode_literals, absolute_import, print_function, division

import requests

import sopel
import sopel.module
import sopel.tools


wait_time = 24 * 60 * 60  # check once per day
startup_check_run = False
version_url = 'https://sopel.chat/latest.json'
message = (
    'A new Sopel version, {}, is available. I am running {}. Please update '
    'me. Full release notes at {}'
)
unstable_message = (
    'A new pre-release version, {}, is available. I am running {}. Please '
    'update me. {}'
)


@sopel.module.event(sopel.tools.events.RPL_LUSERCLIENT)
def startup_version_check(bot, trigger):
    global startup_check_run
    if not startup_check_run:
        startup_check_run = True
        check_version(bot)


def _check_succeeded(bot):
    bot.memory['update_failures'] = 0


def _check_failed(bot):
    bot.memory['update_failures'] = 1 + bot.memory.get('update_failures', 0)


@sopel.module.interval(wait_time)
def check_version(bot):
    version = sopel.version_info
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

    if not success and bot.memory.get('update_failures', 0) > 4:
        bot.say("I haven't been able to check for updates in a while. "
                "Please verify that {} is working and I can reach it."
                .format(version_url), bot.config.core.owner)
        bot.say("If this issue persists, please alert the Sopel dev team in "
                "#sopel on freenode, or open a GitHub issue: "
                "https://github.com/sopel-irc/sopel/issues",
                bot.config.core.owner)
        return

    _check_succeeded(bot)

    if version.releaselevel == 'final':
        latest = info['version']
        notes = info['release_notes']
    else:
        latest = info['unstable']
        notes = info.get('unstable_notes', '')
        if notes:
            notes = 'Full release notes at ' + notes
    latest_version = sopel._version_info(latest)
    msg = message.format(latest, sopel.__version__, notes)

    if version < latest_version:
        bot.say(msg, bot.config.core.owner)
