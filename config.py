#!/usr/bin/env python
# coding=utf-8
"""
*Availability: 3+ for all functions; attributes may vary.*

The config class is an abstraction class for accessing the active Willie configuration file.

The Willie config file is divided to sections, each section contains keys and values.
A section is an attribute of the config class, and thus it is of the type ``ConfigSection``.
Each sections contains the keys as attributes, for example, if you want to access key example from section test, use
``config.example.test``

The ``core`` section will always be presnet, and contains configuration used by the Willie core. Modules are allowed to read those, but must not change them.

The config file can store strings, booleans and lists. If you need to store a number, cast it to ``int()`` when reading.

For backwards compatibility, every key in the core section is an attribute of the config class as well as of config.core.
For new code, always specify the name of the section, because this behavior might be removed in the future.

Running the ``config.py`` file directly will give the user an interactive series
of dialogs to create the configuration file. This will guide the user through
creating settings for the Willie core, the settings database, and any modules
which have a configuration function.

The configuration function, if used, must be declared with the signature
``configure(config)``. To add options, use ``interactive_add``, ``add_list`` and ``add_option``.
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
import imp
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
        self.parser = ConfigParser.RawConfigParser(allow_no_value=True)
        if load:
            self.parser.read(self.filename)

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
        else:
            self.parser.add_section('core')

    def save(self):
        """Save all changes to the config file"""
        cfgfile = open(self.filename, 'w')
        self.parser.write(cfgfile)

    def add_section(self, name):
        """ Add a section to the config file, returns ``False`` if already exists"""
        try:
            return self.parser.add_section(name)
        except ConfigParser.DuplicateSectionError:
            return False

    def has_option(self, section, name):
        """ Check if section ``name`` exists """
        return self.parser.has_option(section, name)

    class ConfigSection(object):
        """Represents a section of the config file, contains all keys in the section as attributes"""
        def __init__(self, name, items, parent):
            object.__setattr__(self, '_name', name)
            object.__setattr__(self, '_parent', parent)
            for item in items:
                value = item[1].strip()
                if not value.lower() == 'none':
                    if value.lower() == 'false':
                        value = False
                    object.__setattr__(self, item[0], value)
        
        def __getattr__(self, name):
            return None

        def __setattr__(self, name, value):
            object.__setattr__(self, name, value)
            if type(value) is list:
                value = ','.join(value)
            self._parent.parser.set(self._name, name, value)

    def __getattr__(self, name):
        """"""
        if name in self.parser.sections():
            items = self.parser.items(name)
            section = self.ConfigSection(name, items, self) #Return a section
            setattr(self, name, section)
            return section
        elif self.parser.has_option('core', name):
            return self.parser.get('core', name) #For backwards compatibility
        else:
            raise AttributeError("%r object has no attribute %r" % (type(self).__name__, name))


    def interactive_add(self, section, option, prompt, default=None, ispass=False):
        """
        Ask user in terminal for the value to assign to ``option`` under ``section``. If ``default``
        is passed, it will be shown as the default value in the prompt. If
        ``option`` is already defined in ``section``, it will be used instead of ``default``,
        regardless of wheather ``default`` is passed.
        """
        if not self.parser.has_section(section):
            self.parser.add_section(section)
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
            value = ''
            while not value:
                if ispass == True:
                    value = getpass.getpass(prompt+': ')
                else:
                    value = raw_input(prompt+': ')
            self.parser.set(section, option, value)

    def add_list(self, section, option, message, prompt):
        """
        Ask user in terminal for a list to assign to ``option``. If 
        ``option`` is already defined under ``section``, show the user the current values and
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

    def add_option(self, section, option, question, default=False):
        """
        Show user in terminal a "y/n" prompt, and set `option` to True or False
        based on the response. If default is passed as true, the default will be
        shown as ``[y]``, else it will be ``[n]``. ``question`` should be phrased
        as a question, but without a question mark at the end. If ``option`` is
        already defined, it will be used instead of ``default``, regardless of
        wheather ``default`` is passed.
        """
        if self.parser.has_option(section, option):
            default = self.parser.getboolean(section, option)
        answer = self.option(question, default)
        self.parser.set(section, option, str(answer))
        
    def option(self, question, default=False):
        """
        Show user in terminal a "y/n" prompt, and return true or false based on
        the response. If default is passed as true, the default will be shown as
        ``[y]``, else it will be ``[n]``. ``question`` should be phrased as a
        question, but without a question mark at the end.
        """
        d = 'n'
        if default: 
            d = 'y'
        ans = raw_input(question+' (y/n)? ['+d+']')
        if not ans: 
            ans = d
        return (ans is 'y' or ans is 'Y')
    
    def _core(self):
        self.interactive_add('core', 'nick', 'Enter the nickname for your bot', 'Willie')
        self.interactive_add('core', 'user', 'Enter the "user" for your bot (the part that comes before the @ in the hostname', 'willie')
        self.interactive_add('core', 'name', 'Enter the "real name" of you bot for WHOIS responses',
                             'Willie Embosbot, http://willie.dftba.net')
        self.interactive_add('core', 'host', 'Enter the server to connect to', 'irc.dftba.net')
        self.interactive_add('core', 'port', 'Enter the port to connect on', '6667')
        self.add_option('core', 'use_ssl', 'Use SSL Secured connection?', False)
        if self.parser.get('core', 'use_ssl') == 'True':
            self.add_option('core', 'verify_ssl', 'Require trusted SSL certificates?', True)
            if self.parser.get('core', 'verify_ssl') == 'True':
                self.interactive_add('core', 'ca_certs', 'Enter full path to the CA Certs pem file', '/etc/pki/tls/cert.pem')
        self.interactive_add('core', 'bind_host', 'Bind connection to a specific IP', 'None')
        
        c='Enter the channels to connect to by default, one at a time. When done, hit enter again.'
        self.add_list('core', 'channels', c, 'Channel:')
                
        self.interactive_add('core', 'owner', "Enter your own IRC name (or that of the bot's owner)")
        self.interactive_add('core', 'debug_target', 'Enter the channel to print debugging messages to. If set to stdio, debug messages will be printed to standard output', 'stdio')
        
        self.interactive_add('core', 'verbose', 'Verbosity level. If None, all debug messages will be discarded. Valid options are warning/verbose/none', 'None') #FIXME: Make this a bit more user friendly
        
        c="List users you'd like "+self.nick+" to ignore (e.g. other bots), one at a time. Hit enter when done."
        self.add_list('core', 'other_bots', c, 'Nick:')
        
        self.interactive_add('core', 'nickserv_password', "Enter the bot's NickServ password", 'None', ispass=True)
        self.interactive_add('core', 'server_password', "Enter the bot's server password", 'None', ispass=True)
        
        oper = self.option("Will this bot have IRC Operator privilages")
        if oper:
            self.interactive_add('core', 'oper_name', "Operator name:")
            self.interactive_add('core', 'oper_pass', "Operator password:", ispass=True)
            


        c='Enter other users who can perform some adminstrative tasks, one at a time. When done, hit enter again.'
        self.add_list('core', 'admins', c, 'Nick:')
        
        c=trim("""\
        If you have any modules you do not wish this bot to load, enter them now, one at
        a time. When done, hit enter. (If you'd rather whitelist modules, leave this empty.)""")
        self.add_list('core', 'exclude', c, 'Module:')
        
        if not self.exclude:
            wl = self.option("Would you like to create a module whitelist")
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
        print trim("""
        The configuration utility will now attempt to find modules with their own
        configuration needs.
        """)
    
    def _modules(self):
        home = os.getcwd()
        modules_dir = os.path.join(home, 'modules')
        filenames = enumerate_modules(self)
        os.sys.path.insert(0,modules_dir) 
        for filename in filenames:
            name = os.path.basename(filename)[:-3]
            if name in self.exclude:
                continue
            try:
                module = imp.load_source(name, filename)
            except Exception, e:
                print >> sys.stderr, "Error loading %s: %s (in config.py)" % (name, e)
            else:
                if hasattr(module, 'configure'):
                    module.configure(self)


def main(argv=None):
    import optparse
    parser = optparse.OptionParser('%prog [options]')
    parser.add_option('-c', '--config', metavar='fn',
        help='use this configuration file or directory')
    opts, args = parser.parse_args(argv)
    dotdir = os.path.expanduser('~/.willie')
    configpath = os.path.join(dotdir, (opts.config or 'default')+'.cfg')
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
        config._db()
        config._modules()
        config.save()
    except Exception, e:
        print "Encountered an error while writing the config file. This shouldn't happen. Check permissions."
        raise
        sys.exit(1)
    print "Config file written sucessfully!"

if __name__ == '__main__':
    main()

