# coding=utf-8
"""
meetbot.py - Sopel Meeting Logger Plugin
This plugin is an attempt to implement some of the functionality of Debian's meetbot
Copyright © 2012, Elad Alfassa, <elad@fedoraproject.org>
Licensed under the Eiffel Forum License 2.

https://sopel.chat
"""
from __future__ import absolute_import, division, print_function, unicode_literals

import codecs
import collections
import os
import re
from string import punctuation, whitespace
import time

from sopel import formatting, plugin, tools
from sopel.config import types
from sopel.modules.url import find_title


UNTITLED_MEETING = "Untitled meeting"


class MeetbotSection(types.StaticSection):
    """Configuration file section definition"""

    meeting_log_path = types.FilenameAttribute(
        "meeting_log_path",
        relative=False,
        directory=True,
        default="~/www/meetings")
    """Path to meeting logs storage directory.

    This should be an absolute path, accessible on a webserver.
    """

    meeting_log_baseurl = types.ValidatedAttribute(
        "meeting_log_baseurl",
        default="http://localhost/~sopel/meetings")
    """Base URL for the meeting logs directory."""


def configure(config):
    """
    | name | example | purpose |
    | ---- | ------- | ------- |
    | meeting\\_log\\_path | /home/sopel/www/meetings | Path to meeting logs storage directory (should be an absolute path, accessible on a webserver) |
    | meeting\\_log\\_baseurl | http://example.com/~sopel/meetings | Base URL for the meeting logs directory |
    """
    config.define_section("meetbot", MeetbotSection)
    config.meetbot.configure_setting(
        "meeting_log_path", "Enter the directory to store logs in."
    )
    config.meetbot.configure_setting(
        "meeting_log_baseurl", "Enter the base URL for the meeting logs."
    )


def setup(bot):
    bot.config.define_section("meetbot", MeetbotSection)


meetings_dict = collections.defaultdict(dict)  # Saves metadata about currently running meetings
"""
meetings_dict is a 2D dict.

Each meeting should have:
channel
time of start
head (can stop the meeting, plus all abilities of chairs)
chairs (can add infolines to the logs)
title
current subject
comments (what people who aren't voiced want to add)

Using channel as the meeting ID as there can't be more than one meeting in a
channel at the same time.
"""

# To be defined on meeting start as part of sanity checks, used by logging
# functions so we don't have to pass them bot
meeting_log_path = ""
meeting_log_baseurl = ""

# A dict of channels to the actions that have been created in them. This way
# we can have .listactions spit them back out later on.
meeting_actions = {}


# Get the logfile name for the meeting in the requested channel
# Used by all logging functions and web path
def figure_logfile_name(channel):
    if meetings_dict[channel]["title"] == UNTITLED_MEETING:
        name = "untitled"
    else:
        name = meetings_dict[channel]["title"]
    # Real simple sluggifying.
    # May not handle unicode or unprintables well. Close enough.
    for character in punctuation + whitespace:
        name = name.replace(character, "-")
    name = name.strip("-")
    timestring = time.strftime(
        "%Y-%m-%d-%H:%M", time.gmtime(meetings_dict[channel]["start"])
    )
    filename = timestring + "_" + name
    return filename


# Start HTML log
def log_html_start(channel):
    logfile_filename = os.path.join(
        meeting_log_path + channel, figure_logfile_name(channel) + ".html"
    )
    logfile = codecs.open(logfile_filename, "a", encoding="utf-8")
    timestring = time.strftime(
        "%Y-%m-%d %H:%M", time.gmtime(meetings_dict[channel]["start"])
    )
    title = "%s at %s, %s" % (meetings_dict[channel]["title"], channel, timestring)
    logfile.write(
        (
            "<!doctype html><html><head><meta charset='utf-8'>\n"
            "<title>{title}</title>\n</head><body>\n<h1>{title}</h1>\n"
        ).format(title=title)
    )
    logfile.write(
        "<h4>Meeting started by %s</h4><ul>\n" % meetings_dict[channel]["head"]
    )
    logfile.close()


# Write a list item in the HTML log
def log_html_listitem(item, channel):
    logfile_filename = os.path.join(
        meeting_log_path + channel, figure_logfile_name(channel) + ".html"
    )
    logfile = codecs.open(logfile_filename, "a", encoding="utf-8")
    logfile.write("<li>" + item + "</li>\n")
    logfile.close()


# End the HTML log
def log_html_end(channel):
    logfile_filename = os.path.join(
        meeting_log_path + channel, figure_logfile_name(channel) + ".html"
    )
    logfile = codecs.open(logfile_filename, "a", encoding="utf-8")
    current_time = time.strftime("%H:%M:%S", time.gmtime())
    logfile.write("</ul>\n<h4>Meeting ended at %s UTC</h4>\n" % current_time)
    plainlog_url = meeting_log_baseurl + tools.web.quote(
        channel + "/" + figure_logfile_name(channel) + ".log"
    )
    logfile.write('<a href="%s">Full log</a>' % plainlog_url)
    logfile.write("\n</body>\n</html>\n")
    logfile.close()


