#!/usr/bin/env python
"""
countdown.py - Jenni Countdown Module
Copyright 2011, Michael Yanovich, yanovich.net
Licensed under the Eiffel Forum License 2.

More info:
 * Jenni: https://github.com/myano/jenni/
 * Phenny: http://inamidst.com/phenny/
"""

import datetime

def generic_countdown(jenni, input):
    """ .countdown <year> <month> <day> - displays a countdown to a given date. """
    try:
        text = input.group(2).split()
    except:
        jenni.say("Please use correct format: .countdown 2012 12 21")
    if text[0].isdigit() and text[1].isdigit() and text[2].isdigit() and len(text) == 3:
        diff = datetime.datetime(int(text[0]), int(text[1]), int(text[2])) - datetime.datetime.today()
        jenni.say(str(diff.days) + "-days " +  str(diff.seconds/60/60) + "-hours " +  str(diff.seconds/60 - diff.seconds/60/60 * 60) + "-minutes until " + text[0] + " " + text[1] + " " + text[2])
    else:
        jenni.say("Please use correct format: .countdown 2012 12 21")
generic_countdown.commands = ['countdown']
generic_countdown.priority = 'low'


if __name__ == '__main__':
    print __doc__.strip()
