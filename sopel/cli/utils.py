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
    """Load Sopel settings given a command line's ``options``.

    :param options: parsed arguments
    :return: sopel configuration
    :rtype: :class:`sopel.config.Config`
    :raise sopel.config.NotFound: raised when configuration file is not found
    :raise sopel.config.ConfigurationError: raised when configuration is
                                            invalid

    This function load Sopel settings from one of these sources:

    * value of ``options.config``, if given,
    * ``SOPEL_CONFIG`` environ variable, if no option is given,
    * otherwise the ``default`` configuration is loaded,

    then loads the settings and returns it as a :class:`~sopel.config.Config`
    object.

    If the configuration file can not be found, a :exc:`sopel.config.NotFound`
    error will be raised.

    .. note::

        To use this function effectively, the
        :func:`sopel.cli.utils.add_config_arguments` should be used to add the
        proper option to the argument parser.
    """
    # Default if no options.config or no env var or if they are empty
    name = 'default'
    if options.config:
        name = options.config
    elif 'SOPEL_CONFIG' in os.environ:
        name = os.environ['SOPEL_CONFIG'] or name

    config_filename = run_script.find_config(name)

    if not os.path.isfile(config_filename):
        raise config.NotFound(filename=config_filename)

    return config.Config(config_filename)
