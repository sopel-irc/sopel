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
import platform

from sopel import run, tools, __version__
from sopel.config import (
    Config,
    _create_config,
    ConfigurationError,
    DEFAULT_HOMEDIR,
    _wizard
)


ERR_CODE = 1
"""Error code: program exited with an error"""
ERR_CODE_NO_RESTART = 2
"""Error code: program exited with an error and should not be restarted

This error code is used to prevent systemd from restarting the bot when it
encounter such error case.
"""


def enumerate_configs(config_dir, extension='.cfg'):
    """List configuration file from ``config_dir`` with ``extension``

    :param str config_dir: path to the configuration directory
    :param str extension: configuration file's extension (default to ``.cfg``)
    :return: a list of configuration filename found in ``config_dir`` with
             the correct ``extension``
    :rtype: list

    Example::

        >>> from sopel import run_script, config
        >>> os.listdir(config.DEFAULT_HOMEDIR)
        ['config.cfg', 'extra.ini', 'module.cfg', 'README']
        >>> run_script.enumerate_configs(config.DEFAULT_HOMEDIR)
        ['config.cfg', 'module.cfg']
        >>> run_script.enumerate_configs(config.DEFAULT_HOMEDIR, '.ini')
        ['extra.ini']

    """
    if not os.path.isdir(config_dir):
        return

    for item in os.listdir(config_dir):
        if item.endswith(extension):
            yield item


def find_config(config_dir, name, extension='.cfg'):
    """Build the absolute path for the given configuration file ``name``

    :param str config_dir: path to the configuration directory
    :param str name: configuration file ``name``
    :param str extension: configuration file's extension (default to ``.cfg``)
    :return: the path of the configuration file, either in the current
             directory or from the ``config_dir`` directory

    This function tries different locations:

    * the current directory
    * the ``config_dir`` directory with the ``extension`` suffix
    * the ``config_dir`` directory without a suffix

    Example::

        >>> from sopel import run_script
        >>> os.listdir()
        ['local.cfg', 'extra.ini']
        >>> os.listdir(config.DEFAULT_HOMEDIR)
        ['config.cfg', 'extra.ini', 'module.cfg', 'README']
        >>> run_script.find_config(config.DEFAULT_HOMEDIR, 'local.cfg')
        'local.cfg'
        >>> run_script.find_config(config.DEFAULT_HOMEDIR, 'local')
        '/home/username/.sopel/local'
        >>> run_script.find_config(config.DEFAULT_HOMEDIR, 'config')
        '/home/username/.sopel/config.cfg'
        >>> run_script.find_config(config.DEFAULT_HOMEDIR, 'extra', '.ini')
        '/home/username/.sopel/extra.ini'

    """
    if os.path.isfile(name):
        return name
    name_ext = name + extension
    for config in enumerate_configs(config_dir, extension):
        if name_ext == config:
            return os.path.join(config_dir, name_ext)

    return os.path.join(config_dir, name)


def build_parser():
    """Build an ``argparse.ArgumentParser`` for the bot"""
    parser = argparse.ArgumentParser(description='Sopel IRC Bot',
                                     usage='%(prog)s [options]')
    parser.add_argument('-c', '--config', metavar='filename',
                        help='use a specific configuration file')
    parser.add_argument("-d", '--fork', action="store_true",
                        dest="daemonize", help="Daemonize Sopel")
    parser.add_argument("-q", '--quit', action="store_true", dest="quit",
                        help="Gracefully quit Sopel")
    parser.add_argument("-k", '--kill', action="store_true", dest="kill",
                        help="Kill Sopel")
    parser.add_argument("-r", '--restart', action="store_true", dest="restart",
                        help="Restart Sopel")
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
    return parser


def check_not_root():

    """Check if root is running the bot.

    It raises a ``RuntimeError`` if the user has root privileges on Linux or
    if it is the ``Administrator`` account on Windows.
    """
    if platform.system() in ["Linux", "Darwin"]:
        # Linux/Mac
        if os.getuid() == 0 or os.geteuid() == 0:
            raise RuntimeError('Error: Do not run Sopel with root privileges.')
    elif platform.system() in ["Windows"]:
        # Windows
        if os.environ.get("USERNAME") == "Administrator":
            raise RuntimeError('Error: Do not run Sopel as Administrator.')
    else:
        raise RuntimeError('Error: Could not detect Operating Sytem Type, or it is unsupported.')


def print_version():
    """Print Python version and Sopel version on stdout."""
    py_ver = '%s.%s.%s' % (sys.version_info.major,
                           sys.version_info.minor,
                           sys.version_info.micro)
    print('Sopel %s (running on python %s)' % (__version__, py_ver))
    print('https://sopel.chat/')


def print_config():
    """Print list of available configurations from default homedir."""
    configs = enumerate_configs(DEFAULT_HOMEDIR)
    print('Config files in %s:' % DEFAULT_HOMEDIR)
    config = None
    for config in configs:
        print('\t%s' % config)
    if not config:
        print('\tNone found')

    print('-------------------------')


