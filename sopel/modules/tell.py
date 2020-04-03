# coding=utf-8
"""
tell.py - Sopel Tell and Ask Module
Copyright 2008, Sean B. Palmer, inamidst.com
Copyright 2019, dgw, technobabbl.es
Licensed under the Eiffel Forum License 2.

https://sopel.chat
"""
from __future__ import unicode_literals, absolute_import, print_function, division

import io  # don't use `codecs` for loading the DB; it will split lines on some IRC formatting
import logging
import os
import time
import threading
from collections import defaultdict

from sopel.config.types import StaticSection, ValidatedAttribute
from sopel import module
from sopel.tools import Identifier
from sopel.tools.time import get_timezone, format_time


LOGGER = logging.getLogger(__name__)


class TellSection(StaticSection):
    use_private_reminder = ValidatedAttribute(
        'use_private_reminder', parse=bool, default=False)
    """When set to ``true``, Sopel will send reminder as private message."""
    maximum_public = ValidatedAttribute(
        'maximum_public', parse=int, default=4)
    """How many Sopel can send in public before using private message."""


def configure(config):
    """
    | name | example | purpose |
    | ---- | ------- | ------- |
    | use_private_reminder | false | Send reminders as private message |
    | maximum_public | 4 | Send up to this amount of reminders in public |
    """
    config.define_section('tell', TellSection)
    config.tell.configure_setting(
        'use_private_reminder',
        'Should Sopel send tell/ask reminders as private message only?')
    if not config.tell.use_private_reminder:
        config.tell.configure_setting(
            'maximum_public',
            'How many tell/ask reminders Sopel will send as public message '
            'before sending them as private messages?')


def load_reminders(filename):
    """Load tell/ask reminders from a ``filename``.

    :param str filename: path to the tell/ask reminders file
    :return: a dict with the tell/ask reminders
    :rtype: dict
    """
    result = defaultdict(list)
    with io.open(filename, 'r', encoding='utf-8') as fd:
        for line in fd:
            line = line.strip()
            if line:
                try:
                    tellee, teller, verb, timenow, msg = line.split('\t', 4)
                except ValueError:
                    continue  # TODO: Add warning log about malformed reminder
                result[tellee].append((teller, verb, timenow, msg))

    return result


def dump_reminders(filename, data):
    """Dump tell/ask reminders (``data``) into a ``filename``.

    :param str filename: path to the tell/ask reminders file
    :param dict data: tell/ask reminders ``dict``
    """
    with io.open(filename, 'w', encoding='utf-8') as fd:
        for tellee, reminders in data.items():
            for reminder in reminders:
                line = '\t'.join((tellee,) + tuple(reminder))
                fd.write(line + '\n')
    return True


def setup(bot):
    bot.config.define_section('tell', TellSection)
    fn = bot.config.basename + '.tell.db'
    bot.tell_filename = os.path.join(bot.config.core.homedir, fn)

    # Pre-7.0 migration logic. Remove in 8.0 or 9.0.
    old = bot.nick + '-' + bot.config.core.host + '.tell.db'
    old = os.path.join(bot.config.core.homedir, old)
    if os.path.isfile(old):
        LOGGER.info("Attempting to migrate old 'tell' database {}..."
                    .format(old))
        try:
            os.rename(old, bot.tell_filename)
        except OSError:
            LOGGER.error("Migration failed!")
            LOGGER.error("Old filename: {}".format(old))
            LOGGER.error("New filename: {}".format(bot.tell_filename))
            LOGGER.error(
                "See https://sopel.chat/usage/installing/upgrading-to-sopel-7/#reminder-db-migration")
        else:
            LOGGER.info("Migration finished!")
    # End migration logic

    if not os.path.exists(bot.tell_filename):
        with io.open(bot.tell_filename, 'w', encoding='utf-8') as fd:
            # if we can't open/write into the file, the tell plugin can't work
            fd.write('')

    if 'tell_lock' not in bot.memory:
        bot.memory['tell_lock'] = threading.Lock()

    if 'reminders' not in bot.memory:
        with bot.memory['tell_lock']:
            bot.memory['reminders'] = load_reminders(bot.tell_filename)


def shutdown(bot):
    for key in ['tell_lock', 'reminders']:
        try:
            del bot.memory[key]
        except KeyError:
            pass


