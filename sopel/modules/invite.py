# coding=utf-8
"""
invite.py - Sopel invite module
Copyright © 2016, João Vanzuita, https://github.com/converge
Copyright © 2019, dgw, https://github.com/dgw
Licensed under the Eiffel Forum License 2.

https://sopel.chat
"""
from __future__ import unicode_literals, absolute_import, print_function, division

from sopel.module import commands, example, OP


@commands('invite')
@example('.invite jenny')
@example('.invite converge #sopel')
def invite(bot, trigger):
    """
    Invite the given user to the current channel, or (with optional
    second argument) another channel that Sopel is in.
    """
    if not trigger.group(3):
        return bot.reply("Whom should I invite?")
    nick = trigger.group(3)
    if trigger.group(4):
        channel = trigger.group(4)
    else:
        if trigger.is_privmsg:
            return bot.say(
                "Channel is required ({}invite user #channel) when inviting from queries."
                .format(bot.config.core.help_prefix))
        channel = trigger.sender
    try:
        if bot.channels[channel].privileges[bot.nick] < OP:
            return bot.reply("I'm not a channel operator!")
    except KeyError:
        return bot.reply("I'm not in {}!".format(channel))
    bot.write(['INVITE', nick, channel])
