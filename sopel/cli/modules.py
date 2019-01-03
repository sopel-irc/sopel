# coding=utf-8
"""Sopel Modules Command Line Interfaces (CLI): ``sopel-module``"""
from __future__ import unicode_literals, absolute_import, print_function, division

import argparse
import imp

from sopel import loader, run_script, config


DISPLAY_TYPE = {
    imp.PKG_DIRECTORY: 'p',
    imp.PY_SOURCE: 'm'
}


def main():
    """Console entry point for ``sopel-module``"""
    parser = argparse.ArgumentParser(
        description='Experimental Sopel Module tool')
    subparsers = parser.add_subparsers(
        help='Actions to perform (default to list)',
        dest='action')

    # Configure LIST action
    list_parser = subparsers.add_parser(
        'list',
        help='List availables sopel modules',
        description='List availables sopel modules')
    list_parser.add_argument(
        '-p', '--path',
        action='store_true',
        dest='show_path',
        default=False,
        help='Show the path to the module file')
    list_parser.add_argument(
        '-t', '--type',
        action='store_true',
        dest='show_type',
        default=False,
        help=('Show the type to the module file: '
              '`p` for package directory, '
              '`m` for module file, '
              '`?` for unknown'))
    list_parser.add_argument(
        '-a', '--all',
        action='store_true',
        dest='show_all',
        default=False,
        help='Show all available module, enabled or not')

    options = parser.parse_args()
    action = options.action or 'list'

    if action == 'list':
        config_filename = run_script.find_config('default')
        settings = config.Config(config_filename)
        modules = loader.enumerate_modules(settings, show_all=options.show_all)
        modules = sorted(
            modules.items(),
            key=lambda arg: arg[0])

        col_sep = '\t'
        template = '{name}'
        if options.show_path:
            # Get the maximum length of module names for display purpose
            max_length = max(len(info[0]) for info in modules)

            template = col_sep.join([
                '{name:<' + str(max_length) + '}',
                '{path}',
            ])

        if options.show_type:
            template = col_sep.join(['{module_type}', template])

        for name, info in modules:
            path, module_type = info
            print(template.format(
                name=name,
                path=path,
                module_type=DISPLAY_TYPE.get(module_type, '?'),
            ))

        return
