# coding=utf8
"""
help.py - Willie Help Module
Copyright 2008, Sean B. Palmer, inamidst.com
Copyright © 2013, Elad Alfassa, <elad@fedoraproject.org>
Licensed under the Eiffel Forum License 2.

http://willie.dftba.net
"""
from __future__ import unicode_literals

from willie.module import commands, rule, example, priority
from willie.tools import iterkeys

import textwrap


def setup(bot=None):
    if not bot:
        return

    if (bot.config.has_option('help', 'threshold') and not
            bot.config.help.threshold.isdecimal()):  # non-negative integer
        from willie.config import ConfigurationError
        raise ConfigurationError("Attribute threshold of section [help] must be a nonnegative integer")


@rule('$nick' '(?i)(help|doc) +([A-Za-z]+)(?:\?+)?$')
@example('.help tell')
@commands('help')
@priority('low')
def help(bot, trigger):
    """Shows a command's documentation, and possibly an example."""
    if not trigger.group(2):
        if not trigger.is_privmsg:
            bot.reply("Sending my resume in private...")

        bot.notice("Send e.g. '.help length' for more.", trigger.nick)

        groups = bot.modules_commands
        name_length = max(6, max(len(k) for k in groups))
        for name in sorted(groups):
            group = groups[name]
            # set the name column to a constant width
            name = name.upper().ljust(name_length)
            # bolden the name
            group_help = "\002" + name + "\002  " + "  ".join(group)
            # wrap message with indent for name column
            indent = " " * name_length + "  "
            group_help = textwrap.wrap(group_help, subsequent_indent=indent)
            # send it
            for line in group_help:
                bot.notice(line, trigger.nick)

    else:
        name = trigger.group(2)
        name = name.lower()

        if bot.config.has_option('help', 'threshold'):
            threshold = int(bot.config.help.threshold)
        else:
            threshold = 3

        if name in bot.doc:
            if len(bot.doc[name][0]) + (1 if bot.doc[name][1] else 0) > threshold:
                if trigger.nick != trigger.sender:  # don't say that if asked in private
                    bot.reply('The documentation for this command is too long; I\'m sending it to you in a private message.')
                msgfun = lambda l: bot.msg(trigger.nick, l)
            else:
                msgfun = bot.reply

            for line in bot.doc[name][0]:
                msgfun(line)
            if bot.doc[name][1]:
                msgfun('e.g. ' + bot.doc[name][1])


@commands('commands')
@priority('low')
def commands(bot, trigger):
    """Return a list of bot's commands"""
    names = ', '.join(sorted(iterkeys(bot.doc)))
    if not trigger.is_privmsg:
        bot.reply("I am sending you a private message of all my commands!")
    bot.msg(trigger.nick, 'Commands I recognise: ' + names + '.', max_messages=10)
    bot.msg(trigger.nick, ("For help, do '%s: help example' where example is the " +
                           "name of the command you want help for.") % bot.nick)


@rule('$nick' r'(?i)help(?:[?!]+)?$')
@priority('low')
def help2(bot, trigger):
    response = (
        'Hi, I\'m a bot. Say ".commands" to me in private for a list ' +
        'of my commands, or see http://willie.dftba.net for more ' +
        'general details. My owner is %s.'
    ) % bot.config.owner
    bot.reply(response)
