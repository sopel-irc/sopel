# coding=utf-8
from __future__ import unicode_literals, absolute_import, print_function, division

import os
import sys

from sopel import config, tools

# Allow clean import *
__all__ = [
    'enumerate_configs',
    'find_config',
    'add_common_arguments',
    'load_settings',
    'redirect_outputs',
]


def enumerate_configs(config_dir, extension='.cfg'):
    """List configuration files from ``config_dir`` with ``extension``

    :param str config_dir: path to the configuration directory
    :param str extension: configuration file's extension (default to ``.cfg``)
    :return: a list of configuration filenames found in ``config_dir`` with
             the correct ``extension``
    :rtype: list

    Example::

        >>> from sopel import cli, config
        >>> os.listdir(config.DEFAULT_HOMEDIR)
        ['config.cfg', 'extra.ini', 'module.cfg', 'README']
        >>> cli.enumerate_configs(config.DEFAULT_HOMEDIR)
        ['config.cfg', 'module.cfg']
        >>> cli.enumerate_configs(config.DEFAULT_HOMEDIR, '.ini')
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
    for filename in enumerate_configs(config_dir, extension):
        if name_ext == filename:
            return os.path.join(config_dir, name_ext)

    return os.path.join(config_dir, name)


def add_common_arguments(parser):
    """Add common and configuration-related arguments to a ``parser``.

    :param parser: Argument parser (or subparser)
    :type parser: argparse.ArgumentParser

    This functions adds the common arguments for Sopel's command line tools.
    At the moment, this functions adds only one argument to the parser: the
    argument used as the standard way to define a configuration filename.

    This can be used on an argument parser, or an argument subparser, to handle
    these cases::

        [sopel-command] -c [filename]
        [sopel-command] [action] -c [filename]

    Then, when the parser parses the command line arguments, it will expose
    a ``config`` option to be used to find and load Sopel's settings.

    .. seealso::

        The :func:`sopel.cli.utils.load_settings` function uses an ``options``
        object from a parser configured with such arguments.

    """
    parser.add_argument(
        '-c', '--config',
        default=None,
        metavar='filename',
        dest='config',
        help='Use a specific configuration file')


def load_settings(options):
    """Load Sopel's settings using the command line's ``options``.

    :param options: parsed arguments
    :return: sopel configuration
    :rtype: :class:`sopel.config.Config`
    :raise sopel.config.ConfigurationNotFound: raised when configuration file
                                               is not found
    :raise sopel.config.ConfigurationError: raised when configuration is
                                            invalid

    This function loads Sopel's settings from one of these sources:

    * value of ``options.config``, if given,
    * ``SOPEL_CONFIG`` environment variable, if no option is given,
    * otherwise the ``default`` configuration is loaded,

    then loads the settings and returns it as a :class:`~sopel.config.Config`
    object.

    If the configuration file can not be found, a
    :exc:`sopel.config.ConfigurationNotFound` error will be raised.

    .. note::

        To use this function effectively, the
        :func:`sopel.cli.utils.add_common_arguments` function should be used to
        add the proper option to the argument parser.

    """
    # Default if no options.config or no env var or if they are empty
    name = 'default'
    if options.config:
        name = options.config
    elif 'SOPEL_CONFIG' in os.environ:
        name = os.environ['SOPEL_CONFIG'] or name  # use default if empty

    filename = find_config(config.DEFAULT_HOMEDIR, name)

    if not os.path.isfile(filename):
        raise config.ConfigurationNotFound(filename=filename)

    return config.Config(filename)


def redirect_outputs(settings, is_quiet=False):
    """Redirect ``sys``'s outputs using Sopel's settings.

    :param settings: Sopel's configuration
    :type settings: :class:`sopel.config.Config`
    :param bool is_quiet: Optional, set to True to make Sopel's outputs quiet

    Both ``sys.stderr`` and ``sys.stdout`` are redirected to a logfile.
    """
    logfile = os.path.os.path.join(settings.core.logdir, 'stdio.log')
    sys.stderr = tools.OutputRedirect(logfile, True, is_quiet)
    sys.stdout = tools.OutputRedirect(logfile, False, is_quiet)
