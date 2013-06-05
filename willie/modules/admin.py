# coding=utf-8
"""
admin.py - Willie Admin Module
Copyright 2010-2011, Sean B. Palmer (inamidst.com) and Michael Yanovich
(yanovich.net)
Copyright © 2012, Elad Alfassa, <elad@fedoraproject.org>

Licensed under the Eiffel Forum License 2.

http://willie.dfbta.net
"""

import willie.module


def configure(config):
    """
    | [admin] | example | purpose |
    | -------- | ------- | ------- |
    | hold_ground | False | Auto re-join on kick |
    """
    config.add_option('admin', 'hold_ground', "Auto re-join on kick")


@willie.module.commands('join')
@willie.module.priority('low')
@willie.module.example('.join #example or .join #example key')
def join(bot, trigger):
    """Join the specified channel. This is an admin-only command."""
    # Can only be done in privmsg by an admin
    if trigger.sender.startswith('#'):
        return
    if trigger.admin:
        channel, key = trigger.group(3), trigger.group(4)
        if not key:
            bot.join(channel)
        else:
            bot.join(channel, key)


@willie.module.commands('part')
@willie.module.priority('low')
@willie.module.example('.part #example')
def part(bot, trigger):
    """Part the specified channel. This is an admin-only command."""
    # Can only be done in privmsg by an admin
    if trigger.sender.startswith('#'):
        return
    if trigger.admin:
        bot.part(trigger.group(2).strip())


@willie.module.commands('quit')
@willie.module.priority('low')
def quit(bot, trigger):
    """Quit from the server. This is an owner-only command."""
    # Can only be done in privmsg by the owner
    if trigger.sender.startswith('#'):
        return
    if trigger.owner:
        quit_message = 'Quitting on command from %s' % trigger.nick
        if trigger.group(2) is not None:
            quit_message = trigger.group(2)
        bot.quit(quit_message)


@willie.module.commands('msg')
@willie.module.priority('low')
@willie.module.example('.msg #YourPants Does anyone else smell neurotoxin?')
def msg(bot, trigger):
    """
    Send a message to a given channel or nick. Can only be done in privmsg by an
    admin.
    """
    if trigger.sender.startswith('#'):
        return
    a, b = trigger.group(3), trigger.group(4)
    if (not a) or (not b):
        return
    if trigger.admin:
        bot.msg(a, b)


@willie.module.commands('me')
@willie.module.priority('low')
def me(bot, trigger):
    """
    Send an ACTION (/me) to a given channel or nick. Can only be done in privmsg
    by an admin.
    """
    if trigger.sender.startswith('#'):
        return
    if trigger.admin:
        msg = '\x01ACTION %s\x01' % trigger.group(4)
        bot.msg(trigger.group(3), msg)


@willie.module.event('KICK')
@willie.module.rule(r'.*')
@willie.module.priority('low')
def hold_ground(bot, trigger):
    """
    This function monitors all kicks across all channels willie is in. If it
    detects that it is the one kicked it'll automatically join that channel.

    WARNING: This may not be needed and could cause problems if willie becomes
    annoying. Please use this with caution.
    """
    if bot.config.has_section('admin') and bot.config.admin.hold_ground:
        channel = trigger.sender
        if trigger.args[1] == bot.nick:
            bot.join(channel)


@willie.module.commands('mode')
@willie.module.priority('low')
def mode(bot, trigger):
    """Set a user mode on Willie. Can only be done in privmsg by an admin."""
    if trigger.sender.startswith('#'):
        return
    if trigger.admin:
        mode = trigger.group(3)
        bot.write(('MODE ', bot.nick + ' ' + mode))


if __name__ == '__main__':
    print __doc__.strip()
