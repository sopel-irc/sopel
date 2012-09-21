#!/usr/bin/env python
# coding=utf-8
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
Copyright © 2012, Elad Alfassa <elad@fedoraproject.org>

Licensed under the Eiffel Forum License 2.

http://willie.dftba.net
"""

import db
import os
import sys
import ConfigParser
import getpass
from textwrap import dedent as trim
from bot import enumerate_modules

class ConfigurationError(Exception):
    """ Exception type for configuration errors """
    def __init__(self, value):  
        self.value = value
    def __str__(self):
        return 'ConfigurationError: %s' % self.value

class Config(object):
    def __init__(self, filename, load=True, ignore_errors=False):
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
        self.parser = ConfigParser.SafeConfigParser(allow_no_value=True)
        if load:
            self.load(False)

            if not ignore_errors:
                #Sanity check for the configuration file:
                if not self.parser.has_section('core'):
                    raise ConfigurationError('Core section missing!')
                if not self.parser.has_option('core', 'nick'):
                    raise ConfigurationError('Bot IRC nick not defined, expected option `nick` in [core] section')
                if not self.parser.has_option('core', 'owner'):
                    raise ConfigurationError('Bot owner not defined, expected option `owner` in [core] section')
                if not self.parser.has_option('core', 'host'):
                    raise ConfigurationError('IRC server address not defined, expceted option `host` in [core] section')

            #Setting defaults:
            if not self.parser.has_option('core', 'port'):
                self.parser.set('core', 'port', '6667')
            if not self.parser.has_option('core', 'user'):
                self.parser.set('core', 'user', 'willie')
            if not self.parser.has_option('core', 'name'):
                self.parser.set('core', 'name', 'Willie Embosbot, http://willie.dftba.net')
            if not self.parser.has_option('core', 'prefix'):
                self.parser.set('core', 'prefix', r'\.')
            if not self.parser.has_option('core', 'admins'):
                self.parser.set('core', 'admins', '')
                
    def save(self):
        """Save all changes to the config file"""
        cfgfile = open(self.filename, 'w')
        self.parser.write(cfgfile)
        
    def load(self, re_init=True):
        """(re)load the config file"""
        if re_init:
            self.parser = ConfigParser.SafeConfigParser(allow_no_value=True)
        self.parser.read(self.filename)
    def add_section(self, name):
        """ Add a section to the config file """
        self.parser.add_section(name)

    class ConfigSection(object):
        """Represents a section of the config file, contains all keys in the section as attributes"""
        def __init__(self, name, items, parent):
            object.__setattr__(self, '_name', name)
            object.__setattr__(self, '_parent', parent)
            for item in items:
                object.__setattr__(self, item[0], item[1].strip())
        
        def __getattr__(self, name):
            return None

        def __setattr__(self, name, value):
            self._parent.parser.set(self._name, name, value)

    def __getattr__(self, name):
        """"""
        if name in self.parser.sections():
            items = self.parser.items(name)
            return self.ConfigSection(name, items, self) #Return a section
        elif self.parser.has_option('core', name):
            return self.parser.get('core', name) #For backwards compatibility
        else:
            raise AttributeError("%r object has no attribute %r" % (type(self).__name__, name))
    
    def write(self):
        """
        Writes the current configuration to the file from which the current
        configuration is derived. Changes made through ``set_attr`` may not be
        properly written by this function.
        """
        pass
        
    
    def interactive_add(self, section, option, prompt, default=None, ispass=False):
        """
        Ask user in terminal for the value to assign to ``option``. If ``default``
        is passed, it will be shown as the default value in the prompt. If
        ``attrib`` is already defined, it will be used instead of ``default``,
        regardless of wheather ``default`` is passed.
        """
        if self.parser.has_option(section, option):
            atr = self.parser.get(section, option)
            if ispass == True:
                value = getpass.getpass(prompt+' [%s]: ' % atr) or atr
                self.parser.set(section, option, value)
            else:
                value = raw_input(prompt+' [%s]: ' % atr) or atr
                self.parser.set(section, option, value)
        elif default:
            if ispass == True:
                value = getpass.getpass(prompt+' [%s]: ' % default) or default
                self.parser.set(section, option, value)
            else:
                value = raw_input(prompt+' [%s]: ' % default) or default
                self.parser.set(section, option, value)
        else:
            inp = ''
            while not inp:
                if ispass == True:
                    value = getpass.getpass(prompt+': ')
                else:
                    value = raw_input(prompt+': ')
            self.parser.set(section, option, value)

    def add_list(self, section, option, message, prompt):
        """
        Ask user in terminal for a list to assign to ``attrib``. If 
        ``self.attrib`` is already defined, show the user the current values and
        ask if the user would like to keep them. If so, additional values can be
        entered. 
        """
        print message
        lst = []
        if self.parser.has_option(section, option) and self.parser.get(section, option):
            m = "You currently have "+ self.parser.get(section, option)
            if self.option(m+'. Would you like to keep them', True):
                lst = self.parser.get(section, option)
        mem = raw_input(prompt)
        while mem:
            lst.append(mem)
            mem = raw_input(prompt)
        self.parser.set(section, option, ','.join(lst))

    def add_option(self, attrib, question, default=False):
        """
        Show user in terminal a "y/n" prompt, and set `attrib` to True or False
        based on the response. If default is passed as true, the default will be
        shown as ``[y]``, else it will be ``[n]``. ``question`` should be phrased
        as a question, but without a question mark at the end. If ``attrib`` is
        already defined, it will be used instead of ``default``, regardless of
        wheather ``default`` is passed.
        """
        if hasattr(self, attrib):
            default = getattr(self, attrib)
        d = 'n'
        if default: d = 'y'
        ans = raw_input(question+' (y/n)? ['+d+']')
        if not ans: ans = d
        if ans == 'y':
            ans = 'yes'
        else:
            ans = 'no'
        setattr(self, attrib, ans)
        
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
        self.interactive_add('core', 'nick', 'Enter the nickname for your bot', 'Willie')
        self.interactive_add('core', 'user', 'Enter the "user" for your bot (the part that comes before the @ in the hostname', 'willie')
        self.interactive_add('core', 'name', 'Enter the "real name" of you bot for WHOIS responses',
                             'Willie Embosbot, http://willie.dftba.net')
        self.interactive_add('core', 'host', 'Enter the server to connect to', 'irc.dftba.net')
        self.interactive_add('core', 'port', 'Enter the port to connect on', '6667')
        self.add_option('core', 'use_ssl', 'Use SSL Secured connection?', False)
        if self.use_ssl:
            self.add_option('core', 'verify_ssl', 'Require trusted SSL certificates?', True)
            if self.verify_ssl:
                self.interactive_add('core', 'ca_certs', 'Enter full path to the CA Certs pem file', '/etc/pki/tls/cert.pem')
        self.interactive_add('core', 'bind_host', 'Bind connection to a specific IP', 'None')
        
        c='Enter the channels to connect to by default, one at a time. When done, hit enter again.'
        self.add_list('core', 'channels', c, 'Channel:')
                
        self.interactive_add('core', 'owner', "Enter your own IRC name (or that of the bot's owner)")
        self.interactive_add('core', 'debug_target', 'Enter the channel to print debugging messages to. If set to stdio, debug messages will be printed to standard output', 'stdio')
        
        self.interactive_add('core', 'verbose', 'Verbosity level. If None, all debug messages will be discarded. Valid options are warning/verbose/none', 'None') #FIXME: Make this a bit more user friendly
        
        c="List users you'd like "+self.nick+" to ignore (e.g. other bots), one at a time. Hit enter when done."
        self.add_list('core', 'other_bots', c, 'Nick:')
        
        self.interactive_add('core', 'password', "Enter the bot's NickServ password", 'None', ispass=True)
        self.interactive_add('core', 'serverpass', "Enter the bot's server password", 'None', ispass=True)
        
        oper = self.option('core', "Will this bot have IRC Operator privilages")
        if oper:#TODO make this do things normally...
            opername = raw_input("Operator name:")
            operpass = getpass.getpass("Operator password:")
            self.operline = "Oper = ('"+opername+"', '"+operpass+"')"
        else: self.operline = "# Oper = ('opername', 'operpass')"
        
        #Note that this won't include owner. Will insert that later.

        c='Enter other users who can perform some adminstrative tasks, one at a time. When done, hit enter again.'
        self.add_list('core', 'admins', c, 'Nick:')
        
        c=trim("""\
        If you have any modules you do not wish this bot to load, enter them now, one at
        a time. When done, hit enter. (If you'd rather whitelist modules, leave this empty.)""")
        self.add_list('core', 'exclude', c, 'Module:')
        
        if not self.exclude:
            wl = self.option('core', "Would you like to create a module whitelist")
            self.enable = []
            if wl:
                c="Enter the modules to use, one at a time. Hit enter when done."
                self.add_list('core', 'enable', c, 'Module:')

        c = trim("""\
        If you'd like to include modules from other directories, enter them one at a
        time, and hit enter again when done.""")
        self.add_list('core', 'extra', c, 'Directory:')
        
    def _db(self):
        db.configure(self)
        self.settings = True #why?
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