# Write a string to the plain text log
def log_plain(item, channel):
    logfile_filename = os.path.join(
        meeting_log_path + channel, figure_logfile_name(channel) + ".log"
    )
    logfile = codecs.open(logfile_filename, "a", encoding="utf-8")
    current_time = time.strftime("%H:%M:%S", time.gmtime())
    logfile.write("[" + current_time + "] " + item + "\r\n")
    logfile.close()


# Check if a meeting is currently running
def is_meeting_running(channel):
    try:
        return meetings_dict[channel]["running"]
    except KeyError:
        return False


# Check if nick is a chair or head of the meeting
def is_chair(nick, channel):
    try:
        return (
            nick.lower() == meetings_dict[channel]["head"] or
            nick.lower() in meetings_dict[channel]["chairs"]
        )
    except KeyError:
        return False


# Start meeting (also performs all required sanity checks)
@plugin.command("startmeeting")
@plugin.example(".startmeeting", user_help=True)
@plugin.example(".startmeeting Meeting Title", user_help=True)
@plugin.require_chanmsg("Meetings can only be started in channels")
def startmeeting(bot, trigger):
    """
    Start a meeting.\
    See [meetbot plugin usage]({% link _usage/meetbot-plugin.md %})
    """
    if is_meeting_running(trigger.sender):
        bot.say("There is already an active meeting here!")
        return
    # Start the meeting
    meetings_dict[trigger.sender]["start"] = time.time()
    if not trigger.group(2):
        meetings_dict[trigger.sender]["title"] = UNTITLED_MEETING
    else:
        meetings_dict[trigger.sender]["title"] = trigger.group(2)
    meetings_dict[trigger.sender]["head"] = trigger.nick.lower()
    meetings_dict[trigger.sender]["running"] = True
    meetings_dict[trigger.sender]["comments"] = []

    # Set up paths and URLs
    global meeting_log_path
    meeting_log_path = bot.config.meetbot.meeting_log_path
    if not meeting_log_path.endswith(os.sep):
        meeting_log_path += os.sep

    global meeting_log_baseurl
    meeting_log_baseurl = bot.config.meetbot.meeting_log_baseurl
    if not meeting_log_baseurl.endswith("/"):
        meeting_log_baseurl = meeting_log_baseurl + "/"

    channel_log_path = meeting_log_path + trigger.sender
    if not os.path.isdir(channel_log_path):
        try:
            os.makedirs(channel_log_path)
        except Exception:  # TODO: Be specific
            bot.say(
                "Meeting not started: Couldn't create log directory for this channel"
            )
            meetings_dict[trigger.sender] = collections.defaultdict(dict)
            raise
    # Okay, meeting started!
    log_plain("Meeting started by " + trigger.nick.lower(), trigger.sender)
    log_html_start(trigger.sender)
    meeting_actions[trigger.sender] = []
    bot.say(
        (
            formatting.bold("Meeting started!") + " use {0}action, {0}agreed, "
            "{0}info, {0}link, {0}chairs, {0}subject, and {0}comments to "
            "control the meeting. To end the meeting, type {0}endmeeting"
        ).format(bot.config.core.help_prefix)
    )
    bot.say(
        (
            "Users without speaking permission can participate by sending me "
            "a PM with `{0}comment {1}` followed by their comment."
        ).format(bot.config.core.help_prefix, trigger.sender)
    )


# Change the current subject (will appear as <h3> in the HTML log)
@plugin.command("subject")
@plugin.example(".subject roll call")
def meetingsubject(bot, trigger):
    """
    Change the meeting subject.\
    See [meetbot plugin usage]({% link _usage/meetbot-plugin.md %})
    """
    if not is_meeting_running(trigger.sender):
        bot.say("There is no active meeting")
        return
    if not trigger.group(2):
        bot.say("What is the subject?")
        return
    if not is_chair(trigger.nick, trigger.sender):
        bot.say("Only meeting head or chairs can do that")
        return
    meetings_dict[trigger.sender]["current_subject"] = trigger.group(2)
    logfile_filename = os.path.join(
        meeting_log_path + trigger.sender, figure_logfile_name(trigger.sender) + ".html"
    )
    logfile = codecs.open(logfile_filename, "a", encoding="utf-8")
    logfile.write("</ul><h3>" + trigger.group(2) + "</h3><ul>")
    logfile.close()
    log_plain(
        "Current subject: {} (set by {})".format(trigger.group(2), trigger.nick),
        trigger.sender,
    )
    bot.say(formatting.bold("Current subject:") + " " + trigger.group(2))


