"""
reload.py - Willie Module Reloader Module
Copyright 2008, Sean B. Palmer, inamidst.com
Licensed under the Eiffel Forum License 2.

http://willie.dftba.net
"""

import sys, os.path, time, imp
import willie.irc
import subprocess

def f_reload(willie, trigger):
    """Reloads a module, for use by admins only."""
    if not trigger.admin: return

    name = trigger.group(2)
    if name == willie.config.owner:
        return willie.reply('What?')

    if (not name) or (name == '*') or (name == 'ALL THE THINGS'):
        willie.variables = None
        willie.commands = None
        willie.setup()
        return willie.reply('done')

    if not sys.modules.has_key(name):
        return willie.reply('%s: no such module!' % name)

    # Thanks to moot for prodding me on this
    path = sys.modules[name].__file__
    if path.endswith('.pyc') or path.endswith('.pyo'):
        path = path[:-1]
    if not os.path.isfile(path):
        return willie.reply('Found %s, but not the source file' % name)

    module = imp.load_source(name, path)
    sys.modules[name] = module
    if hasattr(module, 'setup'):
        module.setup(willie)

    mtime = os.path.getmtime(module.__file__)
    modified = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(mtime))

    willie.register(vars(module))
    willie.bind_commands()

    willie.reply('%r (version: %s)' % (module, modified))
f_reload.name = 'reload'
f_reload.rule = ('$nick', ['reload'], r'(.+)?')
f_reload.priority = 'low'
f_reload.thread = False

if sys.version_info >= (2, 7):
    def update(willie, trigger):
        if not trigger.admin: return
        
        """Pulls the latest versions of all modules from Git"""
        proc = subprocess.Popen('/usr/bin/git pull',
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,shell=True)
        willie.reply(proc.communicate()[0])
        
        f_reload(willie, trigger)
else:
    def update(willie, trigger):
        willie.say('You need to run me on Python 2.7 to do that.')
update.rule = ('$nick', ['update'], r'(.+)')

def f_load(willie, trigger):
    """Loads a module, for use by admins only."""
    if not trigger.admin: return

    module_name = trigger.group(2)
    path = ''
    if module_name == willie.config.owner:
        return willie.reply('What?')

    if module_name in sys.modules:
        return willie.reply('Module already loaded, use reload')

    filenames = willie.enumerate_modules(willie.config)
    excluded_modules = getattr(willie.config, 'exclude', [])
    for filename in filenames:
        name = os.path.basename(filename)[:-3]
        if name in excluded_modules: continue
        if name == trigger.group(2):
            path = filename
    if not os.path.isfile(path):
        return willie.reply('Module %s not found' % module_name)

    module = imp.load_source(module_name, path)
    mtime = os.path.getmtime(module.__file__)
    modified = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(mtime))
    if hasattr(module, 'setup'):
        module.setup(willie)
    willie.register(vars(module))
    willie.bind_commands()

    willie.reply('%r (version: %s)' % (module, modified))
f_load.name = 'load'
f_load.rule = ('$nick', ['load'], r'(.+)?')
f_load.priority = 'low'
f_load.thread = False

if __name__ == '__main__':
    print __doc__.strip()
