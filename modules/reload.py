#!/usr/bin/env python
"""
reload.py - Jenni Module Reloader Module
Copyright 2008, Sean B. Palmer, inamidst.com
Licensed under the Eiffel Forum License 2.

http://inamidst.com/phenny/
"""

import sys, os.path, time, imp
import irc
import subprocess

def f_reload(jenni, input):
    """Reloads a module, for use by admins only."""
    if not input.admin: return

    name = input.group(2)
    if name == jenni.config.owner:
        return jenni.reply('What?')

    if (not name) or (name == '*') or (name == 'ALL THE THINGS'):
        jenni.variables = None
        jenni.commands = None
        jenni.setup()
        return jenni.reply('done')

    if not sys.modules.has_key(name):
        return jenni.reply('%s: no such module!' % name)

    # Thanks to moot for prodding me on this
    path = sys.modules[name].__file__
    if path.endswith('.pyc') or path.endswith('.pyo'):
        path = path[:-1]
    if not os.path.isfile(path):
        return jenni.reply('Found %s, but not the source file' % name)

    module = imp.load_source(name, path)
    sys.modules[name] = module
    if hasattr(module, 'setup'):
        module.setup(jenni)

    mtime = os.path.getmtime(module.__file__)
    modified = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(mtime))

    jenni.register(vars(module))
    jenni.bind_commands()

    jenni.reply('%r (version: %s)' % (module, modified))
f_reload.name = 'reload'
f_reload.rule = ('$nick', ['reload'], r'(.+)?')
f_reload.priority = 'low'
f_reload.thread = False

if sys.version_info >= (2, 7):
    def update(jenni, input):
        """Pulls the latest versions of all modules from Git"""
        proc = subprocess.Popen('/usr/bin/git pull',
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,shell=True)
        jenni.reply(proc.communicate()[0])
        
        f_reload(jenni, input)
else:
    def update(jenni, input):
        jenni.say('You need to run me on Python 2.7 to do that.')
update.rule = ('$nick', ['update'], r'(.+)')

if __name__ == '__main__':
    print __doc__.strip()
