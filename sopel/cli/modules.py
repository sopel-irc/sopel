# coding=utf-8
"""Sopel Modules Command Line Interfaces (CLI): ``sopel-module``"""
from __future__ import unicode_literals, absolute_import, print_function, division

import argparse

from sopel import loader, run_script, config, tools


def main():
    """Console entry point for ``sopel-module``"""
    parser = argparse.ArgumentParser(
        description='Experimental Sopel Module tool')
    subparsers = parser.add_subparsers(
        help='Actions to perform, default to list',
        dest='action')

    # Configure LIST action
    subparsers.add_parser(
        'list', help='List availables sopel modules')

    options = parser.parse_args()
    action = options.action or 'list'

    if action == 'list':
        config_filename = run_script.find_config('default')
        settings = config.Config(config_filename)
        modules = sorted(
            tools.iteritems(loader.enumerate_modules(settings)),
            key=lambda arg: arg[0])

        for name, info in modules:
            print(name)

        return
