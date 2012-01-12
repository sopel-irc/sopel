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

exp = re.compile(r"(?<!\\)/")

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
    # only do something if there is conversation to work with
    if input.sender not in search_dict or input.nick not in search_dict[input.sender]: return


    global search_dict
    global search_file

    sep = unicode(input.group(1))
    rest = unicode(input.group(2)).split(sep)
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

    for line in reversed(search_dict[input.sender][input.nick]):
        new_phrase = repl(line)
        if new_phrase != line: # we are done
            break

    if new_phrase == line: return # Didn't find anything

    # Save the new "edited" message.
    list = search_dict[input.sender][input.nick]
    list.append(new_phrase)
    search_dict[input.sender][input.nick] = list
    search_file = open("find.txt","w")
    pickle.dump(search_dict, search_file)
    search_file.close()

    # output
    if new_phrase:
        if "ACTION" in new_phrase: # /me
            new_phrase = new_phrase.replace("ACTION", "")
            new_phrase = new_phrase[1:-1]
            phrase = input.nick + new_phrase
            phrase = "\x02" + phrase + "\x02"
        else:
            phrase = input.nick + " meant to say: " + new_phrase
        jenni.say(phrase)

# Matches optional whitespace + 's' + optional whitespace + separator character
findandreplace.rule = r'(?u)\s*s\s*([^\s\w])(.*)' 
#findandreplace.rule = r'(\S+:?)?\s*s\s*([^\s\w])(.*)' # May work for both this and "meant" (requires input.group(i+1))
findandreplace.priority = 'high'

#def meant (jenni, input):
#    # don't bother in PM
#    if not input.sender.startswith('#'): return
#
#    global search_dict
#    global search_file
#    global exp
#
#    text = unicode(input.group())
#    pos = text.find(" ")
#    user = text[:pos - 1]
#    matching = text[pos + 1:]
#
#    if not matching.startswith("s/"):
#        return
#
#    list_pattern = exp.split(matching)
#    try:
#        pattern = list_pattern[1]
#    except:
#        return
#
#    # Make sure the list exists
#    try:
#        replacement = list_pattern[2]
#    except:
#        return
#
#    # If someone does it for a user that hasn't said anything
#    try:
#        current_list = search_dict[input.sender][user]
#    except:
#        return
#    phrase = unicode(current_list[-1])
#
#    if matching.endswith("/g"):
#        new_phrase = freplace(current_list, pattern, replacement, phrase, 0)
#    else:
#        new_phrase = freplace(current_list, pattern, replacement, phrase, 1)
#
#    # Prevents abuse; apparently there is an RFC spec about how servers handle
#    # messages that contain more than 512 characters.
#    if new_phrase:
#        if len(new_phrase) > 512:
#            new_phrase[511:]
#
#    # Save the new "edited" message.
#    list = search_dict[input.sender][user]
#    list.append(new_phrase)
#    search_dict[input.sender][user] = list
#    search_file = open("find.txt","w")
#    pickle.dump(search_dict, search_file)
#    search_file.close()
#
#    # output
#    if new_phrase:
#        #new_phrase = new_phrase.replace("\\", "\\\\")
#        phrase = "%s thinks %s \x02meant:\x02 %s" % (input.nick, user, new_phrase)
#        jenni.say(phrase)
#
#meant.rule = r'\S+(\S|\:)\s.*'
#meant.priority = 'high'

if __name__ == '__main__':
    print __doc__.strip()