def get_configuration(options):
    """Get an instance of configuration from options.

    This may raise a ``sopel.config.ConfigurationError`` if the file is an
    invalid configuration file.
    """
    config_name = options.config or 'default'
    config_path = find_config(DEFAULT_HOMEDIR, config_name)

    if not os.path.isfile(config_path):
        print(
            "Welcome to Sopel!\n"
            "I can't seem to find the configuration file, "
            "so let's generate it!\n")

        if not config_path.endswith('.cfg'):
            config_path = config_path + '.cfg'

        config_path = _create_config(config_path)

    bot_config = Config(config_path)
    bot_config._is_daemonized = options.daemonize

    return bot_config


def get_pid_filename(options, pid_dir):
    """Get the pid file name in ``pid_dir`` from the given ``options``.

    :param options: command line options
    :param str pid_dir: path to the pid directory
    :return: absolute filename of the pid file

    By default, it's ``sopel.pid``, but if a configuration filename is given
    in the ``options``, its basename is used to generate the filename, as:
    ``sopel-{basename}.pid`` instead.
    """
    name = 'sopel.pid'
    if options.config:
        basename = os.path.basename(options.config)
        if basename.endswith('.cfg'):
            basename = basename[:-4]
        name = 'sopel-%s.pid' % basename

    return os.path.abspath(os.path.join(pid_dir, name))


def get_running_pid(filename):
    """Retrieve the PID number from the given ``filename``.

    :param str filename: path to file to read the PID from
    :return: the PID number of a Sopel instance if running, ``None`` otherwise
    :rtype: integer

    This function tries to retrieve a PID number from the given ``filename``,
    as an integer, and returns ``None`` if the file is not found or if the
    content is not an integer.
    """
    if not os.path.isfile(filename):
        return

    with open(filename, 'r') as pid_file:
        try:
            return int(pid_file.read())
        except ValueError:
            pass


def main(argv=None):
    try:
        # Step One: Parse The Command Line
        parser = build_parser()
        opts = parser.parse_args(argv or None)

        # Step Two: "Do not run as root" checks
        try:
            check_not_root()
        except RuntimeError as err:
            stderr('%s' % err)
            return ERR_CODE

        # Step Three: Handle "No config needed" options
        if opts.version:
            print_version()
            return

        if opts.wizard:
            _wizard('all', opts.config)
            return

        if opts.mod_wizard:
            _wizard('mod', opts.config)
            return

        if opts.list_configs:
            print_config()
            return

        # Step Four: Get the configuration file and prepare to run
        try:
            config_module = get_configuration(opts)
        except ConfigurationError as e:
            stderr(e)
            return ERR_CODE_NO_RESTART

        if config_module.core.not_configured:
            stderr('Bot is not configured, can\'t start')
            return ERR_CODE_NO_RESTART

        # Step Five: Manage logfile, stdout and stderr
        logfile = os.path.os.path.join(config_module.core.logdir, 'stdio.log')
        sys.stderr = tools.OutputRedirect(logfile, True, opts.quiet)
        sys.stdout = tools.OutputRedirect(logfile, False, opts.quiet)

        # Step Six: Handle process-lifecycle options and manage the PID file
        pid_dir = config_module.core.pid_dir
        pid_file_path = get_pid_filename(opts, pid_dir)
        old_pid = get_running_pid(pid_file_path)

        if old_pid is not None and tools.check_pid(old_pid):
            if not opts.quit and not opts.kill and not opts.restart:
                stderr('There\'s already a Sopel instance running with this config file')
                stderr('Try using either the --quit, --restart, or --kill option')
                return ERR_CODE
            elif opts.kill:
                stderr('Killing the Sopel')
                os.kill(old_pid, signal.SIGKILL)
                return
            elif opts.quit:
                stderr('Signaling Sopel to stop gracefully')
                if hasattr(signal, 'SIGUSR1'):
                    os.kill(old_pid, signal.SIGUSR1)
                else:
                    # Windows will not generate SIGTERM itself
                    # https://docs.microsoft.com/en-us/cpp/c-runtime-library/reference/signal
                    os.kill(old_pid, signal.SIGTERM)
                return
            elif opts.restart:
                stderr('Asking Sopel to restart')
                if hasattr(signal, 'SIGUSR2'):
                    os.kill(old_pid, signal.SIGUSR2)
                else:
                    # Windows will not generate SIGILL itself
                    # https://docs.microsoft.com/en-us/cpp/c-runtime-library/reference/signal
                    os.kill(old_pid, signal.SIGILL)
                return
        elif opts.kill or opts.quit or opts.restart:
            stderr('Sopel is not running!')
            return ERR_CODE

        if opts.daemonize:
            child_pid = os.fork()
            if child_pid is not 0:
                return
        with open(pid_file_path, 'w') as pid_file:
            pid_file.write(str(os.getpid()))

        # Step Seven: Initialize and run Sopel
        ret = run(config_module, pid_file_path)
        os.unlink(pid_file_path)
        if ret == -1:
            os.execv(sys.executable, ['python'] + sys.argv)
        else:
            return ret

    except KeyboardInterrupt:
        print("\n\nInterrupted")
        return ERR_CODE


if __name__ == '__main__':
    sys.exit(main())
