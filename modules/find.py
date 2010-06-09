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
    del list[:-3]
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
        new_phrase = unicode(re.sub(pattern, replacement, phrase)) 
    else:
        new_phrase = unicode(re.sub(pattern, replacement, phrase, 1))
    # Prevents abuse; apparently there is an RFC spec about how servers handle
    # messages that contain more than 512 characters.
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
    if list[-2] != new_phrase:
       phenny.say(phrase) 
findandreplace.rule = '(s)/.*'
findandreplace.priority = 'high'

if __name__ == '__main__':
    print __doc__.strip()
