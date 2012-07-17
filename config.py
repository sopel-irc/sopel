#!/usr/bin/env python
"""
*Availability: 3.x+*

The config class is, essentially, a representation of the active jenni config
file. As such, the details of its members depend entirely upon what is written
there.

Running the ``config.py`` file directly will give the user an interactive series
of dialogs to create the configuration file. This will guide the user through
creating settings for the jenni core, the settings database, and any modules
which have a configuration function.

The configuration function, if used, must be declared with the signature
``configure(config)`` and return a string which will be written to the config
file. The ``configure`` function should not write to the file, as this is done
by the utility.
"""
"""
Config - A config class and writing/updating utility for jenni
Copyright 2012, Edward Powell, embolalia.net
Licensed under the Eiffel Forum License 2.

http://dft.ba/-williesource
"""

import os, sys, imp
from textwrap import dedent as trim

class Config(object):
    def __init__(self, filename, load=True):
        """
        Return a configuration object. The given filename will be associated
        with the configuration, and is the file which will be written if write()
        is called. If load is not given or True, the configuration object will
        load the attributes from the file at filename.
        
        A few default values will be set here if they are not defined in the
        config file, or a config file is not loaded. They are documented below.
        """
        self.filename = filename
        """The config object's associated file, as noted above."""
        self.prefix = r'\.'
        """
        This indicates the prefix for commands. (i.e, the . in the .w
        command.) Note that this is used in a regular expression, so regex
        syntax and special characters apply.
        """
        self.name = 'Willie Embosbot, https://github.com/embolalia/jenni'
        """The "real name" used for the bot's whois."""
        self.port = 6667
        """The port to connect on"""
        self.password = None
        """The nickserv password"""
        self.host = 'irc.example.net'
        """
        The host to connect to. This is set to irc.example.net by default,
        which serves as a sanity check to make sure that the bot has been
        configured.
        """
        if load:
            module = imp.load_source('Config', filename)
            for attrib in dir(module):
                setattr(self, attrib, getattr(module, attrib))

    def set_attr(self, attr, value):
        """
        Set attr to value. This will succeed regardless of whether the attribute
        is already set, and regardless of whether the given and current values
        are of the same type.
        """
        setattr(self, attr, value)
    
    def write(self):
        """
        Writes the current configuration to the file from which the current
        configuration is derived. Changes made through ``set_attr`` may not be
        properly written by this function.
        """
        f = open(self.filename, 'w')
        
        if hasattr(self, 'password') and self.password:
            password_line = "password = '"+self.password+"'"
        else:
            password_line = "# password = 'example'"
        if hasattr(self, 'serverpass') and self.serverpass:
            serverpass_line = "serverpass = '"+self.serverpass+"'"
        else:
            serverpass_line = "# serverpass = 'example'"
        if hasattr(self, 'enable') and self.enable:
            enable_line = "enable = "+str(self.enable)
        else:
            enable_line = "# enable = []"
        extra = self.extra.append(os.getcwd() + '/modules/')
        
        output = trim("""\
        nick = '"""+self.nick+"""'
        host = '"""+self.host+"""'
        port = """+str(self.port)+"""
        channels = """+str(self.channels)+"""
        owner = '"""+self.owner+"""'
        
        # Channel where debug messages should be sent.
        debug_target = '"""+self.debug_target+"""'
        
        # Verbosity level for debug messages.
        verbose = '"""+self.verbose+"""'
        
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
    
        
    
    def interactive_add(self, attrib, prompt, default=None):
        """
        Ask user in terminal for the value to assign to ``attrib``. If ``default``
        is passed, it will be shown as the default value in the prompt. If
        ``attrib`` is already defined, it will be used instead of ``default``,
        regardless of wheather ``default`` is passed.
        """
        if hasattr(self, attrib):
            atr = getattr(self, attrib)
            setattr(self, attrib, raw_input(prompt+' [%s]: ' % atr) or atr)
        elif default:
            setattr(self, attrib, raw_input(prompt+' [%s]: ' % default) or default)
        else:
            inp = ''
            while not inp:
                inp = raw_input(prompt+': ')
            setattr(self, attrib, inp)

    def add_list(self, attrib, message, prompt):
        """
        Ask user in terminal for a list to assign to ``attrib``. If 
        ``self.attrib`` is already defined, show the user the current values and
        ask if the user would like to keep them. If so, additional values can be
        entered. 
        """
        print message
        lst = []
        if hasattr(self, attrib) and getattr(self, attrib):
            m = "You currently have "
            for c in getattr(self, attrib): m = m + c + ', '
            if self.option(m[:-2]+'. Would you like to keep them', True):
                lst = getattr(self, attrib)
        mem = raw_input(prompt)
        while mem:
            lst.append(mem)
            mem = raw_input(prompt)
        setattr(self, attrib, lst)
            
    def option(self, question, default=False):
        """
        Show user in terminal a "y/n" prompt, and return true or false based on
        the response. If default is passed as true, the default will be shown as
        ``[y]``, else it will be ``[n]``. ``question`` should be phrased as a
        question, but without a question mark at the end.
        """
        d = 'n'
        if default: d = 'y'
        ans = raw_input(question+' (y/n)? ['+d+']')
        if not ans: ans = d
        return (ans is 'y' or ans is 'Y')
    
    def _core(self):
        self.interactive_add('nick', 'Enter the nickname for your bot', 'jenni')
        self.interactive_add('host', 'Enter the server to connect to', 'irc.dftba.net')
        self.interactive_add('port', 'Enter the port to connect on', '6667')
        
        c='Enter the channels to connect to by default, one at a time. When done, hit enter again.'
        self.add_list('channels', c, 'Channel:')
                
        self.interactive_add('owner', "Enter your own IRC name (or that of the bot's owner)")
        self.interactive_add('debug_target', 'Enter the channel to print debugging messages to. If set to stdio, debug messages will be printed to standard output', 'stdio')
        
        self.interactive_add('verbose', 'Verbosity level. If None, all debug messages will be discarded. Valid options are warning/verbose/none', 'None') #FIXME: Make this a bit more user friendly
        
        c="List users you'd like "+self.nick+" to ignore (e.g. other bots), one at a time. Hit enter when done."
        self.add_list('other_bots', c, 'Nick:')
        
        self.interactive_add('password', "Enter the bot's NickServ password", 'None')
        self.interactive_add('serverpass', "Enter the bot's server password", 'None')
        
        oper = self.option("Will this bot have IRC Operator privilages")
        if oper:
            opername = raw_input("Operator name:")
            operpass = raw_input("Operator password:")
            self.operline = "Oper = ('"+opername+"', '"+operpass+"')"
        else: self.operline = "# Oper = ('opername', 'operpass')"
        
        #Note that this won't include owner. Will insert that later.

        c='Enter other users who can perform some adminstrative tasks, one at a time. When done, hit enter again.'
        self.add_list('admins', c, 'Nick:')
        
        c=trim("""\
        If you have any modules you do not wish this bot to load, enter them now, one at
        a time. When done, hit enter. (If you'd rather whitelist modules, leave this empty.)""")
        self.add_list('exclude', c, 'Module:')
        
        if not self.exclude:
            wl = self.option("Would you like to create a module whitelist")
            if wl:
                c="Enter the modules to use, one at a time. Hit enter when done."
                self.add_list('enable', c, 'Module:')
        else: self.enable = []
        
        c = trim("""\
        If you'd like to include modules from other directories, enter them one at a
        time, and hit enter again when done.""")
        self.add_list('extra', c, 'Directory:')
        
    def _settings(self):
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
    
    def _modules(self):
        home = os.getcwd()
        self.modules_chunk = ''
        # This segment largely copied from bot.py
        filenames = []
        if not self.enable:
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
            print filename
            name = os.path.basename(filename)[:-3]
            if name in self.exclude: continue
            # if name in sys.modules:
            #     del sys.modules[name]
            try: module = imp.load_source(name, filename)
            except Exception, e:
                print >> sys.stderr, "Error loading %s: %s (in config.py)" % (name, e)
            else:
                if hasattr(module, 'configure'):
                    chunk = module.configure(self)
                    if chunk and isinstance(chunk, basestring):
                        self.modules_chunk += trim(chunk)

def _config_names(dotdir, config):
    config = config or 'default'

    def files(d):
        names = os.listdir(d)
        return list(os.path.join(d, fn) for fn in names if fn.endswith('.py'))

    here = os.path.join('.', config)
    if os.path.isfile(here):
        return [here]
    if os.path.isfile(here + '.py'):
        return [here + '.py']
    if os.path.isdir(here):
        return files(here)

    there = os.path.join(dotdir, config)
    if os.path.isfile(there):
        return [there]
    if os.path.isfile(there + '.py'):
        return [there + '.py']
    if os.path.isdir(there):
        return files(there)

    sys.exit(1)

def main(argv=None):
    import optparse
    parser = optparse.OptionParser('%prog [options]')
    parser.add_option('-c', '--config', metavar='fn',
        help='use this configuration file or directory')
    opts, args = parser.parse_args(argv)
    dotdir = os.path.expanduser('~/.jenni')

    if not os.path.isdir(dotdir):
        print 'Creating a config directory at ~/.jenni...'
        try: os.mkdir(dotdir)
        except Exception, e:
            print >> sys.stderr, 'There was a problem creating %s:' % dotdir
            print >> sys.stderr, e.__class__, str(e)
            print >> sys.stderr, 'Please fix this and then run jenni again.'
            sys.exit(1)
    
    configpath = os.path.join(dotdir, (opts.config or 'default')+'.py')
    config = Config(configpath, os.path.isfile(configpath))
    config._core()
    config._settings()
    config._modules()
    config.write()
    
if __name__ == '__main__':
    main()

