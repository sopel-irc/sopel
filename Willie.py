"""
Willie! either non-existant or the API and bot and whatnot, but doesnt deal
with connection crap. just gets told when stuff is going on by IRCParser (if
Willie is a standalone class. it gets its own copy of the config file in case
anything needs to be changed on the fly, but also a pointer to the factory's
file in case it needs to change anything for all times Willie is run.
"""
import os, imp
from tools import try_print_stderr as stderr

modules_dir = os.path.join(os.getcwd(), 'modules')

## this is the trigger object in the API
class Trigger(object):
    pass
    
## this is the API modules connect to
class Willie(object):
    def __init__(self):
        pass
        #loadmodules()
        
    def PrivMsg(self, trigger): # \
        pass ### handle PMs       |-> might merge
    def ChanMsg(self, trigger): #/
        pass ### handle messages from in a channel
    def JOIN(self, trigger): # \
        pass ### handle JOINs  |-> might merge
    def PART(self, trigger): #/
        pass ### handle PARTs
    def NICK(self, trigger):
        pass
    ## replaces self.protocol.msg with self.msg
    def msg(self, user, message, length=None):
        self.protocol.msg(user, message, length=None)
    
    ## get list of modules to load, post-blacklisting
    def enumerate_modules(self):
        filenames = []
        # if whitelist is disabled or undefined
        if not hasattr(self.config, 'enable') or not self.config.enable:
            # get all the files that are .py files and aren't in blacklist
            blacklist = getattr(self.config, 'exclude', [])
            for fn in os.listdir(modules_dir):
                if fn.endswith('.py') and not fn.startswith('_') and (fn[:-3] not in blacklist):
                    filenames.append(os.path.join(modules_dir, fn))
        # if whitelist is enabled
        else:
            for fn in self.config.enable:
                filenames.append(os.path.join(modules_dir, fn + '.py'))
        # if extra modules are defined
        if hasattr(self.config, 'extra') and self.config.extra is not None:
            for fn in config.extra:
                # if this entry is a file append it
                if os.path.isfile(fn):
                    filenames.append(fn)
                # if this entry is a directory append all .py files
                elif os.path.isdir(fn): 
                    for n in os.listdir(fn):
                        if n.endswith('.py') and not n.startswith('_'):
                            filenames.append(os.path.join(fn, n))
        return filenames
    
    def loadmodules():
        print "Welcome to Willie.\nLoading Modules...\n"
        
        # get modules to load
        errCount = 0
        
        # for each filename in the list of modules to load
        for filename in enumerate_modules():
            name = os.path.basename(filename)[:3] # get module name
            try: module = imp.load_source(name, filename) # try to load it
            except Exception, e:
                # if it fails, tell us why
                errCount += 1
                stderr("Error loading module %s in bot.py: %s" % (name, e))
            # module loaded, check for and run setup
            else:
                try:
                    # if the 
                    if hasattr(self.config, "setup"): module.setup
                    self.register(vars(module))
                    modules.append(name)
                except Exception, e:
                    error_count += 1
                    stderr("Error encountered while setting up module % in bot.py: %s" % (name, e))
                    
            if modules:
                stderr('\n\nRegistered %d modules,' % len(modules)
                stderr('%d modules failed to load\n\n' % error_count)
            else: stderr("Warning: Couldn't find any modules or all of them failed to load")

            self.bind_commands()
    
    ## operates just like in asyncore willie, but broken down
    ## by command to increase speed
    def bind_commands(self):
        commandsets = dict()
        commandsets['PRIVMSG'] = {'high': {}, 'medium': {}, 'low': {}}
        commandsets['JOIN'] = {'high': {}, 'medium': {}, 'low': {}}
        commandsets['PART'] = {'high': {}, 'medium': {}, 'low': {}}
        commandsets['NICK'] = {'high': {}, 'medium': {}, 'low': {}}
        commandsets['DEFAULT'] = {'high': {}, 'medium': {}, 'low': {}}
