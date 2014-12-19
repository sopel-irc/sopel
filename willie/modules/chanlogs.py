# coding=utf8
"""
chanlogs.py - Willie Channel Logger module
Copyright 2014, David Baumgold <david@davidbaumgold.com>

Licensed under the Eiffel Forum License 2

http://willie.dftba.net
"""
from __future__ import unicode_literals
import os
import os.path
import threading
import sys
from datetime import datetime
import willie.module
import willie.tools
from willie.config import ConfigurationError

MESSAGE_TPL = "{datetime}  <{trigger.nick}> {message}"
ACTION_TPL = "{datetime}  * {trigger.nick} {message}"
NICK_TPL = "{datetime}  *** {trigger.nick} is now known as {trigger.sender}"
JOIN_TPL = "{datetime}  *** {trigger.nick} has joined {trigger}"
PART_TPL = "{datetime}  *** {trigger.nick} has left {trigger}"
QUIT_TPL = "{datetime}  *** {trigger.nick} has quit IRC"


def configure(config):
    if config.option("Configure channel logging", False):
        config.add_section("chanlogs")
        config.interactive_add(
            "chanlogs", "dir",
            "Absolute path to channel log storage directory",
            default=os.path.join("~", "chanlogs")
        )
        config.add_option("chanlogs", "by_day", "Split log files by day", default=True)
        config.add_option("chanlogs", "privmsg", "Record private messages", default=False)
        config.add_option("chanlogs", "microseconds", "Microsecond precision", default=False)
        # could ask if user wants to customize message templates,
        # but that seems unnecessary


def get_fpath(bot, trigger, channel=None):
    """
    Returns a string corresponding to the path to the file where the message
    currently being handled should be logged.
    """
    basedir = os.path.expanduser(bot.config.chanlogs.dir)
    channel = channel or trigger.sender
    channel = channel.lstrip("#")

    dt = datetime.utcnow()
    if not bot.config.chanlogs.microseconds:
        dt = dt.replace(microsecond=0)
    if bot.config.chanlogs.by_day:
        fname = "{channel}-{date}.log".format(channel=channel, date=dt.date().isoformat())
    else:
        fname = "{channel}.log".format(channel=channel)
    return os.path.join(basedir, fname)


def _format_template(tpl, bot, trigger, **kwargs):
    dt = datetime.utcnow()
    if not bot.config.chanlogs.microseconds:
        dt = dt.replace(microsecond=0)

    formatted = tpl.format(
        trigger=trigger, datetime=dt.isoformat(),
        date=dt.date().isoformat(), time=dt.time().isoformat(),
        **kwargs
    ) + "\n"

    if sys.version_info.major < 3 and isinstance(formatted, unicode):
        formatted = formatted.encode('utf-8')
    return formatted


def setup(bot):
    if not getattr(bot.config, "chanlogs", None):
        raise ConfigurationError("Channel logs are not configured")
    if not getattr(bot.config.chanlogs, "dir", None):
        raise ConfigurationError("Channel log storage directory is not defined")

    # ensure log directory exists
    basedir = os.path.expanduser(bot.config.chanlogs.dir)
    if not os.path.exists(basedir):
        os.makedirs(basedir)

    # locks for log files
    if not bot.memory.contains('chanlog_locks'):
        bot.memory['chanlog_locks'] = willie.tools.WillieMemoryWithDefault(threading.Lock)


@willie.module.rule('.*')
@willie.module.unblockable
def log_message(bot, message):
    "Log every message in a channel"
    # if this is a private message and we're not logging those, return early
    if message.sender.is_nick() and not bot.config.chanlogs.privmsg:
        return

    # determine which template we want, message or action
    if message.startswith("\001ACTION ") and message.endswith("\001"):
        tpl = bot.config.chanlogs.action_template or ACTION_TPL
        # strip off start and end
        message = message[8:-1]
    else:
        tpl = bot.config.chanlogs.message_template or MESSAGE_TPL

    logline = _format_template(tpl, bot, message, message=message)
    fpath = get_fpath(bot, message)
    with bot.memory['chanlog_locks'][fpath]:
        with open(fpath, "a") as f:
            f.write(logline)


@willie.module.rule('.*')
@willie.module.event("JOIN")
@willie.module.unblockable
def log_join(bot, trigger):
    tpl = bot.config.chanlogs.join_template or JOIN_TPL
    logline = _format_template(tpl, bot, trigger)
    fpath = get_fpath(bot, trigger, channel=trigger.sender)
    with bot.memory['chanlog_locks'][fpath]:
        with open(fpath, "a") as f:
            f.write(logline)


@willie.module.rule('.*')
@willie.module.event("PART")
@willie.module.unblockable
def log_part(bot, trigger):
    tpl = bot.config.chanlogs.part_template or PART_TPL
    logline = _format_template(tpl, bot, trigger=trigger)
    fpath = get_fpath(bot, trigger, channel=trigger.sender)
    with bot.memory['chanlog_locks'][fpath]:
        with open(fpath, "a") as f:
            f.write(logline)


@willie.module.rule('.*')
@willie.module.event("QUIT")
@willie.module.unblockable
@willie.module.thread(False)
@willie.module.priority('high')
def log_quit(bot, trigger):
    tpl = bot.config.chanlogs.quit_template or QUIT_TPL
    logline = _format_template(tpl, bot, trigger)
    # make a copy of bot.privileges that we can safely iterate over
    privcopy = list(bot.privileges.items())
    # write logline to *all* channels that the user was present in
    for channel, privileges in privcopy:
        if trigger.nick in privileges:
            fpath = get_fpath(bot, trigger, channel)
            with bot.memory['chanlog_locks'][fpath]:
                with open(fpath, "a") as f:
                    f.write(logline)


@willie.module.rule('.*')
@willie.module.event("NICK")
@willie.module.unblockable
def log_nick_change(bot, trigger):
    tpl = bot.config.chanlogs.nick_template or NICK_TPL
    logline = _format_template(tpl, bot, trigger)
    old_nick = trigger.nick
    new_nick = trigger.sender
    # make a copy of bot.privileges that we can safely iterate over
    privcopy = list(bot.privileges.items())
    # write logline to *all* channels that the user is present in
    for channel, privileges in privcopy:
        if old_nick in privileges or new_nick in privileges:
            fpath = get_fpath(bot, trigger, channel)
            with bot.memory['chanlog_locks'][fpath]:
                with open(fpath, "a") as f:
                    f.write(logline)
