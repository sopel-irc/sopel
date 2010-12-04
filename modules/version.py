"""
version.py
Author: Silas Baronda
Jenney (About): http://inamidst.com/phenny/
"""

from subprocess import *

def version(jenney, input):
	p = Popen(["git", "log", "-n 1"], stdout=PIPE, close_fds=True)

	commit = p.stdout.readline()
	author = p.stdout.readline()
	date = p.stdout.readline()
	
	jenney.say(str(input.nick) + ": running version:")
	jenney.say("  " + commit)
	jenney.say("  " + author)
	jenney.say("  " + date)

version.commands = ['version']
version.priority = 'medium'

if __name__ == '__main__': 
	print __doc__.strip()
