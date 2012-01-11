#!/usr/bin/env python
"""
git.py - Jenni Github Module
Copyright 2012, Dimitri Molenaars http://tyrope.nl/
Licensed under the Eiffel Forum License 2.

More info:
 * Jenni: https://github.com/myano/jenni/
 * Phenny: http://inamidst.com/phenny/

This module will parse any command , spitting out a random http://www.fmylife.com/ quote.
"""

import re, urllib2

def issue(jenni, input):
    #Grab info from rscript (code re-used from ytinfo)

    #this is the curl command that should be executed.
    curl = 'curl -u \''+input.gitUser+':'+input.gitPassword+'\' -H "Content-Type: application/json" -X POST -d \'{"title":"'+input.group(1)+'", "body":"'+input.group(3)+'"}\' https://api.github.com/repos/embolalia/jenni/issues'

issue.rule = '\.issue ([^~]+)( ~ )([^.]+)'

if __name__ == '__main__':
    print __doc__.strip()