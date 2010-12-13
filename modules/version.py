"""
version.py
Author: Silas Baronda
Jenni (About): http://inamidst.com/phenny/
"""

from subprocess import *

def version(jenni, input):
	p = Popen(["git", "log", "-n 1"], stdout=PIPE, close_fds=True)

	commit = p.stdout.readline()
	author = p.stdout.readline()
	date = p.stdout.readline()
	
	jenni.say(str(input.nick) + ": running version:")
	jenni.say("  " + commit)
	jenni.say("  " + author)
	jenni.say("  " + date)

version.commands = ['version']
version.priority = 'medium'

if __name__ == '__main__': 
	print __doc__.strip()
