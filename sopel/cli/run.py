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

import argparse
import logging
import os
import platform
import signal
import sys
import time

from sopel import bot, config, logger, tools, __version__
from . import utils

# This is in case someone somehow manages to install Sopel on an old version
# of pip (<9.0.0), which doesn't know about `python_requires`, or tries to run
# from source on an unsupported version of Python.
if sys.version_info < (2, 7) or (
    sys.version_info.major >= 3 and sys.version_info < (3, 3)
):
    tools.stderr('Error: Sopel requires Python 2.7+ or 3.3+.')
    sys.exit(1)
if sys.version_info.major == 2:
    now = time.time()
    state = 'has reached end of life'
    if now >= 1588291200:  # 2020-05-01 00:00:00 UTC
        state += ' and will receive no further updates'
    tools.stderr('Warning: Python 2.x %s. Sopel 8.0 will drop support for it.' % state)

LOGGER = logging.getLogger(__name__)

ERR_CODE = 1
"""Error code: program exited with an error"""
ERR_CODE_NO_RESTART = 2
"""Error code: program exited with an error and should not be restarted

This error code is used to prevent systemd from restarting the bot when it
encounters such an error case.
"""


def run(settings, pid_file, daemon=False):
    delay = 20

    # Acts as a welcome message, showing the program and platform version at start
    print_version()
    # Also show the location of the config file used to load settings
    print("\nLoaded config file: {}".format(settings.filename))

    if not settings.core.ca_certs:
        tools.stderr(
            'Could not open CA certificates file. SSL will not work properly!')

    def signal_handler(sig, frame):
        if sig == signal.SIGUSR1 or sig == signal.SIGTERM or sig == signal.SIGINT:
            LOGGER.warning('Got quit signal, shutting down.')
            p.quit('Closing')
        elif sig == signal.SIGUSR2 or sig == signal.SIGILL:
            LOGGER.warning('Got restart signal, shutting down and restarting.')
            p.restart('Restarting')

    # Define empty variable `p` for bot
    p = None
    while True:
        if p and p.hasquit:  # Check if `hasquit` was set for bot during disconnected phase
            break
        try:
            p = bot.Sopel(settings, daemon=daemon)
            if hasattr(signal, 'SIGUSR1'):
                signal.signal(signal.SIGUSR1, signal_handler)
            if hasattr(signal, 'SIGTERM'):
                signal.signal(signal.SIGTERM, signal_handler)
            if hasattr(signal, 'SIGINT'):
                signal.signal(signal.SIGINT, signal_handler)
            if hasattr(signal, 'SIGUSR2'):
                signal.signal(signal.SIGUSR2, signal_handler)
            if hasattr(signal, 'SIGILL'):
                signal.signal(signal.SIGILL, signal_handler)
            p.setup()
        except KeyboardInterrupt:
            break
        except Exception:
            # In that case, there is nothing we can do.
            # If the bot can't setup itself, then it won't run.
            # This is a critical case scenario, where the user should have
            # direct access to the exception traceback right in the console.
            # Besides, we can't know if logging has been set up or not, so
            # we can't rely on that here.
            tools.stderr('Unexpected error in bot setup')
            raise

        try:
            p.run(settings.core.host, int(settings.core.port))
        except KeyboardInterrupt:
            break
        except Exception:
            err_log = logging.getLogger('sopel.exceptions')
            err_log.exception('Critical exception in core')
            err_log.error('----------------------------------------')
            # TODO: This should be handled by command_start
            # All we should need here is a return value, but replacing the
            # os._exit() call below (at the end) broke ^C.
            # This one is much harder to test, so until that one's sorted it
            # isn't worth the risk of trying to remove this one.
            os.unlink(pid_file)
            os._exit(1)

        if not isinstance(delay, int):
            break
        if p.wantsrestart:
            return -1
        if p.hasquit:
            break
        LOGGER.warning('Disconnected. Reconnecting in %s seconds...', delay)
        time.sleep(delay)
    # TODO: This should be handled by command_start
    # All we should need here is a return value, but making this
    # a return makes Sopel hang on ^C after it says "Closed!"
    os.unlink(pid_file)
    os._exit(0)


