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

    global search_dict
    global search_file
    # obtain "old word" and "new word"
    text = unicode(input.group())
    list_pattern = exp.split(text)
    pattern = list_pattern[1]
    try:
        replacement = list_pattern[2]
    except: return
    try:
        current_list = search_dict[input.sender][input.nick]
    except: return # no nick found in this room, fail silently
    phrase = unicode(current_list[-1])

    if text.endswith("/g"):
        new_phrase = freplace(current_list, pattern, replacement, phrase, 0)
    else:
        new_phrase = freplace(current_list, pattern, replacement, phrase, 1)

    # Prevents abuse; apparently there is an RFC spec about how servers handle
    # messages that contain more than 512 characters.
    if new_phrase:
        if len(new_phrase) > 512:
            new_phrase[511:]

    # Save the new "edited" message.
    list = search_dict[input.sender][input.nick]
    list.append(new_phrase)
    search_dict[input.sender][input.nick] = list
    search_file = open("find.txt","w")
    pickle.dump(search_dict, search_file)
    search_file.close()

    # output
    if new_phrase:
        new_phrase = new_phrase.replace("\\", "\\\\")
        if "ACTION" in new_phrase:
            new_phrase = new_phrase.replace("ACTION", "")
            new_phrase = new_phrase[1:-1]
            phrase = input.nick + new_phrase
            phrase = "\x0300,01" + phrase
        else:
            phrase = input.nick + " meant to say: " + new_phrase
        jenni.say(phrase)
findandreplace.rule = r'(s)/.*'
findandreplace.priority = 'high'

def freplace(list, pattern, replacement, phrase, flag):
    i = 0
    while i <= len(list):
        i += 1
        k = -i
        if len(list) > i:
            phrase_new = unicode(list[k])
            if flag == 0:
                sample = unicode(re.sub(pattern, replacement, phrase_new))
            elif flag == 1:
                sample = unicode(re.sub(pattern, replacement, phrase_new, 1))

            if sample != phrase_new:
                return sample
                break

def meant (jenni, input):
    # don't bother in PM
    if not input.sender.startswith('#'): return

    global search_dict
    global search_file
    global exp

    text = unicode(input.group())
    pos = text.find(" ")
    user = text[:pos - 1]
    matching = text[pos + 1:]

    if not matching.startswith("s/"):
        return

    list_pattern = exp.split(matching)
    try:
        pattern = list_pattern[1]
    except:
        return

    # Make sure the list exists
    try:
        replacement = list_pattern[2]
    except:
        return

    # If someone does it for a user that hasn't said anything
    try:
        current_list = search_dict[input.sender][user]
    except:
        return
    phrase = unicode(current_list[-1])

    if matching.endswith("/g"):
        new_phrase = freplace(current_list, pattern, replacement, phrase, 0)
    else:
        new_phrase = freplace(current_list, pattern, replacement, phrase, 1)

    # Prevents abuse; apparently there is an RFC spec about how servers handle
    # messages that contain more than 512 characters.
    if new_phrase:
        if len(new_phrase) > 512:
            new_phrase[511:]

    # Save the new "edited" message.
    list = search_dict[input.sender][user]
    list.append(new_phrase)
    search_dict[input.sender][user] = list
    search_file = open("find.txt","w")
    pickle.dump(search_dict, search_file)
    search_file.close()

    # output
    if new_phrase:
        new_phrase = new_phrase.replace("\\", "\\\\")
        phrase = "%s thinks %s \x02meant:\x02 %s" % (input.nick, user, new_phrase)
        jenni.say(phrase)

meant.rule = r'\S+(\S|\:)\s.*'
meant.priority = 'high'

if __name__ == '__main__':
    print __doc__.strip()