@module.commands('tell', 'ask')
@module.nickname_commands('tell', 'ask')
@module.example('$nickname, tell dgw he broke something again.')
def f_remind(bot, trigger):
    """Give someone a message the next time they're seen"""
    teller = trigger.nick
    verb = trigger.group(1)

    if not trigger.group(3):
        bot.reply("%s whom?" % verb)
        return

    tellee = trigger.group(3).rstrip('.,:;')
    msg = trigger.group(2).lstrip(tellee).lstrip()

    if not msg:
        bot.reply("%s %s what?" % (verb, tellee))
        return

    tellee = Identifier(tellee)

    if not os.path.exists(bot.tell_filename):
        return

    if len(tellee) > 30:  # TODO: use server NICKLEN here when available
        return bot.reply('That nickname is too long.')
    if tellee == bot.nick:
        return bot.reply("I'm here now; you can tell me whatever you want!")

    if tellee not in (Identifier(teller), bot.nick, 'me'):
        tz = get_timezone(bot.db, bot.config, None, tellee)
        timenow = format_time(bot.db, bot.config, tz, tellee)
        with bot.memory['tell_lock']:
            if tellee not in bot.memory['reminders']:
                bot.memory['reminders'][tellee] = [(teller, verb, timenow, msg)]
            else:
                bot.memory['reminders'][tellee].append((teller, verb, timenow, msg))
            # save the reminders
            dump_reminders(bot.tell_filename, bot.memory['reminders'])

        response = "I'll pass that on when %s is around." % tellee
        bot.reply(response)
    elif Identifier(teller) == tellee:
        bot.say('You can %s yourself that.' % verb)
    else:
        bot.say("Hey, I'm not as stupid as Monty you know!")


def get_nick_reminders(reminders, nick):
    lines = []
    template = "%s: %s <%s> %s %s %s"
    today = time.strftime('%d %b', time.gmtime())

    for (teller, verb, datetime, msg) in reminders:
        if datetime.startswith(today):
            datetime = datetime[len(today) + 1:]
        lines.append(template % (nick, datetime, teller, verb, nick, msg))

    return lines


def nick_match_tellee(nick, tellee):
    """Tell if a ``nick`` matches a ``tellee``.

    :param str nick: Nick seen by the bot
    :param str tellee: Tellee name or pattern

    The check between ``nick`` and ``tellee`` is case-insensitive::

        >>> nick_match_tellee('Exirel', 'exirel')
        True
        >>> nick_match_tellee('exirel', 'EXIREL')
        True
        >>> nick_match_tellee('exirel', 'dgw')
        False

    If ``tellee`` ends with a wildcard token (``*`` or ``:``), then ``nick``
    matches if it starts with ``tellee`` (without the token)::

        >>> nick_match_tellee('Exirel', 'Exi*')
        True
        >>> nick_match_tellee('Exirel', 'exi:')
        True
        >>> nick_match_tellee('Exirel', 'Exi')
        False

    Note that this is still case-insensitive.
    """
    if tellee[-1] in ['*', ':']:  # these are wildcard token
        return nick.lower().startswith(tellee.lower().rstrip('*:'))
    return nick.lower() == tellee.lower()


@module.rule('(.*)')
@module.priority('low')
@module.unblockable
def message(bot, trigger):
    nick = trigger.nick

    if not os.path.exists(bot.tell_filename):
        # plugin can't work without its storage file
        return

    # get all matching reminders
    reminders = []
    tellees = list(reversed(sorted(
        tellee
        for tellee in bot.memory['reminders']
        if nick_match_tellee(nick, tellee)
    )))

    with bot.memory['tell_lock']:
        # pop reminders for nick
        reminders = list(
            reminder
            for tellee in tellees
            for reminder in get_nick_reminders(
                bot.memory['reminders'].pop(tellee, []), nick)
        )

    # check if there are reminders to send
    if not reminders:
        return  # nothing to do

    # then send reminders (as public and/or private messages)
    if bot.config.tell.use_private_reminder:
        # send reminders with private messages
        for line in reminders:
            bot.say(line, nick)
    else:
        # send up to 'maximum_public' reminders to the channel
        max_public = bot.config.tell.maximum_public
        for line in reminders[:max_public]:
            bot.say(line)

        # send other reminders directly to nick as private message
        if reminders[max_public:]:
            bot.say('Further messages sent privately')
            for line in reminders[max_public:]:
                bot.say(line, nick)

    # save reminders left in memory
    with bot.memory['tell_lock']:
        dump_reminders(bot.tell_filename, bot.memory['reminders'])
