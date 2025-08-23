"""
Sopel - An IRC Bot
Copyright 2008, Sean B. Palmer, inamidst.com
Copyright © 2012-2014, Elad Alfassa <elad@fedoraproject.org>
Licensed under the Eiffel Forum License 2.

https://sopel.chat
"""
from __future__ import annotations

import argparse
import logging
import os
import platform
import signal
import sys
import time

from sopel import __version__, bot, config, logger

from . import utils


# This is in case someone somehow manages to install Sopel on an old version
# of pip (<9.0.0), which doesn't know about `python_requires`, or tries to run
# from source on an unsupported version of Python.
if sys.version_info < (3, 8):
    utils.stderr('Error: Sopel requires Python 3.8+.')
    sys.exit(1)

LOGGER = logging.getLogger(__name__)

ERR_CODE = 1
"""Error code: program exited with an error"""
ERR_CODE_NO_RESTART = 2
"""Error code: program exited with an error and should not be restarted

This error code is used to prevent systemd from restarting the bot when it
encounters such an error case.
"""


def run(settings, pid_file, daemon=False):
    """Run the bot with these ``settings``.

    :param settings: settings with which to run the bot
    :type settings: :class:`sopel.config.Config`
    :param str pid_file: path to the bot's PID file
    :param bool daemon: tell if the bot should be run as a daemon
    """
    delay = 20

    # Acts as a welcome message, showing the program and platform version at start
    print_version()
    # Also show the location of the config file used to load settings
    print("\nLoaded config file: {}".format(settings.filename))

    # Define empty variable `p` for bot
    p = None
    while True:
        if p and p.hasquit:  # Check if `hasquit` was set for bot during disconnected phase
            break
        try:
            p = bot.Sopel(settings, daemon=daemon)
            p.setup()
        except KeyboardInterrupt:
            utils.stderr('Bot setup interrupted')
            break
        except Exception:
            # In that case, there is nothing we can do.
            # If the bot can't setup itself, then it won't run.
            # This is a critical case scenario, where the user should have
            # direct access to the exception traceback right in the console.
            # Besides, we can't know if logging has been set up or not, so
            # we can't rely on that here.
            utils.stderr('Unexpected error in bot setup')
            raise

        try:
            p.run(settings.core.host, int(settings.core.port))
        except KeyboardInterrupt:
            break
        except Exception:
            err_log = logging.getLogger('sopel.exceptions')
            err_log.exception('Critical exception in core')
            err_log.error('----------------------------------------')
            return ERR_CODE

        if p.wantsrestart:
            return -1
        if p.hasquit:
            return 0

        LOGGER.warning('Disconnected. Reconnecting in %s seconds...', delay)
        time.sleep(delay)


