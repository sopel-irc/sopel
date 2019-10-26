# coding=utf-8
"""
tell.py - Sopel Tell and Ask Module
Copyright 2008, Sean B. Palmer, inamidst.com
Licensed under the Eiffel Forum License 2.

https://sopel.chat
"""
from __future__ import unicode_literals, absolute_import, print_function, division

import datetime
import os
import time
import threading
import sys

from sopel.module import commands, nickname_commands, rule, priority, example, require_privilege, OP
from sopel.config.types import StaticSection, ValidatedAttribute
from sopel.tools import Identifier, iterkeys
from sopel.tools.time import get_timezone, format_time, seconds_to_human


MAXIMUM = 4


def loadReminders(fn, lock):
    lock.acquire()
    try:
        result = {}
        f = open(fn)
        for line in f:
            line = line.strip()
            if sys.version_info.major < 3:
                line = line.decode('utf-8')
            if line:
                try:
                    tellee, teller, verb, timenow, timestamp, msg = line.split('\t', 5)
                except ValueError:
                    continue  # @@ hmm
                result.setdefault(tellee, []).append((teller, verb, timenow, timestamp, msg))
        f.close()
    finally:
        lock.release()
    return result


def dumpReminders(fn, data, lock):
    lock.acquire()
    try:
        f = open(fn, 'w')
        for tellee in iterkeys(data):
            for remindon in data[tellee]:
                line = '\t'.join((tellee,) + remindon)
                try:
                    to_write = line + '\n'
                    if sys.version_info.major < 3:
                        to_write = to_write.encode('utf-8')
                    f.write(to_write)
                except IOError:
                    break
        try:
            f.close()
        except IOError:
            pass
    finally:
        lock.release()
    return True


class FormatSection(StaticSection):
    tell_format = ValidatedAttribute(
        'tell_format',
        default='relative')
    """Show relative timestamps by default"""


def configure(config):
    """
    | name        | example  | purpose                                       |
    | ----------- | -------- | --------------------------------------------- |
    | tell_format | absolute | Show absolute timestamp; defaults to relative |
    """
    config.define_section('tell', FormatSection)
    config.tell.configure_setting(
        'tell_format', 'Default timestamp format for messages sent later via tell/ask')


def setup(bot):
    bot.config.define_section('tell', FormatSection)
    fn = bot.nick + '-' + bot.config.core.host + '.tell.db'
    bot.tell_filename = os.path.join(bot.config.core.homedir, fn)
    if not os.path.exists(bot.tell_filename):
        try:
            f = open(bot.tell_filename, 'w')
        except (OSError, IOError):  # TODO: Remove IOError when dropping py2 support
            pass
        else:
            f.write('')
            f.close()
    if 'tell_lock' not in bot.memory:
        bot.memory['tell_lock'] = threading.Lock()
    if 'reminders' not in bot.memory:
        bot.memory['reminders'] = loadReminders(bot.tell_filename, bot.memory['tell_lock'])


def shutdown(bot):
    for key in ['tell_lock', 'reminders']:
        try:
            del bot.memory[key]
        except KeyError:
            pass


@commands('tell', 'ask')
@nickname_commands('tell', 'ask')
@example('$nickname, tell dgw he broke something again.')
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
        timestamp = datetime.datetime.timestamp(datetime.datetime.now())
        timestamp = str(int(timestamp))
        bot.memory['tell_lock'].acquire()
        try:
            if tellee not in bot.memory['reminders']:
                bot.memory['reminders'][tellee] = [(teller, verb, timenow, timestamp, msg)]
            else:
                bot.memory['reminders'][tellee].append((teller, verb, timenow, timestamp, msg))
        finally:
            bot.memory['tell_lock'].release()

        response = "I'll %s %s that when they're around." % (verb, tellee)

        bot.reply(response)
    elif Identifier(teller) == tellee:
        bot.say('You can %s yourself that.' % verb)
    else:
        bot.say("Hey, I'm not as stupid as Monty you know!")

    dumpReminders(bot.tell_filename, bot.memory['reminders'], bot.memory['tell_lock'])  # @@ tell


