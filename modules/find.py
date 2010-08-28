"""
find.py - Phenny Spell Checking Module
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
def collectlines(phenny, input):
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
    del list[:-10]
    search_dict[input.nick] = list
    search_file = open("search.txt","w")
    pickle.dump(search_dict, search_file)
    search_file.close()
collectlines.rule = '.*'
collectlines.priority = 'low'

def findandreplace(phenny, input):
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
    current_list = search_dict[input.nick]
    phrase = unicode(current_list[-1])
    if text.endswith("/g"):
        #new_phrase = unicode(re.sub(pattern, replacement, phrase))
        new_phrase = replace_wg(current_list, pattern, replacement, phrase)
    else:
        #new_phrase = unicode(re.sub(pattern, replacement, phrase, 1))
        new_phrase = replace_wog(current_list, pattern, replacement, phrase)
    
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
    phrase = str(input.nick) + " meant to say: " + new_phrase
    phenny.say(phrase)
findandreplace.rule = '(s)/.*'
findandreplace.priority = 'high'

def replace_wg(list, pattern, replacement, phrase):
    i = 0
    while i <= len(list):
        i += 1
        k = -i
        if len(list) > i:
            phrase_new = unicode(list[k])
            sample = unicode(re.sub(pattern, replacement, phrase_new))
            if sample != phrase_new:
                return sample
                break

def replace_wog(list, pattern, replacement, phrase):
    i = 0
    while i <= len(list):
        i += 1
        k = -i
        if len(list) > i:
            phrase_new = unicode(list[k])
            sample = unicode(re.sub(pattern, replacement, phrase_new, 1))
            if sample != phrase_new:
                return sample
                break

def meant (phenny, input):
    global search_dict
    global search_file
    global exp

    text = unicode(input.group())
    #text = text.split(": ")
    text = text.split(":",1)
    
    user = text[0]
    matching = text[1][1:]

    if str(matching).startswith("http://"):
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
    phrase = unicode(current_list[-1])
    if matching.endswith("/g"):
        #new_phrase = unicode(re.sub(pattern, replacement, phrase))
        new_phrase = replace_wg(current_list, pattern, replacement, phrase)
    else:
        #new_phrase = unicode(re.sub(pattern, replacement, phrase, 1))
        new_phrase = replace_wog(current_list, pattern, replacement, phrase)

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
        phrase = str(input.nick) + " thinks " + str(user) + " meant: " + str(new_phrase)
        phenny.say(phrase)

meant.rule = r'.*\:\s.*'
meant.priority = 'high'
    
if __name__ == '__main__':
    print __doc__.strip()
