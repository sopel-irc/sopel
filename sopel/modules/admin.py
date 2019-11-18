# coding=utf-8
"""
admin.py - Sopel Admin Module
Copyright 2010-2011, Sean B. Palmer (inamidst.com) and Michael Yanovich
(yanovich.net)
Copyright © 2012, Elad Alfassa, <elad@fedoraproject.org>
Copyright 2013, Ari Koivula <ari@koivu.la>
Copyright 2019, Florian Strzelecki, https://github.com/Exirel
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
    """Auto-join channels when invited"""


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


class InvalidSection(Exception):
    def __init__(self, section):
        super(InvalidSection, self).__init__(self, 'Section [{}] does not exist.'.format(section))
        self.section = section


class InvalidSectionOption(Exception):
    def __init__(self, section, option):
        super(InvalidSectionOption, self).__init__(self, 'Section [{}] does not have option \'{}\'.'.format(section, option))
        self.section = section
        self.option = option


def _get_config_channels(channels):
    """List"""
    for channel_info in channels:
        if ' ' in channel_info:
            yield channel_info.split(' ', 1)
        else:
            yield (channel_info, None)


def _set_config_channels(bot, channels):
    bot.config.core.channels = [
        ' '.join([part for part in items if part])
        for items in channels.items()
    ]
    bot.config.save()


def _join(bot, channel, key=None, save=True):
    if not channel:
        return

    if not key:
        bot.join(channel)
    else:
        bot.join(channel, key)

    if save:
        channels = dict(_get_config_channels(bot.config.core.channels))
        # save only if channel is new or key has been changed
        if channel not in channels or channels[channel] != key:
            channels[channel] = key
            _set_config_channels(bot, channels)


def _part(bot, channel, msg=None, save=True):
    bot.part(channel, msg or None)

    if save:
        channels = dict(_get_config_channels(bot.config.core.channels))
        if channel in channels:
            del channels[channel]
            _set_config_channels(bot, channels)


@sopel.module.require_privmsg
@sopel.module.require_admin
@sopel.module.commands('join')
@sopel.module.priority('low')
@sopel.module.example('.join #example key', user_help=True)
@sopel.module.example('.join #example', user_help=True)
def join(bot, trigger):
    """Join the specified channel. This is an admin-only command."""
    channel, key = trigger.group(3), trigger.group(4)
    _join(bot, channel, key)


@sopel.module.require_privmsg
@sopel.module.require_admin
@sopel.module.commands('tmpjoin')
@sopel.module.priority('low')
@sopel.module.example('.tmpjoin #example key', user_help=True)
@sopel.module.example('.tmpjoin #example', user_help=True)
def temporary_join(bot, trigger):
    """Like ``join``, without saving. This is an admin-only command.

    Unlike the ``join`` command, ``tmpjoin`` won't remember the channel upon
    restarting the bot.
    """
    channel, key = trigger.group(3), trigger.group(4)
    _join(bot, channel, key, save=False)


@sopel.module.require_privmsg
@sopel.module.require_admin
@sopel.module.commands('part')
@sopel.module.priority('low')
@sopel.module.example('.part #example')
def part(bot, trigger):
    """Part the specified channel. This is an admin-only command."""
    channel, _sep, part_msg = trigger.group(2).partition(' ')
    _part(bot, channel, part_msg)


@sopel.module.require_privmsg
@sopel.module.require_admin
@sopel.module.commands('tmppart')
@sopel.module.priority('low')
@sopel.module.example('.tmppart #example')
def temporary_part(bot, trigger):
    """Like ``part``, without saving. This is an admin-only command.

    Unlike the ``part`` command, ``tmppart`` will rejoin the channel upon
    restarting the bot.
    """
    channel, _sep, part_msg = trigger.group(2).partition(' ')
    _part(bot, channel, part_msg, save=False)


@sopel.module.require_privmsg
@sopel.module.require_owner
@sopel.module.commands('restart')
@sopel.module.priority('low')
def restart(bot, trigger):
    """Restart the bot. This is an owner-only command."""
    quit_message = trigger.group(2)
    if not quit_message:
        quit_message = 'Restart on command from %s' % trigger.nick

    bot.restart(quit_message)


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
@sopel.module.commands('say', 'msg')
@sopel.module.priority('low')
@sopel.module.example('.say #YourPants Does anyone else smell neurotoxin?')
def say(bot, trigger):
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

    bot.say(message, channel)


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

    bot.action(action, channel)


@sopel.module.event('INVITE')
@sopel.module.priority('low')
def invite_join(bot, trigger):
    """Join a channel Sopel is invited to, if the inviter is an admin."""
    if trigger.admin or bot.config.admin.auto_accept_invite:
        bot.join(trigger.args[1])
        return


@sopel.module.event('KICK')
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
    bot.write(('MODE', bot.nick + ' ' + mode))


def parse_section_option_value(config, trigger):
    """Parse trigger for set/unset to get relevant config elements.

    :param config: Sopel's config
    :param trigger: IRC line trigger
    :return: A tuple with ``(section, section_name, static_sec, option, value)``
    :raises InvalidSection: section does not exist
    :raises InvalidSectionOption: option does not exist for section

    The ``value`` is optional and can be returned as ``None`` if omitted from command.
    """
    match = trigger.group(3)
    if match is None:
        raise ValueError  # Invalid command

    # Get section and option from first argument.
    arg1 = match.split('.')
    if len(arg1) == 1:
        section_name, option = "core", arg1[0]
    elif len(arg1) == 2:
        section_name, option = arg1
    else:
        raise ValueError  # invalid command format

    section = getattr(config, section_name, False)
    if not section:
        raise InvalidSection(section_name)
    static_sec = isinstance(section, StaticSection)

    if static_sec and not hasattr(section, option):
        raise InvalidSectionOption(section_name, option)  # Option not found in section

    if not static_sec and not config.parser.has_option(section_name, option):
        raise InvalidSectionOption(section_name, option)  # Option not found in section

    delim = trigger.group(2).find(' ')
    # Skip preceding whitespaces, if any.
    while delim > 0 and delim < len(trigger.group(2)) and trigger.group(2)[delim] == ' ':
        delim = delim + 1

    value = trigger.group(2)[delim:]
    if delim == -1 or delim == len(trigger.group(2)):
        value = None

    return (section, section_name, static_sec, option, value)


@sopel.module.require_privmsg("This command only works as a private message.")
@sopel.module.require_admin("This command requires admin privileges.")
@sopel.module.commands('set')
@sopel.module.example('.set core.owner MyNick')
def set_config(bot, trigger):
    """See and modify values of Sopel's config object.

    Trigger args:
        arg1 - section and option, in the form "section.option"
        arg2 - value

    If there is no section, section will default to "core".
    If value is not provided, the current value will be displayed.
    """
    try:
        section, section_name, static_sec, option, value = parse_section_option_value(bot.config, trigger)
    except ValueError:
        bot.reply('Usage: {}set section.option [value]'.format(bot.config.core.help_prefix))
        return
    except (InvalidSection, InvalidSectionOption) as exc:
        bot.say(exc.args[1])
        return

    # Display current value if no value is given
    if not value:
        if option.endswith("password") or option.endswith("pass"):
            value = "(password censored)"
        else:
            value = getattr(section, option)
        bot.reply("%s.%s = %s (%s)" % (section_name, option, value, type(value).__name__))
        return

    # Owner-related settings cannot be modified interactively. Any changes to these
    # settings must be made directly in the config file.
    if section_name == 'core' and option in ['owner', 'owner_account']:
        bot.say("Changing '{}.{}' requires manually editing the configuration file."
                .format(section_name, option))
        return

    # Otherwise, set the value to one given
    if static_sec:
        descriptor = getattr(section.__class__, option)
        try:
            if isinstance(descriptor, FilenameAttribute):
                value = descriptor.parse(value, bot.config, descriptor)
            else:
                value = descriptor.parse(value)
        except ValueError as exc:
            bot.say("Can't set attribute: " + str(exc))
            return
    setattr(section, option, value)
    bot.say("OK. Set '{}.{}' successfully.".format(section_name, option))


@sopel.module.require_privmsg("This command only works as a private message.")
@sopel.module.require_admin("This command requires admin privileges.")
@sopel.module.commands('unset')
@sopel.module.example('.unset core.owner')
def unset_config(bot, trigger):
    """Unset value of Sopel's config object.

    Unsetting a value will reset it to the default specified in the config
    definition.

    Trigger args:
        arg1 - section and option, in the form "section.option"

    If there is no section, section will default to "core".
    """
    try:
        section, section_name, static_sec, option, value = parse_section_option_value(bot.config, trigger)
    except ValueError:
        bot.reply('Usage: {}unset section.option [value]'.format(bot.config.core.help_prefix))
        return
    except (InvalidSection, InvalidSectionOption) as exc:
        bot.say(exc.args[1])
        return

    if value:
        bot.reply('Invalid command; no value should be provided to unset.')
        return

    try:
        setattr(section, option, None)
        bot.say("OK. Unset '{}.{}' successfully.".format(section_name, option))
    except ValueError:
        bot.reply('Cannot unset {}.{}; it is a required option.'.format(section_name, option))


@sopel.module.require_privmsg
@sopel.module.require_admin
@sopel.module.commands('save')
@sopel.module.example('.save')
def save_config(bot, trigger):
    """Save state of Sopel's config object to the configuration file."""
    bot.config.save()
