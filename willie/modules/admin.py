# coding=utf-8
"""
admin.py - Willie Admin Module
Copyright 2010-2011, Sean B. Palmer (inamidst.com) and Michael Yanovich
(yanovich.net)
Copyright © 2012, Elad Alfassa, <elad@fedoraproject.org>
Copyright 2013, Ari Koivula <ari@koivu.la>

Licensed under the Eiffel Forum License 2.

http://willie.dftba.net
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
    if not trigger.is_privmsg:
        return

    if trigger.admin:
        channel, key = trigger.group(3), trigger.group(4)
        if not channel:
            return
        elif not key:
            bot.join(channel)
        else:
            bot.join(channel, key)


@willie.module.commands('part')
@willie.module.priority('low')
@willie.module.example('.part #example')
def part(bot, trigger):
    """Part the specified channel. This is an admin-only command."""
    # Can only be done in privmsg by an admin
    if not trigger.is_privmsg:
        return
    if not trigger.admin:
        return

    channel, _sep, part_msg = trigger.group(2).partition(' ')
    if part_msg:
        bot.part(channel, part_msg)
    else:
        bot.part(channel)


@willie.module.commands('quit')
@willie.module.priority('low')
def quit(bot, trigger):
    """Quit from the server. This is an owner-only command."""
    # Can only be done in privmsg by the owner
    if not trigger.is_privmsg:
        return
    if not trigger.owner:
        return

    quit_message = trigger.group(2)
    if not quit_message:
        quit_message = 'Quitting on command from %s' % trigger.nick

    bot.quit(quit_message)


@willie.module.commands('msg')
@willie.module.priority('low')
@willie.module.example('.msg #YourPants Does anyone else smell neurotoxin?')
def msg(bot, trigger):
    """
    Send a message to a given channel or nick. Can only be done in privmsg by an
    admin.
    """
    if not trigger.is_privmsg:
        return
    if not trigger.admin:
        return

    channel, _sep, message = trigger.group(2).partition(' ')
    message = message.strip()
    if not channel or not message:
        return

    bot.msg(channel, message)


@willie.module.commands('me')
@willie.module.priority('low')
def me(bot, trigger):
    """
    Send an ACTION (/me) to a given channel or nick. Can only be done in privmsg
    by an admin.
    """
    if not trigger.is_privmsg:
        return
    if not trigger.admin:
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
    if not trigger.admin:
        return
    bot.join(trigger.args[1])


@willie.module.event('KICK')
@willie.module.rule(r'.*')
@willie.module.priority('low')
def hold_ground(bot, trigger):
    """
    This function monitors all kicks across all channels Willie is in. If it
    detects that it is the one kicked it'll automatically join that channel.

    WARNING: This may not be needed and could cause problems if Willie becomes
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
    if not trigger.is_privmsg:
        return
    if not trigger.admin:
        return
    mode = trigger.group(3)
    bot.write(('MODE ', bot.nick + ' ' + mode))


@willie.module.commands('set', 'addto', 'removefrom')
@willie.module.example('.set core.owner Me')
@willie.module.example('.addto core.admins My_Friend')
@willie.module.example('.removefrom core.admins My_ExFriend')
def set_config(bot, trigger):
    """See and modify values of Willie's config object.

    Trigger args:
        arg1 - section and option, in the form "section.option"
        arg2 - value

    If there is no section, section will default to "core".
    If value is None, the option will be deleted.
    """
    if not trigger.is_privmsg:
        bot.reply("This command only works as a private message.")
        return
    if not trigger.admin:
        bot.reply("This command requires admin privileges.")
        return

    # Get section and option from first argument.
    arg1 = trigger.group(3).split('.')
    if len(arg1) == 1:
        section, option = "core", arg1[0]
    elif len(arg1) == 2:
        section, option = arg1
    else:
        bot.reply("Usage: .set section.option value")
        return

    # Set the value of the config option.
    value = trigger.group(4)
    if value:
        command = trigger.group(1)
        if command == 'set':
            # Set the value to one given as argument 2.
            setattr(getattr(bot.config, section), option, value)

        elif command in ('addto', 'removefrom'):
            # Convert this option to a list, and try to add or remove the value.
            vlist = getattr(bot.config, section).get_list(option)
            try:
                vlist.append(value) if command == 'addto' else vlist.remove(value)
                setattr(getattr(bot.config, section), option, vlist)
            except ValueError: # tried to remove value not in list
                pass

    # Display the value of the config option, whether it has been changed or not.
    if not bot.config.has_option(section, option):
        bot.reply("Option {0}.{1} does not exist.".format(section, option))
        return
    # If the option looks like a password, censor it to stop them from being put on log files.
    if option.endswith("password") or option.endswith("pass"):
        value = "(password censored)"
    else:
        value = getattr(getattr(bot.config, section), option)
    bot.reply("{0}.{1} = {2}".format(section, option, value))


@willie.module.commands('save')
@willie.module.example('.save')
def save_config(bot, trigger):
    """Save state of Willie's config object to the configuration file."""
    if not trigger.is_privmsg:
        return
    if not trigger.admin:
        return
    bot.config.save()


if __name__ == '__main__':
    print __doc__.strip()
