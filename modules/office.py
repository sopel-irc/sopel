"""
office.py - Phenny Office Module
Author: Michael S. Yanovich, http://opensource.osu.edu/~yanovich

This module states whether someone is in the club office or not.
"""

import web

def office(phenny, input):
    site = web.get("http://web2/~meinwald/office.php")
    lines = site.split('\n')
    phenny.reply(lines[2])
office.commands = ['office']

def office2(phenny, input):
    site = web.get("http://web2/~yanovich/user")
    line = site.split()
    if len(line) < 1:
        phenny.reply("whatsdoom is not in the office.")
    else:
        if line[0] == "paul904":
            phenny.reply("whatsdoom might be in the office.")
        else:
            phenny.reply("whatsdoom is not in the office.")
office2.commands = ['office2']
if __name__ == '__main__':
    print __doc__.strip()
