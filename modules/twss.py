import urllib2
import re
import os
import sys
from time import sleep

if not os.path.exists("modules/twss.txt"):
    f = open("modules/twss.txt", "w")
    url = "http://www.twssstories.com/best?page="
    first_re = re.compile(r"<p>.+TWSS\.*</p>")
    inner_re = re.compile(u'".+"')

    print "Now creating TWSS database. This will take a few minutes.",
    for page in range(1,148):
        sys.stdout.flush()
        print ".",
        curr_url = url + str(page)
#    print curr_url
        html = urllib2.urlopen(curr_url)
        story_list = first_re.findall(html.read())
        for story in story_list:
            if len(inner_re.findall(story)) > 0:
                lowercase =  inner_re.findall(story)[0].lower()
                f.write(re.sub("[^\w\s]", "", lowercase) + "\n")

    f.close()
    
def say_it(jenni, input):
    with open("modules/twss.txt") as f: 
        quotes = frozenset([line.rstrip() for line in f])
    formatted = input.group(1).lower()
    if re.sub("[^\w\s]", "", formatted) in quotes:
        jenni.say("That's what she said.")
say_it.rule = r"(.*)" 
say_it.priority = "low"
