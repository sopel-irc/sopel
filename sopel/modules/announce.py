# coding=utf-8
"""
announce.py - Sopel Announcement Plugin
Sends announcements to all channels the bot has joined.
Copyright © 2013, Elad Alfassa, <elad@fedoraproject.org>
Licensed under the Eiffel Forum License 2.

https://sopel.chat
"""
from __future__ import absolute_import, division, print_function, unicode_literals

from sopel import plugin


@plugin.command('announce')
@plugin.example('.announce Some important message here')
@plugin.require_admin('Sorry, I can\'t let you do that', reply=True)
@plugin.output_prefix('[ANNOUNCEMENT] ')
def announce(bot, trigger):
    """Send an announcement to all channels the bot is in"""
    for channel in bot.channels:
        bot.say(trigger.group(2), channel)
    bot.reply('Announce complete.')
