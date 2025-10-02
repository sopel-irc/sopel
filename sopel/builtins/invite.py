"""
invite.py - Sopel Invite Plugin
Copyright © 2016, João Vanzuita, https://github.com/converge
Copyright © 2019, dgw, https://github.com/dgw
Licensed under the Eiffel Forum License 2.

https://sopel.chat
"""
from __future__ import annotations

from sopel import plugin


MIN_PRIV = plugin.HALFOP


def invite_handler(bot, sender, user, channel):
    """Common control logic for invite commands received from anywhere."""
    sender = bot.make_identifier(sender)
    user = bot.make_identifier(user)
    channel = bot.make_identifier(channel)

    # Sanity checks, in case someone reuses this function from outside the plugin
    if not sender.is_nick():
        raise ValueError("Invite sender must be a nick, not a channel.")
    if not user.is_nick():
        raise ValueError("User to invite must be a nick, not a channel.")
    if channel.is_nick():
        raise ValueError("Target channel name must not be a nick.")

    # Sopel must be in the target channel
    if channel not in bot.channels or bot.nick not in bot.channels[channel].privileges:
        bot.reply("I'm not in {}!".format(channel))
        return

    privs = bot.channels[channel].privileges

    # Sopel must have sufficient privileges in the target channel to send invites
    if privs[bot.nick] < MIN_PRIV:
        bot.reply("I don't have permission to invite anyone into {}.".format(channel))
        return

    # The sender must be in the target channel
    if sender not in privs:
        bot.reply("You're not in {}.".format(channel))
        return

    # The sender must have sufficient privileges in the target channel to send invites
    if privs[sender] < MIN_PRIV:
        bot.reply("You don't have permission to invite anyone into {}.".format(channel))
        return

    # Sopel and the sender both passed permission checks.
    # DDDDOOOO IIIITTTT
    bot.write(['INVITE', user, channel])


@plugin.command('invite')
@plugin.example('.invite jenny', user_help=True)
@plugin.example('.invite converge #sopel', user_help=True)
def invite(bot, trigger):
    """
    Invite the given user to the current channel, or (with optional
    second argument) another channel that Sopel is in.
    """
    if not trigger.group(3):
        return bot.reply("Whom should I invite?")
    user = trigger.group(3)

    if trigger.group(4):
        channel = trigger.group(4)
    else:
        if trigger.is_privmsg:
            return bot.say(
                "Channel is required ({}invite user #channel) when inviting from queries."
                .format(bot.settings.core.help_prefix))
        channel = trigger.sender

    try:
        invite_handler(bot, trigger.nick, user, channel)
    except ValueError as err:
        bot.reply('%s' % err)
