#!/usr/bin/env python
"""
*Availability: 3+ for all functions; attributes may vary.*

The config class is, essentially, a representation of the active Willie config
file. As such, the details of its members depend entirely upon what is written
there.

Running the ``config.py`` file directly will give the user an interactive series
of dialogs to create the configuration file. This will guide the user through
creating settings for the Willie core, the settings database, and any modules
which have a configuration function.

The configuration function, if used, must be declared with the signature
``configure(config)`` and return a string which will be written to the config
file. The ``configure`` function should not write to the file, as this is done
by the utility.
"""
"""
Config - A config class and writing/updating utility for Willie
Copyright 2012, Edward Powell, embolalia.net
Licensed under the Eiffel Forum License 2.

http://dft.ba/-williesource
"""

import os, sys, imp
import getpass
from textwrap import dedent as trim
from bot import enumerate_modules


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
        self.user = 'willie'
        """The user/ident the bot will use."""
        self.name = 'Willie Embosbot, http://willie.dftba.net'
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
        if hasattr(self, 'verify_ssl'):
            verify_ssl_line = "verify_ssl = "+str(self.verify_ssl)
        else:
            verify_ssl_line = "# verify_ssl = True"
            
        if hasattr(self, 'ca_certs'):
            ca_cert_line = "ca_certs = '"+str(self.ca_certs)+"'"
        else:
            ca_cert_line = "# ca_certs = '/etc/pki/tls/cert.pem'"
        if self.bind_host is not 'None':
            bind_host_line = "bind_host = '%s'" % self.bind_host
        else:
            bind_host_line = "# bind_host = '0.0.0.0'"
        output = trim("""\
        nick = '"""+self.nick+"""'
        user = '"""+self.user+"""'
        host = '"""+self.host+"""'
        port = """+str(self.port)+"""
        channels = """+str(self.channels)+"""
        owner = '"""+self.owner+"""'
        name = '"""+self.name+"""'
        
        use_ssl = '"""+str(self.use_ssl)+"""'
        """+verify_ssl_line+"""
        """+ca_cert_line+"""
        
        """+bind_host_line+"""

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
    
        
    
    def interactive_add(self, attrib, prompt, default=None, ispass=False):
        """
        Ask user in terminal for the value to assign to ``attrib``. If ``default``
        is passed, it will be shown as the default value in the prompt. If
        ``attrib`` is already defined, it will be used instead of ``default``,
        regardless of wheather ``default`` is passed.
        """
        if hasattr(self, attrib):
            atr = getattr(self, attrib)
            if ispass == True:
                setattr(self, attrib, getpass.getpass(prompt+' [%s]: ' % atr) or atr)
            else:
                setattr(self, attrib, raw_input(prompt+' [%s]: ' % atr) or atr)
        elif default:
            if ispass == True:
                setattr(self, attrib, getpass.getpass(prompt+' [%s]: ' % default) or default)
            else:
                setattr(self, attrib, raw_input(prompt+' [%s]: ' % default) or default)
        else:
            inp = ''
            while not inp:
                if ispass == True:
                    inp = getpass.getpass(prompt+': ')
                else:
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
        self.interactive_add('nick', 'Enter the nickname for your bot', 'Willie')
        self.interactive_add('user', 'Enter the "user" for your bot (the part that comes before the @ in the hostname', 'willie')
        self.interactive_add('name', 'Enter the "real name" of you bot for WHOIS responses',
                             'Willie Embosbot, http://willie.dftba.net')
        self.interactive_add('host', 'Enter the server to connect to', 'irc.dftba.net')
        self.interactive_add('port', 'Enter the port to connect on', '6667')
        self.use_ssl = self.option('Use SSL Secured connection?', False)
        if self.use_ssl:
            self.verify_ssl = self.option('Require trusted SSL certificates?', True)
            if self.verify_ssl:
                self.interactive_add('ca_certs', 'Enter full path to the CA Certs pem file', '/etc/pki/tls/cert.pem')
        self.interactive_add('bind_host', 'Bind connection to a specific IP', 'None')
        
        c='Enter the channels to connect to by default, one at a time. When done, hit enter again.'
        self.add_list('channels', c, 'Channel:')
                
        self.interactive_add('owner', "Enter your own IRC name (or that of the bot's owner)")
        self.interactive_add('debug_target', 'Enter the channel to print debugging messages to. If set to stdio, debug messages will be printed to standard output', 'stdio')
        
        self.interactive_add('verbose', 'Verbosity level. If None, all debug messages will be discarded. Valid options are warning/verbose/none', 'None') #FIXME: Make this a bit more user friendly
        
        c="List users you'd like "+self.nick+" to ignore (e.g. other bots), one at a time. Hit enter when done."
        self.add_list('other_bots', c, 'Nick:')
        
        self.interactive_add('password', "Enter the bot's NickServ password", 'None', ispass=True)
        self.interactive_add('serverpass', "Enter the bot's server password", 'None', ispass=True)
        
        oper = self.option("Will this bot have IRC Operator privilages")
        if oper:
            opername = raw_input("Operator name:")
            operpass = getpass.getpass("Operator password:")
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
            self.enable = []
            if wl:
                c="Enter the modules to use, one at a time. Hit enter when done."
                self.add_list('enable', c, 'Module:')

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
        modules_dir = os.path.join(home, 'modules')
        self.modules_chunk = ''

        filenames = enumerate_modules(self)
        os.sys.path.insert(0,modules_dir) 
        for filename in filenames:
            name = os.path.basename(filename)[:-3]
            if name in self.exclude: continue
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
    dotdir = os.path.expanduser('~/.willie')
    configpath = os.path.join(dotdir, (opts.config or 'default')+'.py')
    create_config(configpath)

def create_config(configpath):
    print "Please answer the following questions to create your configuration file:\n"
    dotdir = os.path.expanduser('~/.willie')
    if not os.path.isdir(dotdir):
        if os.path.isdir(os.path.expanduser('~/.jenni')):
            dotdir = os.path.expanduser('~/.jenni')
        elif os.path.isdir(os.path.expanduser('~/.phenny')):
            dotdir = os.path.expanduser('~/.phenny')
    if not os.path.isdir(dotdir):
        print 'Creating a config directory at ~/.willie...'
        try: os.mkdir(dotdir)
        except Exception, e:
            print >> sys.stderr, 'There was a problem creating %s:' % dotdir
            print >> sys.stderr, e.__class__, str(e)
            print >> sys.stderr, 'Please fix this and then run Willie again.'
            sys.exit(1)
    try:
        config = Config(configpath, os.path.isfile(configpath))
        config._core()
        config._settings()
        config._modules()
        config.write()
    except Exception, e:
        print "Encountered an error while writing the config file. This shouldn't happen. Check permissions."
        raise
        sys.exit(1)
    print "Config file written sucessfully!"

if __name__ == '__main__':
    main()

