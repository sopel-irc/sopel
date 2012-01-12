#!/usr/bin/env python
"""
find.py - Jenni Spell Checking Module
Copyright 2011, Michael Yanovich, yanovich.net
Licensed under the Eiffel Forum License 2.

More info:
 * Jenni: https://github.com/myano/jenni/
 * Phenny: http://inamidst.com/phenny/

Contributions from: Matt Meinwald and Morgan Goose
This module will fix spelling errors if someone corrects them
using the sed notation (s///) commonly found in vi/vim.
"""

import pickle, time, re
try:
    search_file = open("find.txt","r")
    search_dict = pickle.load(search_file)
except IOError:
    search_dict = dict()

# Create a temporary log of the most recent thing anyone says.
def collectlines(jenni, input):
    # don't log things in PM
    if not input.sender.startswith('#'): return
    global search_dict
    if input.sender not in search_dict:
        search_dict[input.sender] = { }
    try:
        list = search_dict[input.sender][input.nick]
    except:
        list = []
    line = unicode(input.group())
    if line.startswith("s/"):
        return
    else:
        list.append(line)
    del list[:-10]
    search_dict[input.sender][input.nick] = list
    search_file = open("find.txt","w")
    pickle.dump(search_dict, search_file)
    search_file.close()
collectlines.rule = '.*'
collectlines.priority = 'low'

def findandreplace(jenni, input):
    # don't bother in PM
    if not input.sender.startswith('#'): return


    global search_dict
    global search_file

    rnick = input.group(1) or input.nick # Correcting other person vs self.

    # only do something if there is conversation to work with
    if input.sender not in search_dict or rnick not in search_dict[input.sender]: return

    sep = input.group(2)
    rest = input.group(3).split(sep)
    me = False # /me command
    flags = ''
    if len(rest) < 2:
        return # need at least a find and replacement value
    elif len(rest) > 2:
        # Word characters immediately after the second separator
        # are considered flags (only g and i now have meaning)
        flags = re.match(r'\w*',rest[2], re.U).group(0) 
    #else (len == 2) do nothing special

    count = 'g' in flags and -1 or 1 # Replace unlimited times if /g, else once
    if 'i' in flags:
        regex = re.compile(re.escape(rest[0]),re.U|re.I)
        repl = lambda s: re.sub(regex,rest[1],s,count == 1)
    else:
        repl = lambda s: s.replace(rest[0],rest[1],count)

    for line in reversed(search_dict[input.sender][rnick]):
        if line.startswith("\x01ACTION"):
            me = True # /me command
            line = line[8:]
        else:
            me = False
        new_phrase = repl(line)
        if new_phrase != line: # we are done
            break

    if not new_phrase or new_phrase == line: return # Didn't find anything

    # Save the new "edited" message.
    list = search_dict[input.sender][rnick]
    list.append((me and '\x01ACTION ' or '') + new_phrase)
    search_dict[input.sender][rnick] = list
    search_file = open("find.txt","w")
    pickle.dump(search_dict, search_file)
    search_file.close()

    # output
    phrase = input.nick + (input.group(1) and ' thinks ' + rnick or '') + (me and ' ' or " \x02meant\x02 to say: ") + new_phrase
    if me and not input.group(1): phrase = '\x02' + phrase + '\x02'
    jenni.say(phrase)

# Matches optional whitespace + 's' + optional whitespace + separator character
findandreplace.rule = r'(?u)(?:([^\s:]+)[\s:])?\s*s\s*([^\s\w])(.*)' # May work for both this and "meant" (requires input.group(i+1))
findandreplace.priority = 'high'


if __name__ == '__main__':
    print __doc__.strip()