def getReminders(bot, channel, key, tellee):
    lines = []
    today = time.strftime('%d %b', time.gmtime())

    bot.memory['tell_lock'].acquire()
    try:
        for (teller, verb, date_time, timestamp, msg) in bot.memory['reminders'][key]:
            format_ = bot.db.get_nick_value(tellee, 'tell_format') or \
                bot.db.get_channel_value(channel, 'tell_format') or \
                bot.config.tell.tell_format or \
                'relative'
            template = "{destination}: "
            if date_time.startswith(today):
                date_time = date_time[len(today) + 1:]

            if verb.lower() == "ask":
                if format_ == "relative":
                    template += "{sender} asked {msg} (sent {timedelta})"
                else:
                    template += "{date_time} {sender} asked {msg}"
            else:
                if format_ == "relative":
                    template += "<{sender}> {msg} (sent {timedelta})"
                else:
                    template += "{date_time} <{sender}> {msg}"
            timedelta = int(datetime.datetime.timestamp(datetime.datetime.now()) - int(timestamp))
            timedelta = seconds_to_human(timedelta)
            lines.append(template.format(
                destination=tellee,
                date_time=date_time,
                timedelta=timedelta,
                sender=teller,
                msg=msg)
            )

        try:
            del bot.memory['reminders'][key]
        except KeyError:
            bot.say('Er…', channel)
    finally:
        bot.memory['tell_lock'].release()
    return lines


@rule('(.*)')
@priority('low')
def message(bot, trigger):

    tellee = trigger.nick
    channel = trigger.sender

    if not os.path.exists(bot.tell_filename):
        return

    reminders = []
    try:
        remkeys = list(reversed(sorted(bot.memory['reminders'].keys())))
    except KeyError:
        return

    for remkey in remkeys:
        if not remkey.endswith('*') or remkey.endswith(':'):
            if tellee.lower() == remkey.lower():
                reminders.extend(getReminders(bot, channel, remkey, tellee))
        elif tellee.lower().startswith(remkey.lower().rstrip('*:')):
            reminders.extend(getReminders(bot, channel, remkey, tellee))

    for line in reminders[:MAXIMUM]:
        bot.say(line)

    if reminders[MAXIMUM:]:
        bot.say('Further messages sent privately')
        for line in reminders[MAXIMUM:]:
            bot.say(line, tellee)

    if len(bot.memory['reminders'].keys()) != remkeys:
        dumpReminders(bot.tell_filename, bot.memory['reminders'], bot.memory['tell_lock'])  # @@ tell


@commands('settellf', 'settellformat')
@example('.settellf absolute')
def update_user_tell_format(bot, trigger):
    """Set your preferred tell timestamp format. (absolute or relative)
    """
    argument = trigger.group(2)
    if not argument:
        bot.reply("What format do you want to set?")
        return

    valid_formats = ['absolute', 'relative']

    argument = argument.lower().strip()
    if argument not in valid_formats:
        return bot.reply("I need a valid format (relative or absolute)")

    bot.db.set_nick_value(trigger.nick, 'tell_format', argument)

    bot.reply('I have set the tell timestamp format for you to %s' % argument)


@commands('gettellf', 'gettellformat')
@example('.gettellf [nick]')
def get_user_tell_format(bot, trigger):
    """Gets a user's preferred tell timestamp format; will show yours if no user specified."""
    nick = trigger.group(2)
    if not nick:
        nick = trigger.nick

    nick = nick.strip()
    format_ = bot.db.get_nick_value(nick, 'tell_format')

    if format_:
        bot.say('%s\'s tell timestamp format is %s.' % (nick, format_))
    else:
        bot.say('%s has not set their tell timestamp format' % nick)


@commands('setchanneltellf', 'setctellf')
@example('.setctellf absolute')
@require_privilege(OP)
def update_channel(bot, trigger):
    """Set the preferred tell timestamp format for the channel."""
    argument = trigger.group(2)
    if not argument:
        bot.reply("What format do you want to set?")
        return

    valid_formats = ['absolute', 'relative']

    argument = argument.lower().strip()
    if argument not in valid_formats:
        return bot.reply("I need a valid format (relative or absolute)")

    channel = trigger.sender
    bot.db.set_channel_value(channel, 'tell_format', argument)

    bot.reply('I have set the tell timestamp format for %s to %s' % (channel, argument))


@commands('getchanneltellf', 'getctellf')
@example('.getctellf [channel]')
def get_channel_tell_format(bot, trigger):
    """
    Gets the channel's preferred tell timestamp format; returns the current channel's
    if no channel name is given.
    """
    channel = trigger.group(2)
    if not channel:
        channel = trigger.sender

    channel = channel.strip()
    format_ = bot.db.get_channel_value(channel, 'tell_format')

    if format_:
        bot.say('%s\'s tell timestamp format: %s' % (channel, format_))
    else:
        bot.say('%s has no preferred tell timestamp format' % channel)
