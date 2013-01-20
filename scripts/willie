#!/usr/bin/env python2.7
# coding=utf-8
"""
Willie - An IRC Bot
Copyright 2008, Sean B. Palmer, inamidst.com
Copyright © 2012, Elad Alfassa <elad@fedoraproject.org>
Licensed under the Eiffel Forum License 2.

http://willie.dftba.net
"""

import sys
import os
import optparse
import signal
import imp
try:
    from willie.__init__ import run
    from willie.config import Config, create_config, ConfigurationError, wizard
    import willie.tools as tools
    from willie.tools import stderr, stdout
except ImportError:
    from __init__ import run
    from config import Config, create_config, ConfigurationError
    import tools
    from tools import stderr, stdout

willie_dotdir = os.path.expanduser('~/.willie')
jenni_dotdir = os.path.expanduser('~/.jenni')
phenny_dotdir = os.path.expanduser('~/.phenny')
dotdir = willie_dotdir


def check_python_version():
    if sys.version_info < (2, 7):
        stderr('Error: Requires Python 2.7 or later. Try python2.7 willie')
        sys.exit(1)


def enumerate_configs(extension='.cfg'):
    willie_config = []
    jenni_config = []
    phenny_config = []
    if os.path.isdir(willie_dotdir):
        willie_dotdirfiles = os.listdir(willie_dotdir)  # Preferred
        for item in willie_dotdirfiles:
            if item.endswith(extension):
                willie_config.append(item)
    if os.path.isdir(jenni_dotdir):
        jenni_dotdirfiles = os.listdir(jenni_dotdir)  # Fallback
        for item in jenni_dotdirfiles:
            if item.endswith(extension):
                jenni_config.append(item)
    if os.path.isdir(phenny_dotdir):
        phenny_dotdirfiles = os.listdir(phenny_dotdir)  # Fallback of fallback
        for item in phenny_dotdirfiles:
            willie_config = []
            if item.endswith(extension):
                phenny_config.append(item)

    return (willie_config, jenni_config, phenny_config)


def find_config(name, extension='.cfg'):
    global dotdir
    configs = enumerate_configs(extension)
    if name in configs[0] or name + extension in configs[0]:
        dotdir = willie_dotdir
        if name + extension in configs[0]:
            name = name + extension
    elif name in configs[1] or name + extension in configs[1]:
        dotdir = jenni_dotdir
        if name + extension in configs[1]:
            name = name + extension
    elif name in configs[2] or name + extension in configs[2]:
        dotdir = phenny_dotdir
        if name + extension in configs[2]:
            name = name + extension
    elif not name.endswith(extension):
        name = name + extension

    return os.path.join(dotdir, name)


