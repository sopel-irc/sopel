# coding=utf-8
"""
invite.py - Sopel invite module
Copyright © 2016, João Vanzuita, https://github.com/converge
Licensed under the Eiffel Forum License 2.

http://sopel.chat
"""
from __future__ import unicode_literals, absolute_import, print_function, division

from sopel.module import commands, example, OP

@commands('invite')
@example('.invite converge #sopel')
def invite(bot, trigger):
    if bot.privileges[trigger.sender][bot.nick] < OP:
        return bot.reply("I'm not a channel operator!")
    if not trigger.group(3) or not trigger.group(4):
        return bot.reply("Usage: .invite user #channel (the bot must be operator and in the invited channel)")
    bot.write(['INVITE', trigger.group(3), trigger.group(4)])
