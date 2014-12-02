# coding=utf8
"""
find.py - Willie Spelling correction module
Copyright 2011, Michael Yanovich, yanovich.net
Copyright 2013, Edward Powell, embolalia.net
Licensed under the Eiffel Forum License 2.

http://willie.dftba.net

Contributions from: Matt Meinwald, Morgan Goose and Max Gurela
This module will fix spelling errors if someone corrects them
using the sed notation (s///) commonly found in vi/vim.
"""
from __future__ import unicode_literals

import re
from willie.tools import Nick, WillieMemory
from willie.module import rule, priority
from willie.formatting import bold


def setup(bot):
    bot.memory['find_lines'] = WillieMemory()


@rule('.*')
@priority('low')
def collectlines(bot, trigger):
    """Create a temporary log of what people say"""

    # Don't log things in PM
    if trigger.is_privmsg:
        return

    # Add a log for the channel and nick, if there isn't already one
    if trigger.sender not in bot.memory['find_lines']:
        bot.memory['find_lines'][trigger.sender] = WillieMemory()
    if Nick(trigger.nick) not in bot.memory['find_lines'][trigger.sender]:
        bot.memory['find_lines'][trigger.sender][Nick(trigger.nick)] = list()

    # Create a temporary list of the user's lines in a channel
    templist = bot.memory['find_lines'][trigger.sender][Nick(trigger.nick)]
    line = trigger.group()
    if line.startswith("s/"):  # Don't remember substitutions
        return
    elif line.startswith("\x01ACTION"):  # For /me messages
        line = line[:-1]
        templist.append(line)
    else:
        templist.append(line)

    del templist[:-10]  # Keep the log to 10 lines per person

    bot.memory['find_lines'][trigger.sender][Nick(trigger.nick)] = templist


#Match nick, s/find/replace/flags. Flags and nick are optional, nick can be
#followed by comma or colon, anything after the first space after the third
#slash is ignored, you can escape slashes with backslashes.
#
#Slightly modified regex from https://www.azabani.com/2014/02/08/writing-irc-sedbot.html
@rule(r"""^			# start of the message
(?:(\S+)[:,]\s+)? 	# CAPTURE nick
(?:					# BEGIN first sed expression
  s/				#   sed replacement expression delimiter
  (					#   BEGIN needle component
    (?:				#     BEGIN single needle character
      [^\\/]		#       anything that isn't a slash or backslash...
      |\\.			#       ...or any backslash escape
    )*				#     END single needle character, zero or more
  )					#   END needle component
  /					#   slash between needle and replacement
  (					#   BEGIN replacement component
    (?:				#     BEGIN single replacement character
      [^\\/]|\\.	#       escape or non-slash-backslash, as above
    )*				#     END single replacement character, zero or more
  )					#   END replacement component
  (?:/				#   slash between replacement and flags
  (					#   BEGIN flags component
    (?:				#     BEGIN single flag
      [^ ]+			#       any sequence of non-whitespace chars
    )*				#     END single flag, zero or more
  ))?				#   END flags component
)					# END first sed expression
$					# end of the message
          """)
@priority('high')
def findandreplace(bot, trigger):
    # Don't bother in PM
    if trigger.is_privmsg:
        return

    # Correcting other person vs self.
    rnick = Nick(trigger.group(1) or trigger.nick)

    search_dict = bot.memory['find_lines']
    # only do something if there is conversation to work with
    if trigger.sender not in search_dict:
        return
    if Nick(rnick) not in search_dict[trigger.sender]:
        return

    rest = [trigger.group(2), trigger.group(3)]
    find = rest[0]
    replace = rest[1]
    me = False  # /me command
    flags = (trigger.group(4) or '')

    # If g flag is given, replace all. Otherwise, replace once.
    if 'g' in flags:
        count = -1
    else:
        count = 1

    reflags = 0
    if 'i' in flags:
        reflags = re.U | re.I

    try:
        find = re.compile(find, reflags)
    except re.error as e:
        bot.reply(u'That ain\'t valid regex! (%s)' % (e.message))
        return

    # Look back through the user's lines in the channel until you find a line
    # where the replacement works
    for line in reversed(search_dict[trigger.sender][rnick]):
        if line.startswith("\x01ACTION"):
            me = True  # /me command
            line = line[8:]
        else:
            me = False
        new_phrase = find.sub(replace, line, count == 1)
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
