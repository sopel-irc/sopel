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

import os, re


def give_me_unicode(obj, encoding="utf-8"):
    if isinstance(obj, basestring):
        if not isinstance(obj, unicode):
            obj = unicode(obj, encoding)
    return obj

def load_db():
    """ load lines from find.txt to search_dict """
    if not os.path.isfile("find.txt"):
        f = open("find.txt", "w")
        f.write("#test,yano,foobar\n")
        f.close()
    search_file = open("find.txt", "r")
    lines = search_file.readlines()
    search_file.close()
    search_dict = dict()
    for line in lines:
        line = give_me_unicode(line)
        a = line.replace(r'\n', '')
        new = a.split(r',')
        if len(new) < 3: continue
        channel = new[0]
        nick = new[1]
        if len(new) < 2: continue
        if channel not in search_dict:
            search_dict[channel] = dict()
        if nick not in search_dict[channel]:
            search_dict[channel][nick] = list()
        if len(new) > 3:
            result = ",".join(new[2:])
            result = result.replace('\n','')
        elif len(new) == 3:
            result = new[-1]
            if len(result) > 0:
                result = result[:-1]
        if result:
            search_dict[channel][nick].append(result)
    return search_dict

def save_db(search_dict):
    """ save search_dict to find.txt """
    search_file = open("find.txt", "w")
    for channel in search_dict:
        if channel is not "":
            for nick in search_dict[channel]:
                for line in search_dict[channel][nick]:
                    channel_utf = (channel).encode("utf-8")
                    search_file.write(channel)
                    search_file.write(",")
                    nick = (nick).encode("utf-8")
                    search_file.write(nick)
                    search_file.write(",")
                    line_utf = (line).encode("utf-8")
                    search_file.write(line_utf)
                    search_file.write("\n")
    search_file.close()

# Create a temporary log of the most recent thing anyone says.
def collectlines(jenni, input):
    # don't log things in PM
    channel = (input.sender).encode("utf-8")
    nick = (input.nick).encode("utf-8")
    if not channel.startswith('#'): return
    search_dict = load_db()
    if channel not in search_dict:
        search_dict[channel] = dict()
    if nick not in search_dict[channel]:
        search_dict[channel][nick] = list()
    templist = search_dict[channel][nick]
    line = input.group()
    if line.startswith("s/"):
        return
    elif line.startswith("\x01ACTION"):
        line = line[:-1]
        templist.append(line)
    else:
        templist.append(line)
    del templist[:-10]
    search_dict[channel][nick] = templist
    save_db(search_dict)
collectlines.rule = r'.*'
collectlines.priority = 'low'

def findandreplace(jenni, input):
    # don't bother in PM
    channel = (input.sender).encode("utf-8")
    nick = (input.nick).encode("utf-8")

    if not channel.startswith('#'): return

    search_dict = load_db()

    rnick = input.group(1) or nick # Correcting other person vs self.

    # only do something if there is conversation to work with
    if channel not in search_dict or rnick not in search_dict[channel]: return

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

    for line in reversed(search_dict[channel][rnick]):
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
    templist = search_dict[channel][rnick]
    templist.append((me and '\x01ACTION ' or '') + new_phrase)
    search_dict[channel][rnick] = templist
    save_db(search_dict)

    # output
    phrase = nick + (input.group(1) and ' thinks ' + rnick or '') + (me and ' ' or " \x02meant\x02 to say: ") + new_phrase
    if me and not input.group(1): phrase = '\x02' + phrase + '\x02'
    jenni.say(phrase)

# Matches optional whitespace + 's' + optional whitespace + separator character
findandreplace.rule = r'(?u)(?:([^\s:]+)[\s:])?\s*s\s*([^\s\w])(.*)' # May work for both this and "meant" (requires input.group(i+1))
findandreplace.priority = 'high'
findandreplace.rate = 30


if __name__ == '__main__':
    print __doc__.strip()
