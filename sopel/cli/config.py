# coding=utf-8
"""Sopel Config Command Line Interfaces (CLI): ``sopel-config``"""
from __future__ import unicode_literals, absolute_import, print_function, division

import argparse
import os

from sopel import run_script, tools, config


def add_config_option(subparser):
    """FIXME: Duplicate from sopel.cli.modules"""
    subparser.add_argument(
        '-c', '--config', default=None, metavar='filename', dest='config',
        help='Use a specific configuration file')


def build_parser():
    """Configure an argument parser for ``sopel-config``."""
    parser = argparse.ArgumentParser(
        description='Experimental Sopel Config tool')
    add_config_option(parser)  # global configuration

    # Subparser: sopel-config <subparser> <sub-options>
    subparsers = parser.add_subparsers(
        help='Actions to perform (default to list)',
        dest='action')

    init_parser = subparsers.add_parser(
        'init',
        help='Initialize sopel configuration file',
        description='Initialize sopel configuration file')
    add_config_option(init_parser)

    return parser


def load_settings(options):
    """FIXME: Duplicate from sopel.cli.modules."""
    config_filename = run_script.find_config(
        getattr(options, 'config', None) or 'default')

    if not os.path.isfile(config_filename):
        raise Exception(
            'Unable to find the configuration file %s' % config_filename)

    return config.Config(config_filename)


def handle_init(options):
    """Use config's wizard to initialize a new configuration file for the bot

    :param options: argument parser's parsed options

    .. note::

       Due to how the config's wizard works, the configuration filename's
       extension will be ignored and replaced by ``.cfg``.

    """
    config_filename = run_script.find_config(
        getattr(options, 'config', None) or 'default')
    config_name, ext = os.path.splitext(config_filename)

    if ext and ext != '.cfg':
        tools.stderr('Configuration wizard accepts .cfg file only')
        return 2
    elif not ext:
        config_filename = config_name + '.cfg'

    if os.path.isfile(config_filename):
        tools.stderr('Configuration file %s already exists' % config_filename)
        return 2

    print('Starting Sopel config wizard for: %s' % config_filename)
    config._wizard('all', config_name)


def main():
    """Console entry point for ``sopel-config``"""
    parser = build_parser()
    options = parser.parse_args()

    # init command does not require existing settings
    if options.action == 'init':
        return handle_init(options)

    # to manage other action, existing settings are required
    try:
        settings = load_settings(options)
    except Exception as error:
        tools.stderr(error)
        return 2

    print('Configuration file at: %s' % settings.filename)
