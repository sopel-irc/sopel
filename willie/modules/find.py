"""
find.py - Willie Spelling correction module
Copyright 2011, Michael Yanovich, yanovich.net
Copyright 2013, Edward Powell, embolalia.net
Licensed under the Eiffel Forum License 2.

http://willie.dftba.net

Contributions from: Matt Meinwald and Morgan Goose
This module will fix spelling errors if someone corrects them
using the sed notation (s///) commonly found in vi/vim.
"""

import re

def setup(willie):
    willie.memory['find_lines'] = dict()
    
def collectlines(willie, trigger):
    """Create a temporary log of what people say"""
    
    # Don't log things in PM
    if not trigger.sender.startswith('#'):
        return

    # Add a log for the channel and nick, if there isn't already one
    if trigger.sender not in willie.memory['find_lines']:
        willie.memory['find_lines'][trigger.sender] = dict()
    if trigger.nick not in willie.memory['find_lines'][trigger.sender]:
        willie.memory['find_lines'][trigger.sender][trigger.nick] = list()

    # Create a temporary list of the user's lines in a channel
    templist = willie.memory['find_lines'][trigger.sender][trigger.nick]
    line = trigger.group()
    if line.startswith("s/"): # Don't remember substitutions
        return
    elif line.startswith("\x01ACTION"): # For /me messages
        line = line[:-1]
        templist.append(line)
    else:
        templist.append(line)

    del templist[:-10] # Keep the log to 10 lines per person
    
    willie.memory['find_lines'][trigger.sender][trigger.nick] = templist
collectlines.rule = r'.*'
collectlines.priority = 'low'


def findandreplace(willie, trigger):
    # Don't bother in PM
    if not trigger.sender.startswith('#'): return

    rnick = trigger.group(1) or trigger.nick # Correcting other person vs self.

    search_dict = willie.memory['find_lines']
    # only do something if there is conversation to work with
    if trigger.sender not in search_dict:
        return
    if rnick not in search_dict[trigger.sender]:
        return

    sep = trigger.group(2)
    rest = trigger.group(3).split(sep)
    me = False # /me command
    flags = ''
    
    # Account for if extra flags are given (just g and i for now), or a search
    # and substitution pattern aren't given.
    if len(rest) < 2:
        return
    elif len(rest) > 2:
        # Word characters immediately after the second separator
        # are considered flags (only g and i now have meaning)
        flags = re.match(r'\w*',rest[2], re.U).group(0)
    
    # If g flag is given, replace all. Otherwise, replace once.
    if 'g' in flags:
        count = -1
    else:
        count = 1
    
    # repl is a lambda function which performs the substitution. i flag turns
    # off case sensitivity. re.U turns on unicode replacement.
    if 'i' in flags:
        regex = re.compile(re.escape(rest[0]),re.U|re.I)
        repl = lambda s: re.sub(regex,rest[1],s,count == 1)
    else:
        repl = lambda s: s.replace(rest[0],rest[1],count)

    # Look back through the user's lines in the channel until you find a line
    # where the replacement works
    for line in reversed(search_dict[trigger.sender][rnick]):
        if line.startswith("\x01ACTION"):
            me = True # /me command
            line = line[8:]
        else:
            me = False
        new_phrase = repl(line)
        if new_phrase != line: # we are done
            break

    if not new_phrase or new_phrase == line:
        return # Didn't find anything

    # Save the new "edited" message.
    action = (me and '\x01ACTION ') or '' # If /me message, prepend \x01ACTION
    templist = search_dict[trigger.sender][rnick]
    templist.append(action + new_phrase)
    search_dict[trigger.sender][rnick] = templist
    willie.memory['find_lines'] = search_dict

    # output
    if not me:
        new_phrase = '\x02meant\x02 to say: ' + new_phrase
    if trigger.group(1):
        phrase = '%s thinks %s %s' % (trigger.nick, rnick, new_phrase)
    else:
        phrase = '%s %s' % (trigger.nick, new_phrase)

    willie.say(phrase)

# Matches optional whitespace + 's' + optional whitespace + separator character
findandreplace.rule = r'(?u)(?:([^\s:]+)[\s:])?\s*s\s*([^\s\w])(.*)' # May work for both this and "meant" (requires trigger.group(i+1))
findandreplace.priority = 'high'


