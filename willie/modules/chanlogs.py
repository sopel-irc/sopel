#coding: utf8
"""
Channel logger
"""
from __future__ import unicode_literals
import os
import os.path
from datetime import datetime
import willie.module

MESSAGE_TPL = "{datetime}  <{origin.nick}> {message}"
ACTION_TPL = "{datetime}  * {origin.nick} {message}"
NICK_TPL = "{datetime}  *** {origin.nick} is now known as {origin.sender}"
JOIN_TPL = "{datetime}  *** {origin.nick} has joined {trigger}"
PART_TPL = "{datetime}  *** {origin.nick} has left {trigger}"
QUIT_TPL = "{datetime}  *** {origin.nick} has quit IRC"


def configure(config):
    if config.option("Configure channel logging", False):
        config.add_section("chanlogs")
        config.interactive_add(
            "chanlogs", "dir",
            "Path to channel log storage directory (should be an absolute path, accessible on a webserver)",
            default="/home/willie/chanlogs"
        )
        config.add_option("chanlogs", "by_day", "Split log files by day", default=True)
        config.add_option("chanlogs", "privmsg", "Record private messages", default=False)
        config.add_option("chanlogs", "microseconds", "Microsecond precision", default=False)
        # could ask if user wants to customize message templates,
        # but that seems unnecessary


def get_fpath(bot, channel=None):
    """
    Returns a string corresponding to the path to the file where the message
    currently being handled should be logged.
    """
    basedir = os.path.expanduser(bot.config.chanlogs.dir)
    channel = channel or bot.origin.sender
    channel = channel.lstrip("#")

    dt = datetime.utcnow()
    if not bot.config.chanlogs.microseconds:
        dt = dt.replace(microsecond=0)
    if bot.config.chanlogs.by_day:
        fname = "{channel}-{date}.log".format(channel=channel, date=dt.date().isoformat())
    else:
        fname = "{channel}.log".format(channel=channel)
    return os.path.join(basedir, fname)


def _format_template(tpl, bot, **kwargs):
    dt = datetime.utcnow()
    if not bot.config.chanlogs.microseconds:
        dt = dt.replace(microsecond=0)

    return tpl.format(
        origin=bot.origin, datetime=dt.isoformat(),
        date=dt.date().isoformat(), time=dt.time().isoformat(),
        **kwargs
    )


def setup(bot):
    # ensure log directory exists
    basedir = os.path.expanduser(bot.config.chanlogs.dir)
    if not os.path.exists(basedir):
        os.makedirs(basedir)


@willie.module.rule('.*')
def log_message(bot, message):
    "Log every message in a channel"
    # if this is a private message and we're not logging those, return early
    if not bot.origin.sender.startswith("#") and not bot.config.chanlogs.privmsg:
        return

    # determine which template we want, message or action
    if message.startswith("\001ACTION ") and message.endswith("\001"):
        tpl = bot.config.chanlogs.action_template or ACTION_TPL
        # strip off start and end
        message = message[8:-1]
    else:
        tpl = bot.config.chanlogs.message_template or MESSAGE_TPL

    logline = _format_template(tpl, bot, message=message)
    with open(get_fpath(bot), "a") as f:
        f.write(logline + "\n")


@willie.module.rule('.*')
@willie.module.event("JOIN")
def log_join(bot, trigger):
    tpl = bot.config.chanlogs.join_template or JOIN_TPL
    logline = _format_template(tpl, bot, trigger=trigger)
    with open(get_fpath(bot, channel=trigger), "a") as f:
        f.write(logline + "\n")


@willie.module.rule('.*')
@willie.module.event("PART")
def log_part(bot, trigger):
    tpl = bot.config.chanlogs.part_template or PART_TPL
    logline = _format_template(tpl, bot, trigger=trigger)
    with open(get_fpath(bot, channel=trigger), "a") as f:
        f.write(logline + "\n")


@willie.module.rule('.*')
@willie.module.event("QUIT")
def log_quit(bot, trigger):
    tpl = bot.config.chanlogs.quit_template or QUIT_TPL
    logline = _format_template(tpl, bot, trigger=trigger)
    # write it to *all* channels
    for channel in bot.channels:
        with open(get_fpath(bot, channel), "a") as f:
            f.write(logline + "\n")


@willie.module.rule('.*')
@willie.module.event("NICK")
def log_nick_change(bot, trigger):
    tpl = bot.config.chanlogs.nick_template or NICK_TPL
    logline = _format_template(tpl, bot, trigger=trigger)
    # write it to *all* channels
    for channel in bot.channels:
        with open(get_fpath(bot, channel), "a") as f:
            f.write(logline + "\n")
