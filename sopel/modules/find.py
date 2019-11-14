# coding=utf-8
"""
find.py - Sopel Spelling Correction Module
This module will fix spelling errors if someone corrects them
using the sed notation (s///) commonly found in vi/vim.

Copyright 2011, Michael Yanovich, yanovich.net
Copyright 2013, Elsie Powell, embolalia.com
Includes contributions from: dgw, Matt Meinwald, and Morgan Goose
Licensed under the Eiffel Forum License 2.

https://sopel.chat
"""
from __future__ import (
    absolute_import,
    division,
    print_function,
    unicode_literals
)

import re

from sopel.formatting import bold
from sopel.module import echo, priority, rule
from sopel.tools import Identifier, SopelMemory


def setup(bot):
    if 'find_lines' not in bot.memory:
        bot.memory['find_lines'] = SopelMemory()


def shutdown(bot):
    try:
        del bot.memory['find_lines']
    except KeyError:
        pass


@echo
@rule('.*')
@priority('low')
def collectlines(bot, trigger):
    """Create a temporary log of what people say"""
    if trigger.is_privmsg:
        return  # Don't log things in PM

    # Add a log for the channel and nick, if there isn't already one
    if trigger.sender not in bot.memory['find_lines']:
        bot.memory['find_lines'][trigger.sender] = SopelMemory()
    if Identifier(trigger.nick) not in bot.memory['find_lines'][trigger.sender]:
        bot.memory['find_lines'][trigger.sender][Identifier(trigger.nick)] = list()

    # Create a temporary list of the user's lines in a channel
    templist = bot.memory['find_lines'][trigger.sender][Identifier(trigger.nick)]
    line = trigger.group()
    if line.startswith("s/"):  # Don't remember substitutions
        return
    elif line.startswith("\x01ACTION"):  # For /me messages
        line = line[:-1]
        templist.append(line)
    else:
        templist.append(line)

    del templist[:-10]  # Keep the log to 10 lines per person

    bot.memory['find_lines'][trigger.sender][Identifier(trigger.nick)] = templist


# Match nick, s/find/replace/flags. Flags and nick are optional, nick can be
# followed by comma or colon, anything after the first space after the third
# slash is ignored, you can escape slashes with backslashes, and if you want to
# search for an actual backslash followed by an actual slash, you're shit out of
# luck because this is the fucking regex of death as it is.
@rule(r"""(?:
            (\S+)           # Catch a nick in group 1
          [:,]\s+)?         # Followed by colon/comma and whitespace, if given
          s/                # The literal s/
          (                 # Group 2 is the thing to find
            (?:\\/ | [^/])+ # One or more non-slashes or escaped slashes
          )/(               # Group 3 is what to replace with
            (?:\\/ | [^/])* # One or more non-slashes or escaped slashes
          )
          (?:/(\S+))?       # Optional slash, followed by group 4 (flags)
          """)
@priority('high')
def findandreplace(bot, trigger):
    # Don't bother in PM
    if trigger.is_privmsg:
        return

    # Correcting other person vs self.
    rnick = Identifier(trigger.group(1) or trigger.nick)

    search_dict = bot.memory['find_lines']
    # only do something if there is conversation to work with
    if trigger.sender not in search_dict:
        return
    if Identifier(rnick) not in search_dict[trigger.sender]:
        return

    old = trigger.group(2).replace(r'\/', '/')
    new = trigger.group(3).replace(r'\/', '/')
    me = False  # /me command
    flags = (trigger.group(4) or '')

    # If g flag is given, replace all. Otherwise, replace once.
    if 'g' in flags:
        count = -1
    else:
        count = 1

    # repl is a dynamically defined function which performs the substitution.
    # i flag turns off case sensitivity. re.U turns on unicode replacement.
    if 'i' in flags:
        regex = re.compile(re.escape(old), re.U | re.I)

        def repl(s):
            return re.sub(regex, new, s, count == 1)
    else:
        def repl(s):
            return s.replace(old, new, count)

    # Look back through the user's lines in the channel until you find a line
    # where the replacement works
    new_phrase = None
    for line in reversed(search_dict[trigger.sender][rnick]):
        if line.startswith("\x01ACTION"):
            me = True  # /me command
            line = line[8:]
        else:
            me = False
        new_phrase = repl(line)
        if new_phrase != line:  # we are done
            break

    if not new_phrase or new_phrase == line:
        return  # Didn't find anything

    # Save the new "edited" message.
    action = (me and '\x01ACTION ') or ''  # If /me message, prepend \x01ACTION
    templist = search_dict[trigger.sender][rnick]
    templist.append(action + new_phrase)
    search_dict[trigger.sender][rnick] = templist
    bot.memory['find_lines'] = search_dict

    # output
    if not me:
        new_phrase = '%s to say: %s' % (bold('meant'), new_phrase)
    if trigger.group(1):
        phrase = '%s thinks %s %s' % (trigger.nick, rnick, new_phrase)
    else:
        phrase = '%s %s' % (trigger.nick, new_phrase)

    bot.say(phrase)
