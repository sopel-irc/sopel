# coding=utf-8
"""
announce.py - Sopel Announcement Module
Sends announcements to all channels the bot has joined.
Copyright © 2013, Elad Alfassa, <elad@fedoraproject.org>
Licensed under the Eiffel Forum License 2.

https://sopel.chat
"""
from __future__ import unicode_literals, absolute_import, print_function, division

from sopel.module import commands, example, require_admin


@commands('announce')
@example('.announce Some important message here')
@require_admin('Sorry, I can\'t let you do that', reply=True)
def announce(bot, trigger):
    """Send an announcement to all channels the bot is in"""
    for channel in bot.channels:
        bot.say('[ANNOUNCEMENT] %s' % trigger.group(2), channel)
    bot.reply('Announce complete.')
