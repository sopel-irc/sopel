"""
find.py - Jenni Spell Checking Module
Author: Michael S. Yanovich, http://opensource.osu.edu/
Contributions from: Matt Meinwald and Morgan Goose
About: http://inamidst.com/phenny/

This module will fix spelling errors if someone corrects them.
"""

import pickle, time, re
try:
    search_file = open("search.txt","r")
except IOError:
    search_dict = dict()
else:
    search_dict = pickle.load(search_file)

exp = re.compile(r"(?<!\\)/")

# Create a temporary log of the most recent thing anyone says.
def collectlines(jenni, input):
    global search_dict
    try:
        list = search_dict[input.nick]
    except:
        list=[]
    line = unicode(input.group())
    if line.startswith("s/"):
        return
    else:    
        list.append(line)
    del list[:-20]
    search_dict[input.nick] = list
    search_file = open("search.txt","w")
    pickle.dump(search_dict, search_file)
    search_file.close()
collectlines.rule = '.*'
collectlines.priority = 'low'

def findandreplace(jenni, input):
    global search_dict
    global search_file
    # obtain "old word" and "new word"
    text = unicode(input.group())
    list_pattern = exp.split(text)
    pattern = list_pattern[1]
    try:
        replacement = list_pattern[2]
    except:
        return
    replacement = replacement.replace("\\", "\\\\")
    current_list = search_dict[input.nick]
    phrase = unicode(current_list[-1])
    
    if text.endswith("/g"):
        #new_phrase = unicode(re.sub(pattern, replacement, phrase))
        new_phrase = freplace(current_list, pattern, replacement, phrase, 0)
    else:
        #new_phrase = unicode(re.sub(pattern, replacement, phrase, 1))
        new_phrase = freplace(current_list, pattern, replacement, phrase, 1)
    
    # Prevents abuse; apparently there is an RFC spec about how servers handle
    # messages that contain more than 512 characters.
    if new_phrase:
        if len(new_phrase) > 512:
            new_phrase[511:]
    
    # Save the new "edited" message.
    list = search_dict[input.nick]
    list.append(new_phrase)
    search_dict[input.nick] = list
    search_file = open("search.txt","w")
    pickle.dump(search_dict, search_file)
    search_file.close()

    # output
    if new_phrase:
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
    global search_dict
    global search_file
    global exp

    text = unicode(input.group())
    #text = text.split(": ")
    text = text.split(":",1)
    
    user = text[0]
    matching = unicode(text[1][1:])

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
        current_list = search_dict[user]
    except:
        return
    replacement = replacement.replace("\\", "\\\\")
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
    list = search_dict[input.nick]
    list.append(new_phrase)
    search_dict[input.nick] = list
    search_file = open("search.txt","w")
    pickle.dump(search_dict, search_file)
    search_file.close()

    # output
    if new_phrase:
        phrase = "%s thinks %s \x0300,01meant:\x03 %s" % (input.nick, user, new_phrase)
        jenni.say(phrase)

meant.rule = r'.*\:\s.*'
meant.priority = 'high'

def printable (str):
    from curses.ascii import isprint
    return ''.join([char for char in str if isprint(char)])
    
if __name__ == '__main__':
    print __doc__.strip()
