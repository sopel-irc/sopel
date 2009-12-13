"""
version.py
Author: Silas Baronda
Phenny (About): http://inamidst.com/phenny/
"""

#
#       version.py
#       
#       Copyright 2009 Michael S. Yanovich
#       
#       This program is free software; you can redistribute it and/or modify
#       it under the terms of the GNU General Public License as published by
#       the Free Software Foundation; either version 3 of the License, or
#       (at your option) any later version.
#       
#       This program is distributed in the hope that it will be useful,
#       but WITHOUT ANY WARRANTY; without even the implied warranty of
#       MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#       GNU General Public License for more details.
#       
#       You should have received a copy of the GNU General Public License
#       along with this program; if not, write to the Free Software
#       Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#       MA 02110-1301, USA.

from subprocess import *

def version(phenny, input):
   p = Popen(["git", "log", "-n 1"], stdout=PIPE, close_fds=True)

   commit = p.stdout.readline()
   author = p.stdout.readline()
   date = p.stdout.readline()
   
   phenny.say(str(input.nick) + ": running version:")
   phenny.say("  " + commit)
   phenny.say("  " + author)
   phenny.say("  " + date)

version.commands = ['version']
version.priority = 'medium'

# vim: set ts=3 sw=3:
