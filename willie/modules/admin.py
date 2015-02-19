# coding=utf8
"""
admin.py - Willie Admin Module
Copyright 2010-2011, Sean B. Palmer (inamidst.com) and Michael Yanovich
(yanovich.net)
Copyright © 2012, Elad Alfassa, <elad@fedoraproject.org>
Copyright 2013, Ari Koivula <ari@koivu.la>

Licensed under the Eiffel Forum License 2.

http://willie.dftba.net
"""
from __future__ import unicode_literals

import willie.module


def configure(config):
    """
    | [admin] | example | purpose |
    | -------- | ------- | ------- |
    | hold_ground | False | Auto re-join on kick |
    | auto_accept_invite | False | Auto accept invites from non-admin users |
    """
    config.add_option('admin', 'hold_ground', "Auto re-join on kick")
    config.add_option('admin', 'auto_accept_invite', "Auto Accept All Invites")


@willie.module.require_privmsg
@willie.module.require_admin
@willie.module.commands('join')
@willie.module.priority('low')
@willie.module.example('.join #example or .join #example key')
def join(bot, trigger):
    """Join the specified channel. This is an admin-only command."""
    channel, key = trigger.group(3), trigger.group(4)
    if not channel:
        return
    elif not key:
        bot.join(channel)
    else:
        bot.join(channel, key)


@willie.module.require_privmsg
@willie.module.require_admin
@willie.module.commands('part')
@willie.module.priority('low')
@willie.module.example('.part #example')
def part(bot, trigger):
    """Part the specified channel. This is an admin-only command."""
    channel, _sep, part_msg = trigger.group(2).partition(' ')
    if part_msg:
        bot.part(channel, part_msg)
    else:
        bot.part(channel)


@willie.module.require_privmsg
@willie.module.require_owner
@willie.module.commands('quit')
@willie.module.priority('low')
def quit(bot, trigger):
    """Quit from the server. This is an owner-only command."""
    quit_message = trigger.group(2)
    if not quit_message:
        quit_message = 'Quitting on command from %s' % trigger.nick

    bot.quit(quit_message)


@willie.module.require_privmsg
@willie.module.require_admin
@willie.module.commands('msg')
@willie.module.priority('low')
@willie.module.example('.msg #YourPants Does anyone else smell neurotoxin?')
def msg(bot, trigger):
    """
    Send a message to a given channel or nick. Can only be done in privmsg by an
    admin.
    """
    if trigger.group(2) is None:
        return

    channel, _sep, message = trigger.group(2).partition(' ')
    message = message.strip()
    if not channel or not message:
        return

    bot.msg(channel, message)


@willie.module.require_privmsg
@willie.module.require_admin
@willie.module.commands('me')
@willie.module.priority('low')
def me(bot, trigger):
    """
    Send an ACTION (/me) to a given channel or nick. Can only be done in privmsg
    by an admin.
    """
    if trigger.group(2) is None:
        return

    channel, _sep, action = trigger.group(2).partition(' ')
    action = action.strip()
    if not channel or not action:
        return

    msg = '\x01ACTION %s\x01' % action
    bot.msg(channel, msg)


@willie.module.event('INVITE')
@willie.module.rule('.*')
@willie.module.priority('low')
def invite_join(bot, trigger):
    """
    Join a channel willie is invited to, if the inviter is an admin.
    """
    if trigger.admin or bot.config.admin.auto_accept_invite:
        bot.join(trigger.args[1])
        return


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


@willie.module.require_privmsg
@willie.module.require_admin
@willie.module.commands('mode')
@willie.module.priority('low')
def mode(bot, trigger):
    """Set a user mode on Willie. Can only be done in privmsg by an admin."""
    mode = trigger.group(3)
    bot.write(('MODE ', bot.nick + ' ' + mode))


@willie.module.require_privmsg("This command only works as a private message.")
@willie.module.require_admin("This command requires admin privileges.")
@willie.module.commands('set')
@willie.module.example('.set core.owner Me')
def set_config(bot, trigger):
    """See and modify values of willies config object.

    Trigger args:
        arg1 - section and option, in the form "section.option"
        arg2 - value

    If there is no section, section will default to "core".
    If value is None, the option will be deleted.
    """
    # Get section and option from first argument.
    arg1 = trigger.group(3).split('.')
    if len(arg1) == 1:
        section, option = "core", arg1[0]
    elif len(arg1) == 2:
        section, option = arg1
    else:
        bot.reply("Usage: .set section.option value")
        return

    # Display current value if no value is given.
    value = trigger.group(4)
    if not value:
        if not bot.config.has_option(section, option):
            bot.reply("Option %s.%s does not exist." % (section, option))
            return
        # Except if the option looks like a password. Censor those to stop them
        # from being put on log files.
        if option.endswith("password") or option.endswith("pass"):
            value = "(password censored)"
        else:
            value = getattr(getattr(bot.config, section), option)
        bot.reply("%s.%s = %s" % (section, option, value))
        return

    # Otherwise, set the value to one given as argument 2.
    setattr(getattr(bot.config, section), option, value)


@willie.module.require_privmsg
@willie.module.require_admin
@willie.module.commands('save')
@willie.module.example('.save')
def save_config(bot, trigger):
    """Save state of willies config object to the configuration file."""
    bot.config.save()
