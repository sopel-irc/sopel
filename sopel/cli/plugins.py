# coding=utf-8
"""Sopel Plugins Command Line Interface (CLI): ``sopel-plugins``"""
from __future__ import unicode_literals, absolute_import, print_function, division

import argparse

from sopel import plugins

from . import utils


def build_parser():
    """Configure an argument parser for ``sopel-plugins``"""
    parser = argparse.ArgumentParser(
        description='Sopel plugins tool')

    # Subparser: sopel-plugins <sub-parser> <sub-options>
    subparsers = parser.add_subparsers(
        help='Action to perform',
        dest='action')

    # sopel-plugins list
    list_parser = subparsers.add_parser(
        'list',
        help="List available Sopel plugins",
        description="""
            List available Sopel plugins from all possible sources: built-in,
            from ``sopel_modules.*``, from ``sopel.plugins`` entry points,
            or Sopel's plugin directories. Enabled plugins are displayed in
            green; disabled, in red.
        """)
    utils.add_common_arguments(list_parser)
    list_parser.add_argument(
        '-C', '--no-color',
        help='Disable colors',
        dest='no_color',
        action='store_true',
        default=False)
    list_enable = list_parser.add_mutually_exclusive_group(required=False)
    list_enable.add_argument(
        '-e', '--enabled-only',
        help='Display only enabled plugins',
        dest='enabled_only',
        action='store_true',
        default=False)
    list_enable.add_argument(
        '-d', '--disabled-only',
        help='Display only disabled plugins',
        dest='disabled_only',
        action='store_true',
        default=False)

    return parser


def handle_list(options):
    """List Sopel plugins"""
    settings = utils.load_settings(options)
    for name, info in plugins.get_usable_plugins(settings).items():
        _, is_enabled = info

        if options.enabled_only and not is_enabled:
            # hide disabled plugins when displaying enabled only
            continue
        elif options.disabled_only and is_enabled:
            # hide enabled plugins when displaying disabled only
            continue

        if options.no_color:
            print(name)
        elif is_enabled:
            print(utils.green(name))
        else:
            print(utils.red(name))


def main():
    """Console entry point for ``sopel-plugins``"""
    parser = build_parser()
    options = parser.parse_args()
    action = options.action

    if not action:
        parser.print_help()
        return

    if action == 'list':
        return handle_list(options)
