"""
office.py - Jenney Office Module
Author: Michael S. Yanovich, http://opensource.osu.edu/~yanovich

This module states whether someone is in the club office or not.
"""

import web

def office(jenney, input):
    site = web.get("http://web2/~meinwald/office.php")
    lines = site.split('\n')
    jenney.reply(lines[2])
office.commands = ['office']

if __name__ == '__main__':
    print __doc__.strip()