def main(argv=None):
    # Step One: Parse The Command Line
    try:
        parser = optparse.OptionParser('%prog [options]')
        parser.add_option('-c', '--config', metavar='filename',
            help='use a specific configuration file')
        parser.add_option("-d", '--fork', action="store_true",
            dest="deamonize", help="Deamonize willie")
        parser.add_option("-q", '--quit', action="store_true", dest="quit",
            help="Gracefully quit Willie")
        parser.add_option("-k", '--kill', action="store_true", dest="kill",
            help="Kill Willie")
        parser.add_option("-l", '--list', action="store_true",
            dest="list_configs", help="List all config files found")
        parser.add_option("-m", '--migrate', action="store_true",
            dest="migrate_configs",
            help="Migrate config files to the new format")
        parser.add_option('--quiet', action="store_true", dest="quiet",
            help="Supress all output")
        parser.add_option('-w', '--configure-all', action='store_true',
            dest='wizard', help='Run the configuration wizard.')
        parser.add_option('--configure-modules', action='store_true',
            dest='mod_wizard', help='Run the configuration wizard, but only for the module configuration options.')
        parser.add_option('--configure-database', action='store_true',
            dest='db_wizard', help='Run the configuration wizard, but only for the database configuration options.')
        opts, args = parser.parse_args(argv)

        if opts.wizard:
            wizard('all', opts.config)
            return
        elif opts.mod_wizard:
            wizard('mod', opts.config)
            return
        elif opts.db_wizard:
            wizard('db', opts.config)
            return

        check_python_version()
        if opts.list_configs is not None:
            configs = enumerate_configs()
            stdout('Config files in ~/.willie:')
            if len(configs[0]) is 0:
                stdout('\tNone found')
            else:
                for config in configs[0]:
                    stdout('\t%s' % config)
            stdout('-------------------------')
            stdout('Config files in ~/.jenni:')
            if len(configs[1]) is 0:
                stdout('\tNone found')
            else:
                for config in configs[1]:
                    stdout('\t%s' % config)
            stdout('-------------------------')
            stdout('Config files in ~/.phenny:')
            if len(configs[2]) is 0:
                stdout('\tNone found')
            else:
                for config in configs[2]:
                    stdout('\t%s' % config)
            stdout('-------------------------')
            return

        config_name = opts.config or 'default'

        if opts.migrate_configs is not None:
            configpath = find_config(config_name, '.py')
            new_configpath = configpath[:-2] + 'cfg'
            if os.path.isfile(new_configpath):
                valid_answer = False
                while not valid_answer:
                    answer = raw_input('Warning, new config file already exists. Overwrite? [y/n]')
                    if answer is 'n' or answer == 'no':
                        return
                    elif answer == 'y' or answer == 'yes':
                        valid_answer = True
            old_cfg = imp.load_source('Config', configpath)
            new_cfg = Config(new_configpath, load=False)
            new_cfg.add_section('core')
            for attrib in dir(old_cfg):
                if not attrib.startswith('_'):
                    value = getattr(old_cfg, attrib)
                    if value is None:
                        continue  # Skip NoneTypes
                    if type(value) is list:  # Parse lists
                        parsed_value = ','.join(value)
                    else:
                        parsed_value = str(value)
                    if attrib == 'password':
                        attrib = 'nickserv_password'
                    if attrib == 'serverpass':
                        attrib = 'server_password'
                    setattr(new_cfg.core, attrib, parsed_value)
            new_cfg.save()
            print 'Configuration migrated sucessfully, starting Willie'

        configpath = find_config(config_name)
        if not os.path.isfile(configpath):
            stdout("Welcome to Willie!\nI can't seem to find the configuration file, so let's generate it!\n")
            if not configpath.endswith('.cfg'):
                configpath = configpath + '.cfg'
            create_config(configpath)
            configpath = find_config(config_name)
        try:
            config_module = Config(configpath)
        except ConfigurationError as e:
            stderr(e)
            sys.exit(1)
        config_module.dotdir = dotdir

        if not config_module.core.logdir:
            config_module.core.logdir = os.path.join(dotdir, 'logs')
        logfile = os.path.os.path.join(config_module.logdir, 'stdio.log')
        if not os.path.isdir(config_module.logdir):
            os.mkdir(config_module.logdir)
        if opts.quiet is None:
            opts.quiet = False

        sys.stderr = tools.OutputRedirect(logfile, True, opts.quiet)
        sys.stdout = tools.OutputRedirect(logfile, False, opts.quiet)

        #Handle --quit, --kill and saving the PID to file
        if opts.config is None:
            pid_file_path = os.path.join(dotdir, '.pid-default')
        else:
            pid_file_path = os.path.join(dotdir, '.pid-%s' % opts.config)
        if os.path.isfile(pid_file_path):
            pid_file = open(pid_file_path, 'r')
            old_pid = int(pid_file.read())
            pid_file.close()
            if tools.check_pid(old_pid):
                if opts.quit is None and opts.kill is None:
                    stderr('There\'s already a Willie instance running with this config file')
                    stderr('Try using the --quit or the --kill options')
                    sys.exit(1)
                elif opts.kill:
                    stderr('Killing the willie')
                    os.kill(old_pid, signal.SIGKILL)
                    sys.exit(0)
                elif opts.quit:
                    stderr('Singaling Willie to stop gracefully')
                    os.kill(old_pid, signal.SIGUSR1)
                    sys.exit(0)
            elif not tools.check_pid(old_pid) and (opts.kill or opts.quit):
                stderr('Willie is not running!')
                sys.exit(1)
        elif opts.quit is not None or opts.kill is not None:
            stderr('Willie is not running!')
            sys.exit(1)
        if opts.deamonize is not None:
            child_pid = os.fork()
            if child_pid is not 0:
                sys.exit()
        pid_file = open(pid_file_path, 'w')
        pid_file.write(str(os.getpid()))
        pid_file.close()
        config_module.pid_file_path = pid_file_path

        # Step Five: Initialise And Run willie
        run(config_module)
    except KeyboardInterrupt:
        stdout("\n\nInterrupted")
        os._exit(1)
if __name__ == '__main__':
    main()