def add_legacy_options(parser):
    # TL;DR: option -d/--fork is not deprecated.
    # When the legacy action is replaced in Sopel 8, 'start' will become the
    # new default action, with its arguments.
    # The option -d/--fork is used by both actions (start and legacy),
    # and it has the same meaning and behavior, therefore it is not deprecated.
    parser.add_argument("-d", '--fork', action="store_true",
                        dest="daemonize",
                        help="Daemonize Sopel.")
    parser.add_argument("-q", '--quit', action="store_true", dest="quit",
                        help=(
                            "Gracefully quit Sopel "
                            "(deprecated, and will be removed in Sopel 8; "
                            "use ``sopel stop`` instead)"))
    parser.add_argument("-k", '--kill', action="store_true", dest="kill",
                        help=(
                            "Kill Sopel "
                            "(deprecated, and will be removed in Sopel 8; "
                            "use ``sopel stop --kill`` instead)"))
    parser.add_argument("-r", '--restart', action="store_true", dest="restart",
                        help=(
                            "Restart Sopel "
                            "(deprecated, and will be removed in Sopel 8; "
                            "use `sopel restart` instead)"))
    parser.add_argument("-l", '--list', action="store_true",
                        dest="list_configs",
                        help=(
                            "List all config files found"
                            "(deprecated, and will be removed in Sopel 8; "
                            "use ``sopel-config list`` instead)"))
    parser.add_argument('--quiet', action="store_true", dest="quiet",
                        help="Suppress all output")
    parser.add_argument('-w', '--configure-all', action='store_true',
                        dest='wizard',
                        help=(
                            "Run the configuration wizard "
                            "(deprecated, and will be removed in Sopel 8; "
                            "use `sopel configure` instead)"))
    parser.add_argument('--configure-modules', action='store_true',
                        dest='mod_wizard',
                        help=(
                            "Run the configuration wizard, but only for the "
                            "plugin configuration options "
                            "(deprecated, and will be removed in Sopel 8; "
                            "use ``sopel configure --plugins`` instead)"))
    parser.add_argument('-v', action="store_true",
                        dest='version_legacy',
                        help=(
                            "Show version number and exit "
                            "(deprecated, and will be removed in Sopel 8; "
                            "use ``-V/--version`` instead)"))
    parser.add_argument('-V', '--version', action='store_true',
                        dest='version',
                        help='Show version number and exit')


def build_parser():
    """Build an ``argparse.ArgumentParser`` for the bot"""
    parser = argparse.ArgumentParser(description='Sopel IRC Bot',
                                     usage='%(prog)s [options]')
    add_legacy_options(parser)
    utils.add_common_arguments(parser)

    subparsers = parser.add_subparsers(
        title='subcommands',
        description='List of Sopel\'s subcommands',
        dest='action',
        metavar='{start,configure,stop,restart}')

    # manage `legacy` subcommand
    parser_legacy = subparsers.add_parser('legacy')
    add_legacy_options(parser_legacy)
    utils.add_common_arguments(parser_legacy)

    # manage `start` subcommand
    parser_start = subparsers.add_parser(
        'start',
        description='Start a Sopel instance. '
                    'This command requires an existing configuration file '
                    'that can be generated with ``sopel configure``.',
        help='Start a Sopel instance')
    parser_start.add_argument(
        '-d', '--fork',
        dest='daemonize',
        action='store_true',
        default=False,
        help='Run Sopel as a daemon (fork). This bot will safely run in the '
             'background. The instance will be named after the name of the '
             'configuration file used to run it. '
             'To stop it, use ``sopel stop`` (with the same configuration).')
    parser_start.add_argument(
        '--quiet',
        action="store_true",
        dest="quiet",
        help="Suppress all output")
    utils.add_common_arguments(parser_start)

    # manage `configure` subcommand
    parser_configure = subparsers.add_parser(
        'configure',
        description='Run the configuration wizard. It can be used to create '
                    'a new configuration file or to update an existing one.',
        help='Sopel\'s Wizard tool')
    parser_configure.add_argument(
        '--plugins',
        action='store_true',
        default=False,
        dest='plugins',
        help='Check for Sopel plugins that require configuration, and run '
             'their configuration wizards.')
    utils.add_common_arguments(parser_configure)

    # manage `stop` subcommand
    parser_stop = subparsers.add_parser(
        'stop',
        description='Stop a running Sopel instance. '
                    'This command determines the instance to quit by the name '
                    'of the configuration file used ("default", or the one '
                    'from the ``-c``/``--config`` option). '
                    'This command should be used when the bot is running in '
                    'the background from ``sopel start -d``, and should not '
                    'be used when Sopel is managed by a process manager '
                    '(like systemd or supervisor).',
        help='Stop a running Sopel instance')
    parser_stop.add_argument(
        '-k', '--kill',
        action='store_true',
        default=False,
        help='Kill Sopel without a graceful quit')
    parser_stop.add_argument(
        '--quiet',
        action="store_true",
        dest="quiet",
        help="Suppress all output")
    utils.add_common_arguments(parser_stop)

    # manage `restart` subcommand
    parser_restart = subparsers.add_parser(
        'restart',
        description='Restart a running Sopel instance',
        help='Restart a running Sopel instance')
    parser_restart.add_argument(
        '--quiet',
        action="store_true",
        dest="quiet",
        help="Suppress all output")
    utils.add_common_arguments(parser_restart)

    return parser


