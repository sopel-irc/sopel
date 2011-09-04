#!/usr/bin/env python
"""
osu.py - Jenni OSU Module
Copyright 2011, Michael Yanovich, yanovich.net
Licensed under the Eiffel Forum License 2.

More info:
 * Jenni: https://github.com/myano/jenni/
 * Phenny: http://inamidst.com/phenny/

The module contains various functions specific to The Ohio State University.
"""

import web, re

re_find_status = re.compile(r'(?ims)(<br>[\d\w\s\.]+(columbus|canceled)[\d\w\s\.]+(columbus|canceled)[\w\d\s\.]+<br>)')
r_tag = re.compile(r'<(?!!)[^>]+>')

def osu_classes (jenni, input):
    a = web.get("http://ap.osu.edu/emergency/default.aspx")
    msg = ""
    try:
        b = re_find_status.findall(a)
        msg = b[0][0]
        msg = r_tag.sub('', msg)
    except:
        msg = "No information can be found about classes being cancelled at The Ohio State University."
    msg += " - %s" % ("Verify at http://go.osu.edu/emergency or call 614-247-7777.")
    jenni.say(msg)
osu_classes.commands = ['osu']
osu_classes.priority = 'high'

def office(jenni, input):
    try:
        site = web.get("http://opensource.osu.edu/~meinwald/office.php")
    except:
        site = web.get("http://web2/~meinwald/office.php")
    lines = site.split('\n')
    jenni.reply(lines[2])
office.commands = ['office']

if __name__ == '__main__':
    print __doc__.strip()

