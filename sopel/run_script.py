#!/usr/bin/env python2.7
# coding=utf-8
"""
Sopel - An IRC Bot
Copyright 2008, Sean B. Palmer, inamidst.com
Copyright © 2012-2014, Elad Alfassa <elad@fedoraproject.org>
Licensed under the Eiffel Forum License 2.

https://sopel.chat
"""
from __future__ import unicode_literals, absolute_import, print_function, division

import sys
from sopel.tools import stderr

if sys.version_info < (2, 7):
    stderr('Error: Requires Python 2.7 or later. Try python2.7 sopel')
    sys.exit(1)
if sys.version_info.major == 3 and sys.version_info.minor < 3:
    stderr('Error: When running on Python 3, Python 3.3 is required.')
    sys.exit(1)

import os
import argparse
import signal

from sopel.__init__ import run, __version__
from sopel.config import Config, _create_config, ConfigurationError, _wizard
import sopel.tools as tools

homedir = os.path.join(os.path.expanduser('~'), '.sopel')


def enumerate_configs(extension='.cfg'):
    configfiles = []
    if os.path.isdir(homedir):
        sopel_dotdirfiles = os.listdir(homedir)  # Preferred
        for item in sopel_dotdirfiles:
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
        parser = argparse.ArgumentParser(description='Sopel IRC Bot',
                                         usage='%(prog)s [options]')
        parser.add_argument('-c', '--config', metavar='filename',
                            help='use a specific configuration file')
        parser.add_argument("-d", '--fork', action="store_true",
                            dest="daemonize", help="Daemonize sopel")
        parser.add_argument("-q", '--quit', action="store_true", dest="quit",
                            help="Gracefully quit Sopel")
        parser.add_argument("-k", '--kill', action="store_true", dest="kill",
                            help="Kill Sopel")
        parser.add_argument("-l", '--list', action="store_true",
                            dest="list_configs",
                            help="List all config files found")
        parser.add_argument("-m", '--migrate', action="store_true",
                            dest="migrate_configs",
                            help="Migrate config files to the new format")
        parser.add_argument('--quiet', action="store_true", dest="quiet",
                            help="Suppress all output")
        parser.add_argument('-w', '--configure-all', action='store_true',
                            dest='wizard', help='Run the configuration wizard.')
        parser.add_argument('--configure-modules', action='store_true',
                            dest='mod_wizard', help=(
                                'Run the configuration wizard, but only for the '
                                'module configuration options.'))
        parser.add_argument('-v', '--version', action="store_true",
                            dest="version", help="Show version number and exit")
        if argv:
            opts = parser.parse_args(argv)
        else:
            opts = parser.parse_args()

        # Step Two: "Do not run as root" checks.
        try:
            # Linux/Mac
            if os.getuid() == 0 or os.geteuid() == 0:
                stderr('Error: Do not run Sopel with root privileges.')
                sys.exit(1)
        except AttributeError:
            # Windows
            if os.environ.get("USERNAME") == "Administrator":
                stderr('Error: Do not run Sopel as Administrator.')
                sys.exit(1)

        if opts.version:
            py_ver = '%s.%s.%s' % (sys.version_info.major,
                                   sys.version_info.minor,
                                   sys.version_info.micro)
            print('Sopel %s (running on python %s)' % (__version__, py_ver))
            print('https://sopel.chat/')
            return
        elif opts.wizard:
            _wizard('all', opts.config)
            return
        elif opts.mod_wizard:
            _wizard('mod', opts.config)
            return

        if opts.list_configs:
            configs = enumerate_configs()
            print('Config files in ~/.sopel:')
            if len(configs) is 0:
                print('\tNone found')
            else:
                for config in configs:
                    print('\t%s' % config)
            print('-------------------------')
            return

        config_name = opts.config or 'default'

        configpath = find_config(config_name)
        if not os.path.isfile(configpath):
            print("Welcome to Sopel!\nI can't seem to find the configuration file, so let's generate it!\n")
            if not configpath.endswith('.cfg'):
                configpath = configpath + '.cfg'
            _create_config(configpath)
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

        logfile = os.path.os.path.join(config_module.core.logdir, 'stdio.log')

        config_module._is_daemonized = opts.daemonize

        sys.stderr = tools.OutputRedirect(logfile, True, opts.quiet)
        sys.stdout = tools.OutputRedirect(logfile, False, opts.quiet)

        # Handle --quit, --kill and saving the PID to file
        pid_dir = config_module.core.pid_dir
        if opts.config is None:
            pid_file_path = os.path.join(pid_dir, 'sopel.pid')
        else:
            basename = os.path.basename(opts.config)
            if basename.endswith('.cfg'):
                basename = basename[:-4]
            pid_file_path = os.path.join(pid_dir, 'sopel-%s.pid' % basename)
        if os.path.isfile(pid_file_path):
            with open(pid_file_path, 'r') as pid_file:
                try:
                    old_pid = int(pid_file.read())
                except ValueError:
                    old_pid = None
            if old_pid is not None and tools.check_pid(old_pid):
                if not opts.quit and not opts.kill:
                    stderr('There\'s already a Sopel instance running with this config file')
                    stderr('Try using the --quit or the --kill options')
                    sys.exit(1)
                elif opts.kill:
                    stderr('Killing the sopel')
                    os.kill(old_pid, signal.SIGKILL)
                    sys.exit(0)
                elif opts.quit:
                    stderr('Signaling Sopel to stop gracefully')
                    if hasattr(signal, 'SIGUSR1'):
                        os.kill(old_pid, signal.SIGUSR1)
                    else:
                        os.kill(old_pid, signal.SIGTERM)
                    sys.exit(0)
            elif opts.kill or opts.quit:
                stderr('Sopel is not running!')
                sys.exit(1)
        elif opts.quit or opts.kill:
            stderr('Sopel is not running!')
            sys.exit(1)
        if opts.daemonize:
            child_pid = os.fork()
            if child_pid is not 0:
                sys.exit()
        with open(pid_file_path, 'w') as pid_file:
            pid_file.write(str(os.getpid()))

        # Step Five: Initialise And Run sopel
        run(config_module, pid_file_path)
    except KeyboardInterrupt:
        print("\n\nInterrupted")
        os._exit(1)


if __name__ == '__main__':
    main()