def check_not_root():
    """Check if root is running the bot.

    It raises a ``RuntimeError`` if the user has root privileges on Linux or
    if it is the ``Administrator`` account on Windows.
    """
    opersystem = platform.system()
    if opersystem in ["Linux", "Darwin"]:
        # Linux/Mac
        if os.getuid() == 0 or os.geteuid() == 0:
            raise RuntimeError('Error: Do not run Sopel with root privileges.')
    elif opersystem in ["Windows"]:
        # Windows
        if os.environ.get("USERNAME") == "Administrator":
            raise RuntimeError('Error: Do not run Sopel as Administrator.')
    else:
        tools.stderr(
            "Warning: %s is an uncommon operating system platform. "
            "Sopel should still work, but please contact Sopel's developers "
            "if you experience issues."
            % opersystem)


def print_version():
    """Print Python version and Sopel version on stdout."""
    py_ver = '%s.%s.%s' % (sys.version_info.major,
                           sys.version_info.minor,
                           sys.version_info.micro)
    print('Sopel %s (running on Python %s)' % (__version__, py_ver))
    print('https://sopel.chat/')


def print_config(configdir):
    """Print list of available configurations from config directory."""
    configs = utils.enumerate_configs(configdir)
    print('Config files in %s:' % configdir)
    configfile = None
    for configfile in configs:
        print('\t%s' % configfile)
    if not configfile:
        print('\tNone found')

    print('-------------------------')


def get_configuration(options):
    """Get or create a configuration object from ``options``.

    :param options: argument parser's options
    :type options: ``argparse.Namespace``
    :return: a configuration object
    :rtype: :class:`sopel.config.Config`

    This may raise a :exc:`sopel.config.ConfigurationError` if the
    configuration file is invalid.

    .. seealso::

       The configuration file is loaded by
       :func:`~sopel.cli.run.utils.load_settings` or created using the
       configuration wizard.

    """
    try:
        settings = utils.load_settings(options)
    except config.ConfigurationNotFound as error:
        print(
            "Welcome to Sopel!\n"
            "I can't seem to find the configuration file, "
            "so let's generate it!\n")
        settings = utils.wizard(error.filename)

    settings._is_daemonized = options.daemonize
    return settings


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
    if options.config and options.config != 'default':
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


def command_start(opts):
    """Start a Sopel instance"""
    # Step One: Get the configuration file and prepare to run
    try:
        config_module = get_configuration(opts)
    except config.ConfigurationError as e:
        tools.stderr(e)
        return ERR_CODE_NO_RESTART

    if config_module.core.not_configured:
        tools.stderr('Bot is not configured, can\'t start')
        return ERR_CODE_NO_RESTART

    # Step Two: Handle process-lifecycle options and manage the PID file
    pid_dir = config_module.core.pid_dir
    pid_file_path = get_pid_filename(opts, pid_dir)
    pid = get_running_pid(pid_file_path)

    if pid is not None and tools.check_pid(pid):
        tools.stderr('There\'s already a Sopel instance running '
                     'with this config file.')
        tools.stderr('Try using either the `sopel stop` '
                     'or the `sopel restart` command.')
        return ERR_CODE

    if opts.daemonize:
        child_pid = os.fork()
        if child_pid != 0:
            return

    with open(pid_file_path, 'w') as pid_file:
        pid_file.write(str(os.getpid()))

    # Step Three: Run Sopel
    ret = run(config_module, pid_file_path)

    # Step Four: Shutdown Clean-Up
    os.unlink(pid_file_path)

    if ret == -1:
        # Restart
        os.execv(sys.executable, ['python'] + sys.argv)
    else:
        # Quit
        return ret


