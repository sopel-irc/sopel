#!/usr/bin/env python
"""
Config - A config class and writing/updating utility for jenni
Copyright 2012, Edward Powell, embolalia.net
Licensed under the Eiffel Forum License 2.

http://dft.ba/-williesource
"""

import os, sys, imp
from textwrap import dedent as trim

class Config(object):
    def __init__(self, filename, load=False):
        self.filename = filename
        if load:
            self = imp.load_source('Config', filename)
        self.core()
        self.settings()
        self.modules()
    
    def write(self):
        f = open(self.filename, 'w')
        
        if self.password:
            password_line = "password = '"+self.password+"'"
        else:
            password_line = "# password = 'example'"
        if self.serverpass:
            serverpass_line = "serverpass = '"+self.serverpass+"'"
        else:
            serverpass_line = "# serverpass = 'example'"
        if self.enable:
            enable_line = "enable = "+str(self.enable)
        else:
            enable_line = "# enable = []"
        extra = self.extra.append(os.getcwd() + '/modules/')
        
        output = trim("""\
        nick = '"""+self.nick+"""'
        host = '"""+self.host+"""'
        port = """+self.port+"""
        channels = """+str(self.channels)+"""
        owner = '"""+self.owner+"""'
        
        # Channel where debug messages should be sent.
        devchan = '"""+self.devchan+"""'
        
        # List of other bots, whose outputs should be ignored
        other_bots = """+str(self.other_bots)+"""

        # password is the NickServ password, serverpass is the server password
        """+password_line+"""
        """+serverpass_line+"""
        
        # The oper name and password, if the bot is allowed to /oper
        """+self.operline+"""

        # These are people who will be able to use admin.py's functions...
        admins = """+str(self.admins)+"""
        # But admin.py is disabled by default, as follows:
        exclude = """+str(self.exclude)+"""

        # If you want to enumerate a list of modules rather than disabling
        # some, use "enable = ['example']", which takes precedent over exclude
        #
        """+enable_line+"""
        
        # Directories to load user modules from
        # e.g. /path/to/my/modules
        extra = """+str(extra)+"""

        # Services to load: maps channel names to white or black lists
        # 
        # ?? Doesn't seem to do anything?
        # external = {
        #    '#liberal': ['!'], # allow all
        #    '#conservative': [], # allow none
        #    '*': ['!'] # default whitelist, allow all
        #}
        """)+(self.settings_chunk+trim("""

        #-----------------------MODULE  SETTINGS-----------------------

        """)+self.modules_chunk)+trim("""
        
        # EOF
        """)
        print >> f, output
        f.close()
    
        
    
    def add(self, attrib, prompt, default=None): #hooray for fucking with attributes
        if hasattr(self, attrib):
            atr = getattr(self, attrib)
            setattr(self, attrib, raw_input(prompt % atr) or atr)
        elif default:
            setattr(self, attrib, raw_input(prompt % default) or default)
        else:
            inp = ''
            while not inp:
                inp = raw_input(prompt)
            setattr(self, attrib, inp)
    def addlist(self, attrib, message, prompt):
        print message
        lst = []
        if hasattr(self, attrib) and self.attrib:
            m = "You currently have "
            for c in self.attrib: m = m + c + ', '
            if self.option(m[:-2]+'. Would you like to keep them', True):
                lst = self.attrib
        mem = raw_input(prompt)
        while mem:
            lst.append(mem)
            mem = raw_input(prompt)
        setattr(self, attrib, lst)
            
    def option(self, question, default=False):
        d = 'n'
        if default: d = 'y'
        ans = raw_input(question+' (y/n)? ['+d+']')
        return (ans == 'y' or ans == 'Y')
    
    def core(self):
        self.add('nick', 'Enter the nickname for your bot:')
        self.add('host', 'Enter the server to connect to:')
        self.add('port', 'Enter the port to connect on [%s]:', '6667')
        
        c='Enter the channels to connect to by default, one at a time. When done, hit enter again.'
        self.addlist('channels', c, 'Channel:')
                
        self.add('owner', "Enter your own IRC name (or that of the bot's owner:")
        self.add('devchan', 'Enter the channel to print debugging messages to [%s]:', 'None')
        
        c="List users you'd like "+self.nick+" to ignore (e.g. other bots), one at a time. Hit enter when done."
        self.addlist('other_bots', c, 'Nick:')
        
        self.add('password', "Enter the bot's NickServ password [%s]:", 'None')
        self.add('serverpass', "Enter the bot's server password [%s]:", 'None')
        
        oper = self.option("Will this bot have IRC Operator privilages")
        if oper:
            opername = raw_input("Operator name:")
            operpass = raw_input("Operator password:")
            self.operline = "Oper = ('"+opername+"', '"+operpass+"')"
        else: self.operline = "# Oper = ('opername', 'operpass')"
        
        #Note that this won't include owner. Will insert that later.

        c='Enter other users who can perform some adminstrative tasks, one at a time. When done, hit enter again.'
        self.addlist('admins', c, 'Nick:')
        
        c=trim("""\
        If you have any modules you do not wish this bot to load, enter them now, one at
        a time. When done, hit enter. (If you'd rather whitelist modules, leave this empty.)""")
        self.addlist('exclude', c, 'Module:')
        
        if not self.exclude:
            wl = self.option("Would you like to create a module whitelist (y/n)? [n]")
            if wl:
                c="Enter the modules to use, one at a time. Hit enter when done."
                self.addlist('enable', c, 'Module:')
        else: self.enable = []
        
        c = trim("""\
        If you'd like to include modules from other directories, enter them one at a
        time, and hit enter again when done.""")
        self.addlist('extra', c, 'Directory:')
        self.extra.append(os.getcwd() + '/modules/')
        
    def settings(self):
        try:
            import settings
            self.settings_chunk = trim(settings.write_config(self))
            self.settings = True
        except: 
            self.settings = False
            self.settings_chunk = trim("""\
            
            # ------------------  USER DATABASE CONFIGURATION  ------------------
            # The user database was not set up at install. Please consult the documentation,
            # or run the configuration utility if you wish to use it.""")
        
        print trim("""
        The configuration utility will now attempt to find modules with their own
        configuration needs.
        """)
    
    def modules(self):
        home = os.getcwd()
        self.modules_chunk = ''
        # This segment largely copied from bot.py
        filenames = []
        if not hasattr(self, 'enable'):
            for fn in os.listdir(os.path.join(home, 'modules')):
                if fn.endswith('.py') and not fn.startswith('_'):
                    filenames.append(os.path.join(home, 'modules', fn))
        else:
            for fn in self.enable:
                filenames.append(os.path.join(home, 'modules', fn + '.py'))

        for fn in self.extra:
            if os.path.isfile(fn):
                filenames.append(fn)
            elif os.path.isdir(fn):
                for n in os.listdir(fn):
                    if n.endswith('.py') and not n.startswith('_'):
                        filenames.append(os.path.join(fn, n))
                        
        for filename in filenames:
            name = os.path.basename(filename)[:-3]
            if name in self.exclude: continue
            # if name in sys.modules:
            #     del sys.modules[name]
            try: module = imp.load_source(name, filename)
            except Exception, e:
                print >> sys.stderr, "Error loading %s: %s (in bot.py)" % (name, e)
            else:
                if hasattr(module, 'config'):
                    chunk = module.config(self)
                    if chunk: self.modules_chunk += trim(chunk)

if __name__ == '__main__':
    config = Config('foo.py')
    config.write()
