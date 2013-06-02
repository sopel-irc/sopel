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

from willie.__init__ import run
from willie.config import Config, create_config, ConfigurationError, wizard
import willie.tools as tools
from willie.tools import stderr


homedir = os.path.join(os.path.expanduser('~'), '.willie')


def check_python_version():
    if sys.version_info < (2, 7):
        stderr('Error: Requires Python 2.7 or later. Try python2.7 willie')
        sys.exit(1)


def enumerate_configs(extension='.cfg'):
    configfiles = []
    if os.path.isdir(homedir):
        willie_dotdirfiles = os.listdir(homedir)  # Preferred
        for item in willie_dotdirfiles:
            if item.endswith(extension):
                configfiles.append(item)

    return configfiles


def find_config(name, extension='.cfg'):
    if os.path.isfile(name):
        return name
    configs = enumerate_configs(extension)
    if name in configs or name + extension in configs:
        if name + extension in configs:
            name = name + extension

    return os.path.join(homedir, name)


def main(argv=None):
    global homedir
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
        parser.add_option('--exit-on-error', action="store_true", dest="exit_on_error",
            help="Exit immediately on every error instead of trying to recover")
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
            print 'Config files in ~/.willie:'
            if len(configs[0]) is 0:
                print '\tNone found'
            else:
                for config in configs:
                    print '\t%s' % config
            print '-------------------------'
            return

        config_name = opts.config or 'default'

        configpath = find_config(config_name)
        if not os.path.isfile(configpath):
            print "Welcome to Willie!\nI can't seem to find the configuration file, so let's generate it!\n"
            if not configpath.endswith('.cfg'):
                configpath = configpath + '.cfg'
            create_config(configpath)
            configpath = find_config(config_name)
        try:
            config_module = Config(configpath)
        except ConfigurationError as e:
            stderr(e)
            sys.exit(2)

        if config_module.core.not_configured:
            stderr('Bot is not configured, can\'t start')
            # exit with code 2 to prevent auto restart on fail by systemd
            sys.exit(2)

        if not config_module.has_option('core', 'homedir'):
            config_module.dotdir = homedir
            config_module.homedir = homedir
        else:
            homedir = config_module.core.homedir
            config_module.dotdir = config_module.core.homedir

        if not config_module.core.logdir:
            config_module.core.logdir = os.path.join(homedir, 'logs')
        logfile = os.path.os.path.join(config_module.logdir, 'stdio.log')
        if not os.path.isdir(config_module.logdir):
            os.mkdir(config_module.logdir)

        if opts.exit_on_error:
            config_module.exit_on_error = True
        else:
            config_module.exit_on_error = False

        if opts.quiet is None:
            opts.quiet = False

        sys.stderr = tools.OutputRedirect(logfile, True, opts.quiet)
        sys.stdout = tools.OutputRedirect(logfile, False, opts.quiet)

        #Handle --quit, --kill and saving the PID to file
        pid_dir = config_module.core.pid_dir or homedir
        if opts.config is None:
            pid_file_path = os.path.join(pid_dir, 'willie.pid')
        else:
            basename = os.path.basename(opts.config)
            if basename.endswith('.cfg'):
                basename = basename[:-4]
            pid_file_path = os.path.join(pid_dir, 'willie-%s.pid' % basename)
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
                    stderr('Signaling Willie to stop gracefully')
                    if hasattr(signal, 'SIGUSR1'):
                        os.kill(old_pid, signal.SIGUSR1)
                    else:
                        os.kill(old_pid, signal.SIGTERM)
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
        print "\n\nInterrupted"
        os._exit(1)
if __name__ == '__main__':
    main()