def command_configure(opts):
    """Sopel Configuration Wizard"""
    configpath = utils.find_config(opts.configdir, opts.config)
    if opts.plugins:
        utils.plugins_wizard(configpath)
    else:
        utils.wizard(configpath)


def command_stop(opts):
    """Stop a running Sopel instance"""
    # Get Configuration
    try:
        settings = utils.load_settings(opts)
    except config.ConfigurationNotFound as error:
        tools.stderr('Configuration "%s" not found' % error.filename)
        return ERR_CODE

    if settings.core.not_configured:
        tools.stderr('Sopel is not configured, can\'t stop')
        return ERR_CODE

    # Configure logging
    logger.setup_logging(settings)

    # Get Sopel's PID
    filename = get_pid_filename(opts, settings.core.pid_dir)
    pid = get_running_pid(filename)

    if pid is None or not tools.check_pid(pid):
        tools.stderr('Sopel is not running!')
        return ERR_CODE

    # Stop Sopel
    if opts.kill:
        tools.stderr('Killing the Sopel')
        os.kill(pid, signal.SIGKILL)
        return

    tools.stderr('Signaling Sopel to stop gracefully')
    if hasattr(signal, 'SIGUSR1'):
        os.kill(pid, signal.SIGUSR1)
    else:
        # Windows will not generate SIGTERM itself
        # https://docs.microsoft.com/en-us/cpp/c-runtime-library/reference/signal
        os.kill(pid, signal.SIGTERM)


def command_restart(opts):
    """Restart a running Sopel instance"""
    # Get Configuration
    try:
        settings = utils.load_settings(opts)
    except config.ConfigurationNotFound as error:
        tools.stderr('Configuration "%s" not found' % error.filename)
        return ERR_CODE

    if settings.core.not_configured:
        tools.stderr('Sopel is not configured, can\'t stop')
        return ERR_CODE

    # Configure logging
    logger.setup_logging(settings)

    # Get Sopel's PID
    filename = get_pid_filename(opts, settings.core.pid_dir)
    pid = get_running_pid(filename)

    if pid is None or not tools.check_pid(pid):
        tools.stderr('Sopel is not running!')
        return ERR_CODE

    tools.stderr('Asking Sopel to restart')
    if hasattr(signal, 'SIGUSR2'):
        os.kill(pid, signal.SIGUSR2)
    else:
        # Windows will not generate SIGILL itself
        # https://docs.microsoft.com/en-us/cpp/c-runtime-library/reference/signal
        os.kill(pid, signal.SIGILL)


