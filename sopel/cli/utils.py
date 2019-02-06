# coding=utf-8
from __future__ import unicode_literals, absolute_import, print_function, division

import os


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
    for config in enumerate_configs(config_dir, extension):
        if name_ext == config:
            return os.path.join(config_dir, name_ext)

    return os.path.join(config_dir, name)


def add_config_arguments(parser):
    """Add configuration-related argument to a ``parser``.

    :param parser: Argument parser (or subparser)
    :type parser: argparse.ArgumentParser

    This function adds the proper argument to the ``parser`` given in order to
    have a standard way to define a configuration filename in all of Sopel's
    command line interfaces.

    This can be used on an argument parser, or an argument subparser, to handle
    these cases::

        [sopel-command] -c [filename]
        [sopel-command] [action] -c [filename]

    Then, when the parser parses the command line arguments, it will expose
    a ``config`` option to be used to find and load Sopel's settings.
    """
    parser.add_argument(
        '-c', '--config',
        default=None,
        metavar='filename',
        dest='config',
        help='Use a specific configuration file')
