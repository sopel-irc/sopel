# coding=utf-8
"""Sopel Config Command Line Interface (CLI): ``sopel-config``"""
from __future__ import unicode_literals, absolute_import, print_function, division

import argparse
import os

from sopel import tools, config
from . import utils


def build_parser():
    """Configure an argument parser for ``sopel-config``"""
    parser = argparse.ArgumentParser(
        description='Sopel configuration tool')

    # Subparser: sopel-config <sub-parser> <sub-options>
    subparsers = parser.add_subparsers(
        help='Actions to perform',
        dest='action')

    # sopel-config list
    list_parser = subparsers.add_parser(
        'list',
        help="List available configurations from Sopel's homedir",
        description="""
            List available configurations from Sopel's homedir ({homedir})
            with the extension "{ext}".
        """.format(homedir=config.DEFAULT_HOMEDIR, ext='.cfg'))
    list_parser.add_argument(
        '-e', '--ext', '--extension',
        dest='extension',
        default='.cfg',
        help='Filter by extension (default to "%(default)s)"')
    list_parser.add_argument(
        '-p', '--path',
        action='store_true',
        dest='display_path',
        default=False,
        help='Display a list of absolute filenames instead of their names')

    # sopel-config init
    init_parser = subparsers.add_parser(
        'init',
        help='Initialize Sopel configuration file',
        description='Initialize Sopel configuration file')
    utils.add_common_arguments(init_parser)

    # sopel-config get <section> <key>
    get_parser = subparsers.add_parser(
        'get',
        help="Get a configuration option's value",
        description="Get a configuration option's value",
    )
    get_parser.add_argument('section')
    get_parser.add_argument('option')
    utils.add_common_arguments(get_parser)

    return parser


def handle_list(options):
    """Display a list of configuration available from Sopel's homedir

    :param options: parsed arguments
    :type options: ``argparse.Namespace``

    This command displays an unordered list of config names from Sopel's
    default homedir, without their extensions::

        $ sopel-config list
        default
        custom

    It is possible to filter by extension using the ``-e/--ext/--extension``
    option; default is ``.cfg`` (the ``.`` prefix is not required).
    """
    display_path = getattr(options, 'display_path', False)
    extension = getattr(options, 'extension', '.cfg')
    if not extension.startswith('.'):
        extension = '.' + extension
    configs = utils.enumerate_configs(config.DEFAULT_HOMEDIR, extension)

    for config_filename in configs:
        if display_path:
            print(os.path.join(config.DEFAULT_HOMEDIR, config_filename))
        else:
            name, _ = os.path.splitext(config_filename)
            print(name)


def handle_init(options):
    """Use config wizard to initialize a new configuration file for the bot

    :param options: parsed arguments
    :type options: ``argparse.Namespace``

    .. note::

       Due to how the config wizard works, the configuration filename's
       extension **must be** ``.cfg``.

    """
    config_filename = utils.find_config(
        config.DEFAULT_HOMEDIR,
        getattr(options, 'config', None) or 'default')
    config_name, ext = os.path.splitext(config_filename)

    if ext and ext != '.cfg':
        tools.stderr('Configuration wizard accepts .cfg files only')
        return 1
    elif not ext:
        config_filename = config_name + '.cfg'

    if os.path.isfile(config_filename):
        tools.stderr('Configuration file %s already exists' % config_filename)
        return 1

    print('Starting Sopel config wizard for: %s' % config_filename)
    config._wizard('all', config_name)


def handle_get(options):
    """Read the settings to display the value of <section> <key>"""
    try:
        settings = utils.load_settings(options)
    except Exception as error:
        tools.stderr(error)
        return 2

    section = options.section
    option = options.option

    # Making sure the section.option exists
    if not settings.parser.has_section(section):
        tools.stderr('Section "%s" does not exist' % section)
        return 1
    if not settings.parser.has_option(section, option):
        tools.stderr(
            'Section "%s" does not have a "%s" option' % (section, option))
        return 1

    # Display the value
    print(settings.get(section, option))


def main():
    """Console entry point for ``sopel-config``"""
    parser = build_parser()
    options = parser.parse_args()
    action = options.action

    if not action:
        parser.print_help()
        return

    # init command does not require existing settings
    if action == 'list':
        return handle_list(options)
    elif action == 'init':
        return handle_init(options)
    elif action == 'get':
        return handle_get(options)
