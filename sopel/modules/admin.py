# coding=utf-8
"""
admin.py - Sopel Admin Module
Copyright 2010-2011, Sean B. Palmer (inamidst.com) and Michael Yanovich
(yanovich.net)
Copyright © 2012, Elad Alfassa, <elad@fedoraproject.org>
Copyright 2013, Ari Koivula <ari@koivu.la>

Licensed under the Eiffel Forum License 2.

https://sopel.chat
"""
from __future__ import unicode_literals, absolute_import, print_function, division

from sopel.config.types import (
    StaticSection, ValidatedAttribute, FilenameAttribute
)
import sopel.module


class AdminSection(StaticSection):
    hold_ground = ValidatedAttribute('hold_ground', bool, default=False)
    """Auto re-join on kick"""
    auto_accept_invite = ValidatedAttribute('auto_accept_invite', bool,
                                            default=True)


def configure(config):
    """
    | name | example | purpose |
    | ---- | ------- | ------- |
    | hold\\_ground | False | Auto-rejoin the channel after being kicked. |
    | auto\\_accept\\_invite | True | Auto-join channels when invited. |
    """
    config.define_section('admin', AdminSection)
    config.admin.configure_setting('hold_ground',
                                   "Automatically re-join after being kicked?")
    config.admin.configure_setting('auto_accept_invite',
                                   'Automatically join channels when invited?')


def setup(bot):
    bot.config.define_section('admin', AdminSection)


@sopel.module.require_privmsg
@sopel.module.require_admin
@sopel.module.commands('join')
@sopel.module.priority('low')
@sopel.module.example('.join #example or .join #example key')
def join(bot, trigger):
    """Join the specified channel. This is an admin-only command."""
    channel, key = trigger.group(3), trigger.group(4)
    if not channel:
        return
    elif not key:
        bot.join(channel)
    else:
        bot.join(channel, key)


@sopel.module.require_privmsg
@sopel.module.require_admin
@sopel.module.commands('part')
@sopel.module.priority('low')
@sopel.module.example('.part #example')
def part(bot, trigger):
    """Part the specified channel. This is an admin-only command."""
    channel, _sep, part_msg = trigger.group(2).partition(' ')
    if part_msg:
        bot.part(channel, part_msg)
    else:
        bot.part(channel)


@sopel.module.require_privmsg
@sopel.module.require_owner
@sopel.module.commands('quit')
@sopel.module.priority('low')
def quit(bot, trigger):
    """Quit from the server. This is an owner-only command."""
    quit_message = trigger.group(2)
    if not quit_message:
        quit_message = 'Quitting on command from %s' % trigger.nick

    bot.quit(quit_message)


@sopel.module.require_privmsg
@sopel.module.require_admin
@sopel.module.commands('msg')
@sopel.module.priority('low')
@sopel.module.example('.msg #YourPants Does anyone else smell neurotoxin?')
def msg(bot, trigger):
    """
    Send a message to a given channel or nick. Can only be done in privmsg by
    an admin.
    """
    if trigger.group(2) is None:
        return

    channel, _sep, message = trigger.group(2).partition(' ')
    message = message.strip()
    if not channel or not message:
        return

    bot.msg(channel, message)


@sopel.module.require_privmsg
@sopel.module.require_admin
@sopel.module.commands('me')
@sopel.module.priority('low')
def me(bot, trigger):
    """
    Send an ACTION (/me) to a given channel or nick. Can only be done in
    privmsg by an admin.
    """
    if trigger.group(2) is None:
        return

    channel, _sep, action = trigger.group(2).partition(' ')
    action = action.strip()
    if not channel or not action:
        return

    msg = '\x01ACTION %s\x01' % action
    bot.msg(channel, msg)


@sopel.module.event('INVITE')
@sopel.module.rule('.*')
@sopel.module.priority('low')
def invite_join(bot, trigger):
    """
    Join a channel Sopel is invited to, if the inviter is an admin.
    """
    if trigger.admin or bot.config.admin.auto_accept_invite:
        bot.join(trigger.args[1])
        return


@sopel.module.event('KICK')
@sopel.module.rule(r'.*')
@sopel.module.priority('low')
def hold_ground(bot, trigger):
    """
    This function monitors all kicks across all channels Sopel is in. If it
    detects that it is the one kicked it'll automatically join that channel.

    WARNING: This may not be needed and could cause problems if Sopel becomes
    annoying. Please use this with caution.
    """
    if bot.config.admin.hold_ground:
        channel = trigger.sender
        if trigger.args[1] == bot.nick:
            bot.join(channel)


@sopel.module.require_privmsg
@sopel.module.require_admin
@sopel.module.commands('mode')
@sopel.module.priority('low')
def mode(bot, trigger):
    """Set a user mode on Sopel. Can only be done in privmsg by an admin."""
    mode = trigger.group(3)
    bot.write(('MODE ', bot.nick + ' ' + mode))


@sopel.module.require_privmsg("This command only works as a private message.")
@sopel.module.require_admin("This command requires admin privileges.")
@sopel.module.commands('set')
@sopel.module.example('.set core.owner Me')
def set_config(bot, trigger):
    """See and modify values of Sopel's config object.

    Trigger args:
        arg1 - section and option, in the form "section.option"
        arg2 - value

    If there is no section, section will default to "core".
    If value is None, the option will be deleted.
    """
    # Get section and option from first argument.
    arg1 = trigger.group(3).split('.')
    if len(arg1) == 1:
        section_name, option = "core", arg1[0]
    elif len(arg1) == 2:
        section_name, option = arg1
    else:
        bot.reply("Usage: .set section.option value")
        return
    section = getattr(bot.config, section_name)
    static_sec = isinstance(section, StaticSection)

    if static_sec and not hasattr(section, option):
        bot.say('[{}] section has no option {}.'.format(section_name, option))
        return

    delim = trigger.group(2).find(' ')
    # Skip preceding whitespaces, if any.
    while delim > 0 and delim < len(trigger.group(2)) and trigger.group(2)[delim] == ' ':
        delim = delim + 1

    # Display current value if no value is given.
    if delim == -1 or delim == len(trigger.group(2)):
        if not static_sec and bot.config.parser.has_option(section, option):
            bot.reply("Option %s.%s does not exist." % (section_name, option))
            return
        # Except if the option looks like a password. Censor those to stop them
        # from being put on log files.
        if option.endswith("password") or option.endswith("pass"):
            value = "(password censored)"
        else:
            value = getattr(section, option)
        bot.reply("%s.%s = %s" % (section_name, option, value))
        return

    # Otherwise, set the value to one given as argument 2.
    value = trigger.group(2)[delim:]
    if static_sec:
        descriptor = getattr(section.__class__, option)
        try:
            if isinstance(descriptor, FilenameAttribute):
                value = descriptor.parse(bot.config, descriptor, value)
            else:
                value = descriptor.parse(value)
        except ValueError as exc:
            bot.say("Can't set attribute: " + str(exc))
            return
    setattr(section, option, value)


@sopel.module.require_privmsg
@sopel.module.require_admin
@sopel.module.commands('save')
@sopel.module.example('.save')
def save_config(bot, trigger):
    """Save state of Sopel's config object to the configuration file."""
    bot.config.save()