# End the meeting
@plugin.command("endmeeting")
@plugin.example(".endmeeting")
def endmeeting(bot, trigger):
    """
    End a meeting.\
    See [meetbot plugin usage]({% link _usage/meetbot-plugin.md %})
    """
    if not is_meeting_running(trigger.sender):
        bot.say("There is no active meeting")
        return
    if not is_chair(trigger.nick, trigger.sender):
        bot.say("Only meeting head or chairs can do that")
        return
    meeting_length = time.time() - meetings_dict[trigger.sender]["start"]
    bot.say(
        formatting.bold("Meeting ended!") +
        " Total meeting length %d minutes" % (meeting_length // 60)
    )
    log_html_end(trigger.sender)
    htmllog_url = meeting_log_baseurl + tools.web.quote(
        trigger.sender + "/" + figure_logfile_name(trigger.sender) + ".html"
    )
    log_plain(
        "Meeting ended by %s. Total meeting length: %d minutes"
        % (trigger.nick, meeting_length // 60),
        trigger.sender,
    )
    bot.say("Meeting minutes: " + htmllog_url)
    meetings_dict[trigger.sender] = collections.defaultdict(dict)
    del meeting_actions[trigger.sender]


# Set meeting chairs (people who can control the meeting)
@plugin.command("chairs")
@plugin.example(".chairs Tyrope Jason elad")
def chairs(bot, trigger):
    """
    Set the meeting chairs.\
    See [meetbot plugin usage]({% link _usage/meetbot-plugin.md %})
    """
    if not is_meeting_running(trigger.sender):
        bot.say("There is no active meeting")
        return
    if not trigger.group(2):
        bot.say(
            "Who are the chairs? Try `{}chairs Alice Bob Cindy`".format(
                bot.config.core.help_prefix
            )
        )
        return
    if trigger.nick.lower() == meetings_dict[trigger.sender]["head"]:
        meetings_dict[trigger.sender]["chairs"] = trigger.group(2).lower().split(" ")
        chairs_readable = trigger.group(2).lower().replace(" ", ", ")
        log_plain("Meeting chairs are: " + chairs_readable, trigger.sender)
        log_html_listitem(
            "<span style='font-weight: bold'>Meeting chairs are:</span> %s"
            % chairs_readable,
            trigger.sender,
        )
        bot.say(formatting.bold("Meeting chairs are:") + " " + chairs_readable)
    else:
        bot.say("Only meeting head can set chairs")


# Log action item in the HTML log
@plugin.command("action")
@plugin.example(".action elad will develop a meetbot")
def meetingaction(bot, trigger):
    """
    Log an action in the meeting log.\
    See [meetbot plugin usage]({% link _usage/meetbot-plugin.md %})
    """
    if not is_meeting_running(trigger.sender):
        bot.say("There is no active meeting")
        return
    if not trigger.group(2):
        bot.say(
            "Try `{}action Bob will do something`".format(bot.config.core.help_prefix)
        )
        return
    if not is_chair(trigger.nick, trigger.sender):
        bot.say("Only meeting head or chairs can do that")
        return
    log_plain("ACTION: " + trigger.group(2), trigger.sender)
    log_html_listitem(
        "<span style='font-weight: bold'>Action: </span>" + trigger.group(2),
        trigger.sender,
    )
    meeting_actions[trigger.sender].append(trigger.group(2))
    bot.say(formatting.bold("ACTION:") + " " + trigger.group(2))


@plugin.command("listactions")
@plugin.example(".listactions")
def listactions(bot, trigger):
    """List all the actions in the meeting summary."""
    if not is_meeting_running(trigger.sender):
        bot.say("There is no active meeting")
        return
    for action in meeting_actions[trigger.sender]:
        bot.say(formatting.bold("ACTION:") + " " + action)


# Log agreed item in the HTML log
@plugin.command("agreed")
@plugin.example(".agreed Bowties are cool")
def meetingagreed(bot, trigger):
    """
    Log an agreement in the meeting log.\
    See [meetbot plugin usage]({% link _usage/meetbot-plugin.md %})
    """
    if not is_meeting_running(trigger.sender):
        bot.say("There is no active meeting")
        return
    if not trigger.group(2):
        bot.say("Try `{}agreed Bowties are cool`".format(bot.config.core.help_prefix))
        return
    if not is_chair(trigger.nick, trigger.sender):
        bot.say("Only meeting head or chairs can do that")
        return
    log_plain("AGREED: " + trigger.group(2), trigger.sender)
    log_html_listitem(
        "<span style='font-weight: bold'>Agreed: </span>" + trigger.group(2),
        trigger.sender,
    )
    bot.say(formatting.bold("AGREED:") + " " + trigger.group(2))


# Log link item in the HTML log
@plugin.command("link")
@plugin.example(".link http://example.com")
def meetinglink(bot, trigger):
    """
    Log a link in the meeing log.\
    See [meetbot plugin usage]({% link _usage/meetbot-plugin.md %})
    """
    if not is_meeting_running(trigger.sender):
        bot.say("There is no active meeting")
        return
    if not trigger.group(2):
        bot.say(
            "Try `{}link https://relevant-website.example/`".format(
                bot.config.core.help_prefix
            )
        )
        return
    if not is_chair(trigger.nick, trigger.sender):
        bot.say("Only meeting head or chairs can do that")
        return
    link = trigger.group(2)
    if not link.startswith("http"):
        link = "http://" + link
    try:
        title = find_title(link)
    except Exception:  # TODO: Be specific
        title = ""
    log_plain("LINK: %s [%s]" % (link, title), trigger.sender)
    log_html_listitem('<a href="%s">%s</a>' % (link, title), trigger.sender)
    bot.say(formatting.bold("LINK:") + " " + link)


# Log informational item in the HTML log
@plugin.command("info")
@plugin.example(".info all board members present")
def meetinginfo(bot, trigger):
    """
    Log an informational item in the meeting log.\
    See [meetbot plugin usage]({% link _usage/meetbot-plugin.md %})
    """
    if not is_meeting_running(trigger.sender):
        bot.say("There is no active meeting")
        return
    if not trigger.group(2):
        bot.say(
            "Try `{}info some informative thing`".format(bot.config.core.help_prefix)
        )
        return
    if not is_chair(trigger.nick, trigger.sender):
        bot.say("Only meeting head or chairs can do that")
        return
    log_plain("INFO: " + trigger.group(2), trigger.sender)
    log_html_listitem(trigger.group(2), trigger.sender)
    bot.say(formatting.bold("INFO:") + " " + trigger.group(2))


# called for every single message
# Will log to plain text only
@plugin.rule("(.*)")
@plugin.priority("low")
def log_meeting(bot, trigger):
    if not is_meeting_running(trigger.sender):
        return

    # Handle live prefix changes with cached regex
    if (
        "meetbot_prefix" not in bot.memory or
        bot.memory["meetbot_prefix"] != bot.config.core.prefix
    ):
        commands = [
            "startmeeting",
            "subject",
            "endmeeting",
            "chairs",
            "action",
            "listactions",
            "agreed",
            "link",
            "info",
            "comments",
        ]

        bot.memory["meetbot_command_regex"] = re.compile(
            "{}({})( |$)".format(bot.config.core.prefix, "|".join(commands))
        )
        bot.memory["meetbot_prefix"] = bot.config.core.prefix

    if bot.memory["meetbot_command_regex"].match(trigger):
        return
    log_plain("<" + trigger.nick + "> " + trigger, trigger.sender)


@plugin.command("comment")
@plugin.require_privmsg()
def take_comment(bot, trigger):
    """
    Log a comment, to be shown with other comments when a chair uses .comments.
    Intended to allow commentary from those outside the primary group of people
    in the meeting.

    Used in private message only, as `.comment <#channel> <comment to add>`

    See [meetbot plugin usage]({% link _usage/meetbot-plugin.md %})
    """
    if not trigger.group(4):  # <2 arguments were given
        bot.say(
            "Usage: {}comment <#channel> <comment to add>".format(
                bot.config.core.help_prefix
            )
        )
        return

    target, message = trigger.group(2).split(None, 1)
    target = tools.Identifier(target)
    if not is_meeting_running(target):
        bot.say("There is no active meeting in that channel.")
    else:
        meetings_dict[trigger.group(3)]["comments"].append((trigger.nick, message))
        bot.say(
            "Your comment has been recorded. It will be shown when the "
            "chairs tell me to show the comments."
        )
        bot.say(
            "A new comment has been recorded.", meetings_dict[trigger.group(3)]["head"]
        )


@plugin.command("comments")
def show_comments(bot, trigger):
    """
    Show the comments that have been logged for this meeting with .comment.

    See [meetbot plugin usage]({% link _usage/meetbot-plugin.md %})
    """
    if not is_meeting_running(trigger.sender):
        return
    if not is_chair(trigger.nick, trigger.sender):
        bot.say("Only meeting head or chairs can do that")
        return
    comments = meetings_dict[trigger.sender]["comments"]
    if comments:
        msg = "The following comments were made:"
        bot.say(msg)
        log_plain("<%s> %s" % (bot.nick, msg), trigger.sender)
        for comment in comments:
            msg = "<%s> %s" % comment
            bot.say(msg)
            log_plain("<%s> %s" % (bot.nick, msg), trigger.sender)
        meetings_dict[trigger.sender]["comments"] = []
    else:
        bot.say("No comments have been recorded")
