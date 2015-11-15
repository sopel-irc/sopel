# coding=utf-8
"""
help.py - Sopel Help Module
Copyright 2008, Sean B. Palmer, inamidst.com
Copyright © 2013, Elad Alfassa, <elad@fedoraproject.org>
Licensed under the Eiffel Forum License 2.

http://sopel.chat
"""
from __future__ import unicode_literals, absolute_import, print_function, division

import textwrap
import collections

from sopel.formatting import bold
from sopel.module import commands, rule, example, priority


@rule('$nick' '(?i)(help|doc) +([A-Za-z]+)(?:\?+)?$')
@example('.help tell')
@commands('help', 'commands')
@priority('low')
def help(bot, trigger):
    """Shows a command's documentation, and possibly an example."""
    if trigger.group(2):
        name = trigger.group(2)
        name = name.lower()

        # number of lines of help to show
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
    else:
        if not trigger.is_privmsg:
            bot.reply("I'm sending you a list of my commands in a private message!")
        bot.say(
            'You can see more info about any of these commands by doing .help '
            '<command> (e.g. .help time)',
            trigger.nick
        )

        name_length = max(6, max(len(k) for k in bot.command_groups.keys()))
        for category, cmds in collections.OrderedDict(sorted(bot.command_groups.items())).items():
            category = category.upper().ljust(name_length)
            cmds = '  '.join(cmds)
            msg = bold(category) + '  ' + cmds
            indent = ' ' * (name_length + 2)
            msg = textwrap.wrap(msg, subsequent_indent=indent)
            for line in msg:
                bot.say(line, trigger.nick)


@rule('$nick' r'(?i)help(?:[?!]+)?$')
@priority('low')
def help2(bot, trigger):
    response = (
        'Hi, I\'m a bot. Say ".commands" to me in private for a list ' +
        'of my commands, or see http://sopel.chat for more ' +
        'general details. My owner is %s.'
    ) % bot.config.core.owner
    bot.reply(response)