def command_legacy(opts):
    """Legacy Sopel run script

    The ``legacy`` command manages the old-style ``sopel`` command line tool.
    Most of its features are replaced by the following commands:

    * ``sopel start`` replaces the default behavior (run the bot)
    * ``sopel stop`` replaces the ``--quit/--kill`` options
    * ``sopel restart`` replaces the ``--restart`` option
    * ``sopel configure`` replaces the
      ``-w/--configure-all/--configure-modules`` options

    The ``-v`` option for "version" is deprecated, ``-V/--version`` should be
    used instead.

    .. seealso::

       The github issue `#1471`__ tracks various changes requested for future
       versions of Sopel, some of them related to this legacy command.

       .. __: https://github.com/sopel-irc/sopel/issues/1471

    """
    # Step One: Handle "No config needed" options
    if opts.version:
        print_version()
        return
    elif opts.version_legacy:
        tools.stderr(
            'WARNING: option -v is deprecated; '
            'use `sopel -V/--version` instead')
        print_version()
        return

    configpath = utils.find_config(opts.configdir, opts.config)

    if opts.wizard:
        tools.stderr(
            'WARNING: option -w/--configure-all is deprecated; '
            'use `sopel configure` instead')
        utils.wizard(configpath)
        return

    if opts.mod_wizard:
        tools.stderr(
            'WARNING: option --configure-modules is deprecated; '
            'use `sopel configure --plugins` instead')
        utils.plugins_wizard(configpath)
        return

    if opts.list_configs:
        tools.stderr(
            'WARNING: option --list is deprecated; '
            'use `sopel-config list` instead')
        print_config(opts.configdir)
        return

    # Step Two: Get the configuration file and prepare to run
    try:
        config_module = get_configuration(opts)
    except config.ConfigurationError as e:
        tools.stderr(e)
        return ERR_CODE_NO_RESTART

    if config_module.core.not_configured:
        tools.stderr('Bot is not configured, can\'t start')
        return ERR_CODE_NO_RESTART

    # Step Three: Handle process-lifecycle options and manage the PID file
    pid_dir = config_module.core.pid_dir
    pid_file_path = get_pid_filename(opts, pid_dir)
    old_pid = get_running_pid(pid_file_path)

    if old_pid is not None and tools.check_pid(old_pid):
        if not opts.quit and not opts.kill and not opts.restart:
            tools.stderr(
                'There\'s already a Sopel instance running with this config file')
            tools.stderr(
                'Try using either the `sopel stop` command or the `sopel restart` command')
            return ERR_CODE
        elif opts.kill:
            tools.stderr(
                'WARNING: option -k/--kill is deprecated; '
                'use `sopel stop --kill` instead')
            tools.stderr('Killing the Sopel')
            os.kill(old_pid, signal.SIGKILL)
            return
        elif opts.quit:
            tools.stderr(
                'WARNING: options -q/--quit is deprecated; '
                'use `sopel stop` instead')
            tools.stderr('Signaling Sopel to stop gracefully')
            if hasattr(signal, 'SIGUSR1'):
                os.kill(old_pid, signal.SIGUSR1)
            else:
                # Windows will not generate SIGTERM itself
                # https://docs.microsoft.com/en-us/cpp/c-runtime-library/reference/signal
                os.kill(old_pid, signal.SIGTERM)
            return
        elif opts.restart:
            tools.stderr(
                'WARNING: options --restart is deprecated; '
                'use `sopel restart` instead')
            tools.stderr('Asking Sopel to restart')
            if hasattr(signal, 'SIGUSR2'):
                os.kill(old_pid, signal.SIGUSR2)
            else:
                # Windows will not generate SIGILL itself
                # https://docs.microsoft.com/en-us/cpp/c-runtime-library/reference/signal
                os.kill(old_pid, signal.SIGILL)
            return
    elif opts.kill or opts.quit or opts.restart:
        tools.stderr('Sopel is not running!')
        return ERR_CODE

    if opts.daemonize:
        child_pid = os.fork()
        if child_pid != 0:
            return
    with open(pid_file_path, 'w') as pid_file:
        pid_file.write(str(os.getpid()))

    # Step Four: Initialize and run Sopel
    ret = run(config_module, pid_file_path)
    os.unlink(pid_file_path)
    if ret == -1:
        os.execv(sys.executable, ['python'] + sys.argv)
    else:
        return ret


def main(argv=None):
    """Sopel run script entry point"""
    try:
        # Step One: Parse The Command Line
        parser = build_parser()

        # make sure to have an action first (`legacy` by default)
        # TODO: `start` should be the default in Sopel 8
        argv = argv or sys.argv[1:]
        if not argv:
            argv = ['legacy']
        elif argv[0].startswith('-') and argv[0] not in ['-h', '--help']:
            argv = ['legacy'] + argv

        opts = parser.parse_args(argv)

        # Step Two: "Do not run as root" checks
        try:
            check_not_root()
        except RuntimeError as err:
            tools.stderr('%s' % err)
            return ERR_CODE

        # Step Three: Handle command
        action = getattr(opts, 'action', 'legacy')
        command = {
            'legacy': command_legacy,
            'start': command_start,
            'configure': command_configure,
            'stop': command_stop,
            'restart': command_restart,
        }.get(action)
        return command(opts)
    except KeyboardInterrupt:
        print("\n\nInterrupted")
        return ERR_CODE


if __name__ == '__main__':
    sys.exit(main())
