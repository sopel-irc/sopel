# coding=utf-8
"""Sopel Command Line Interfaces (CLI) utils"""
from __future__ import unicode_literals, absolute_import, print_function, division
import os

from sopel import config, run_script


def add_config_arguments(parser):
    """Add configuration related argument to a given ``parser``.

    :param parser: Argument parser (or sub-parser)
    :type parser: argparse.ArgumentParser

    This function adds the proper argument to a given ``parser`` in order to
    have a standard way to define a configuration filename in all of Sopel's
    command line interfaces.
    """
    parser.add_argument(
        '-c', '--config',
        default=None,
        metavar='filename',
        dest='config',
        help='Use a specific configuration file')


def load_settings(options):
    """Load Sopel settings from command line's ``options``.

    :param options: parsed arguments
    :return: sopel configuration loaded from the options, or the default one
    :rtype: :class:`sopel.config.Config`
    :raise sopel.config.NotFound: raised when configuration file is not found
    :raise sopel.config.ConfigurationError: raised when configuration is
                                            invalid
    """
    config_filename = run_script.find_config(options.config or 'default')

    if not os.path.isfile(config_filename):
        raise config.NotFound(filename=config_filename)

    return config.Config(config_filename)
