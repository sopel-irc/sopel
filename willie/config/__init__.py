# coding=utf8
"""
*Availability: 3+ for all functions; attributes may vary.*

The config class is an abstraction class for accessing the active Willie
configuration file.

The Willie config file is divided to sections, and each section contains keys
and values. A section is an attribute of the config class, and is of type
``ConfigSection``. Each section contains the keys as attributes. For example,
if you want to access key example from section test, use
``config.test.example``. Note that the key names are made lower-case by the
parser, regardless of whether they are upper-case in the file.

The ``core`` section will always be present, and contains configuration used by
the Willie core. Modules are allowed to read those, but must not change them.

The config file can store strings, booleans and lists. If you need to store a
number, cast it to ``int()`` when reading.

For backwards compatibility, every key in the core section is an attribute of
the config class as well as of config.core. For new code, always specify the
name of the section, because this behavior might be removed in the future.

Running the ``config.py`` file directly will give the user an interactive
series of dialogs to create the configuration file. This will guide the user
through creating settings for the Willie core, the settings database, and any
modules which have a configuration function.

The configuration function, if used, must be declared with the signature
``configure(config)``. To add options, use ``interactive_add``, ``add_list``
and ``add_option``.
"""
# Copyright 2012, Edward Powell, embolalia.net
# Copyright © 2012, Elad Alfassa <elad@fedoraproject.org>
# Licensed under the Eiffel Forum License 2.

from __future__ import unicode_literals
from __future__ import print_function
from __future__ import absolute_import

from willie.tools import iteritems, stderr
import willie.tools
from willie.tools import get_input
import willie.loader
import os
import sys
try:
    import ConfigParser
except ImportError:
    import configparser as ConfigParser
import willie.config.core_section
from willie.config.types import StaticSection


class ConfigurationError(Exception):
    """ Exception type for configuration errors """

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return 'ConfigurationError: %s' % self.value


class Config(object):
    def __init__(self, filename):
        """Return a configuration object.

        The given filename will be associated with the configuration, and is
        the file which will be written if write() is called. If load is not
        given or True, the configuration object will load the attributes from
        the file at filename.

        A few default values will be set here if they are not defined in the
        config file, or a config file is not loaded. They are documented below.

        """
        self.filename = filename
        """The config object's associated file, as noted above."""
        self.parser = ConfigParser.RawConfigParser(allow_no_value=True)
        self.parser.read(self.filename)
        self.define_section('core', willie.config.core_section.CoreSection)
        self.get = self.parser.get

    @property
    def homedir(self):
        """An alias to config.core.homedir"""
        # Technically it's the other way around, so we can bootstrap filename
        # attributes in the core section, but whatever.
        configured = None
        try:
            configured = self.parser.get('core', 'homedir')
        except ConfigParser.NoOptionError:
            pass
        if configured:
            return configured
        else:
            return os.path.dirname(self.filename)

    def save(self):
        """Save all changes to the config file."""
        cfgfile = open(self.filename, 'w')
        self.parser.write(cfgfile)
        cfgfile.flush()
        cfgfile.close()

    def add_section(self, name):
        """Add a section to the config file.

        Returns ``False`` if already exists.
        """
        try:
            return self.parser.add_section(name)
        except ConfigParser.DuplicateSectionError:
            return False

    def define_section(self, name, cls_):
        """Define the available settings in a section.

        ``cls_`` must be a subclass of ``StaticSection``. If the section has
        already been defined with a different class, ValueError is raised."""
        if not issubclass(cls_, StaticSection):
            raise ValueError("Class must be a subclass of StaticSection.")
        current = getattr(self, name)
        if (not isinstance(current, self.ConfigSection)
                and not current.__class__ == cls_):
            raise ValueError("Can not re-define class for section.")
        setattr(self, name, cls_(self, name))

    class ConfigSection(object):

        """Represents a section of the config file.

        Contains all keys in thesection as attributes.

        """

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

        def get_list(self, name):
            value = getattr(self, name)
            if not value:
                return []
            if isinstance(value, basestring):
                value = value.split(',')
                # Keep the split value, so we don't have to keep doing this
                setattr(self, name, value)
            return value

    def __getattr__(self, name):
        if name in self.parser.sections():
            items = self.parser.items(name)
            section = self.ConfigSection(name, items, self)  # Return a section
            setattr(self, name, section)
            return section
        else:
            raise AttributeError("%r object has no attribute %r"
                                 % (type(self).__name__, name))

    def option(self, question, default=False):
        """Ask "y/n" and return the corresponding boolean answer.

        Show user in terminal a "y/n" prompt, and return true or false based on
        the response. If default is passed as true, the default will be shown
        as ``[y]``, else it will be ``[n]``. ``question`` should be phrased as
        a question, but without a question mark at the end.

        """
        d = 'n'
        if default:
            d = 'y'
        ans = get_input(question + ' (y/n)? [' + d + '] ')
        if not ans:
            ans = d
        return ans.lower() == 'y'

    def _modules(self):
        home = os.getcwd()
        modules_dir = os.path.join(home, 'modules')
        filenames = willie.loader.enumerate_modules(self)
        os.sys.path.insert(0, modules_dir)
        for name, mod_spec in iteritems(filenames):
            path, type_ = mod_spec
            try:
                module, _ = willie.loader.load_module(name, path, type_)
            except Exception as e:
                filename, lineno = willie.tools.get_raising_file_and_line()
                rel_path = os.path.relpath(filename, os.path.dirname(__file__))
                raising_stmt = "%s:%d" % (rel_path, lineno)
                stderr("Error loading %s: %s (%s)" % (name, e, raising_stmt))
            else:
                if hasattr(module, 'configure'):
                    prompt = name + ' module'
                    if module.__doc__:
                        doc = module.__doc__.split('\n', 1)[0]
                        if doc:
                            prompt = doc
                    prompt = 'Configure {} (y/n)? [n]'.format(prompt)
                    do_configure = get_input(prompt)
                    do_configure = do_configure and do_configure.lower() == 'y'
                    if do_configure:
                        module.configure(self)
        self.save()


def _wizard(section, config=None):
    dotdir = os.path.expanduser('~/.willie')
    configpath = os.path.join(dotdir, (config or 'default') + '.cfg')
    if section == 'all':
        _create_config(configpath)
    elif section == 'mod':
        _check_dir(False)
        if not os.path.isfile(configpath):
            print("No config file found." +
                  " Please make one before configuring these options.")
            sys.exit(1)
        config = Config(configpath, True)
        config._modules()


def _check_dir(create=True):
    dotdir = os.path.join(os.path.expanduser('~'), '.willie')
    if not os.path.isdir(dotdir):
        if create:
            print('Creating a config directory at ~/.willie...')
            try:
                os.makedirs(dotdir)
            except Exception as e:
                print('There was a problem creating %s:' % dotdir, file=sys.stderr)
                print('%s, %s' % (e.__class__, str(e)), file=sys.stderr)
                print('Please fix this and then run Willie again.', file=sys.stderr)
                sys.exit(1)
        else:
            print("No config file found. Please make one before configuring these options.")
            sys.exit(1)


def _create_config(configpath):
    _check_dir()
    print("Please answer the following questions" +
          " to create your configuration file:\n")
    try:
        config = Config(configpath, os.path.isfile(configpath))
        willie.config.core_section.configure(config)
        if config.option(
            'Would you like to see if there are any modules'
            ' that need configuring'
        ):
            config._modules()
        config.save()
    except Exception:
        print("Encountered an error while writing the config file." +
              " This shouldn't happen. Check permissions.")
        raise
        sys.exit(1)
    print("Config file written sucessfully!")