def build_parser(prog: str = 'sopel') -> argparse.ArgumentParser:
    """Build an argument parser for the bot.

    :return: the argument parser
    :rtype: :class:`argparse.ArgumentParser`
    """
    parser = argparse.ArgumentParser(
        prog=prog,
        description='Sopel IRC Bot',
    )

    parser.add_argument('-V', '--version', action='store_true',
                        dest='version',
                        help='Show version number and exit')

    subparsers = parser.add_subparsers(
        title='subcommands',
        description='List of Sopel\'s subcommands',
        dest='action',
        metavar='{start,configure,stop,restart}')

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
    utils.add_common_arguments(parser_stop)

    # manage `restart` subcommand
    parser_restart = subparsers.add_parser(
        'restart',
        description='Restart a running Sopel instance',
        help='Restart a running Sopel instance')
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
        utils.stderr(
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


def get_configuration(options):
    """Get or create a configuration object from ``options``.

    :param options: argument parser's options
    :type options: :class:`argparse.Namespace`
    :return: a configuration object
    :rtype: :class:`sopel.config.Config`

    This may raise a :exc:`sopel.config.ConfigurationError` if the
    configuration file is invalid.

    .. seealso::

       The configuration file is loaded by
       :func:`~sopel.cli.run.utils.load_settings`

    """
    try:
        settings = utils.load_settings(options)
    except config.ConfigurationNotFound as error:
        raise config.ConfigurationError(
            "%s\n"
            "If you're just setting up Sopel, welcome! "
            "You can use `sopel configure` to get started easily." % error
        )

    settings._is_daemonized = options.daemonize
    return settings


def get_pid_filename(settings, pid_dir):
    """Get the pid file name in ``pid_dir`` from the given ``settings``.

    :param settings: Sopel config
    :type settings: :class:`sopel.config.Config`
    :param str pid_dir: path to the pid directory
    :return: absolute filename of the pid file

    By default, it's ``sopel.pid``, but if the configuration's basename is not
    ``default`` then it will be used to generate the pid file name as
    ``sopel-{basename}.pid`` instead.
    """
    name = 'sopel.pid'
    if settings.basename != 'default':
        filename = os.path.basename(settings.filename)
        basename, ext = os.path.splitext(filename)
        if ext != '.cfg':
            basename = filename
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
    """Start a Sopel instance.

    :param opts: parsed arguments
    :type opts: :class:`argparse.Namespace`
    """
    # Step One: Get the configuration file and prepare to run
    try:
        settings = get_configuration(opts)
    except config.ConfigurationError as e:
        utils.stderr(e)
        return ERR_CODE_NO_RESTART

    if settings.core.not_configured:
        utils.stderr('Bot is not configured, can\'t start')
        return ERR_CODE_NO_RESTART

    # Step Two: Handle process-lifecycle options and manage the PID file
    pid_dir = settings.core.pid_dir
    pid_file_path = get_pid_filename(settings, pid_dir)
    pid = get_running_pid(pid_file_path)

    if pid is not None and utils.check_pid(pid):
        utils.stderr('There\'s already a Sopel instance running '
                     'with this config file.')
        utils.stderr('Try using either the `sopel stop` '
                     'or the `sopel restart` command.')
        return ERR_CODE

    if opts.daemonize:
        child_pid = os.fork()
        if child_pid != 0:
            return

    with open(pid_file_path, 'w') as pid_file:
        pid_file.write(str(os.getpid()))

    try:
        # Step Three: Run Sopel
        ret = run(settings, pid_file_path)
    finally:
        # Step Four: Shutdown Clean-Up
        os.unlink(pid_file_path)

    if ret == -1:
        # Restart
        os.execv(sys.executable, ['python'] + sys.argv)
    else:
        # Quit
        return ret


def command_configure(opts):
    """Sopel Configuration Wizard.

    :param opts: parsed arguments
    :type opts: :class:`argparse.Namespace`
    """
    configpath = utils.find_config(opts.configdir, opts.config)
    if opts.plugins:
        utils.plugins_wizard(configpath)
    else:
        utils.wizard(configpath)


def command_stop(opts):
    """Stop a running Sopel instance.

    :param opts: parsed arguments
    :type opts: :class:`argparse.Namespace`
    """
    # Get Configuration
    try:
        settings = utils.load_settings(opts)
    except config.ConfigurationNotFound as error:
        utils.stderr('Configuration "%s" not found' % error.filename)
        return ERR_CODE

    if settings.core.not_configured:
        utils.stderr('Sopel is not configured, can\'t stop')
        return ERR_CODE

    # Configure logging
    logger.setup_logging(settings)

    # Get Sopel's PID
    filename = get_pid_filename(settings, settings.core.pid_dir)
    pid = get_running_pid(filename)

    if pid is None or not utils.check_pid(pid):
        utils.stderr('Sopel is not running!')
        return ERR_CODE

    # Stop Sopel
    if opts.kill:
        utils.stderr('Killing the Sopel')
        os.kill(pid, signal.SIGKILL)
        return

    utils.stderr('Signaling Sopel to stop gracefully')
    if hasattr(signal, 'SIGUSR1'):
        os.kill(pid, signal.SIGUSR1)
    else:
        # Windows will not generate SIGTERM itself
        # https://docs.microsoft.com/en-us/cpp/c-runtime-library/reference/signal
        os.kill(pid, signal.SIGTERM)


def command_restart(opts):
    """Restart a running Sopel instance.

    :param opts: parsed arguments
    :type opts: :class:`argparse.Namespace`
    """
    # Get Configuration
    try:
        settings = utils.load_settings(opts)
    except config.ConfigurationNotFound as error:
        utils.stderr('Configuration "%s" not found' % error.filename)
        return ERR_CODE

    if settings.core.not_configured:
        utils.stderr('Sopel is not configured, can\'t stop')
        return ERR_CODE

    # Configure logging
    logger.setup_logging(settings)

    # Get Sopel's PID
    filename = get_pid_filename(settings, settings.core.pid_dir)
    pid = get_running_pid(filename)

    if pid is None or not utils.check_pid(pid):
        utils.stderr('Sopel is not running!')
        return ERR_CODE

    utils.stderr('Asking Sopel to restart')
    if hasattr(signal, 'SIGUSR2'):
        os.kill(pid, signal.SIGUSR2)
    else:
        # Windows will not generate SIGILL itself
        # https://docs.microsoft.com/en-us/cpp/c-runtime-library/reference/signal
        os.kill(pid, signal.SIGILL)


def main(argv=None):
    """Sopel run script entry point.

    :param list argv: command line arguments
    """
    # Build parser and handle default command
    global_options = ['-h', '--help', '-V', '--version']
    parser = build_parser()

    argv = argv or sys.argv[1:]
    if not argv:
        # No argument: assume start sub-command
        argv = ['start']

    elif argv[0].startswith('-') and argv[0] not in global_options:
        # No sub-command and no global option
        argv = ['start'] + argv

    # Parse The Command Line
    opts = parser.parse_args(argv)

    # Handle "-V/--version" option
    if opts.version:
        print_version()
        return

    try:
        # Check "Do not run as root"
        check_not_root()

        # Select command
        action = getattr(opts, 'action')
        command = {
            'start': command_start,
            'configure': command_configure,
            'stop': command_stop,
            'restart': command_restart,
        }[action]

        # Run command
        return command(opts)
    except KeyError:
        parser.print_usage()
        return ERR_CODE
    except KeyboardInterrupt:
        print("\n\nInterrupted")
        return ERR_CODE
    except RuntimeError as err:
        utils.stderr(str(err))
        return ERR_CODE


if __name__ == '__main__':
    sys.exit(main())
