# coding=utf-8
"""Sopel Modules Command Line Interfaces (CLI): ``sopel-module``"""
from __future__ import unicode_literals, absolute_import, print_function, division

import argparse
import imp
import inspect

from sopel import loader, run_script, config, tools


DISPLAY_ENABLE = {
    True: 'E',
    False: 'X',
}

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

    # Configure SHOW action
    show_parser = subparsers.add_parser(
        'show',
        help='Show a sopel module\'s details',
        description='Show a sopel module\'s details')
    show_parser.add_argument('module')

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

    list_group = list_parser.add_mutually_exclusive_group()
    list_group.add_argument(
        '-a', '--all',
        action='store_true',
        dest='show_all',
        default=False,
        help='Show all available module, enabled or not')
    list_group.add_argument(
        '-e', '--excluded',
        action='store_true',
        dest='show_excluded',
        default=False,
        help='Show only excluded module')

    options = parser.parse_args()
    action = options.action or 'list'
    config_filename = run_script.find_config('default')
    settings = config.Config(config_filename)

    if action == 'list':
        # Line formatting
        template = '{name}'  # Default display: only the module name
        name_template = '{name}'  # Default: no padding
        col_sep = '\t'  # Separator between displayed columns

        # Get modules
        show_all = options.show_all or options.show_excluded
        modules = loader.enumerate_modules(settings, show_all=show_all).items()

        # Show All
        if show_all:
            # If all are shown, add the "enabled" column
            template = col_sep.join([template, '{enabled}'])

        # Show Excluded Only
        if options.show_excluded:
            if settings.core.enable:
                # Get all but enabled
                modules = [
                    (name, info)
                    for name, info in modules
                    # Remove enabled modules...
                    # ... unless they are in the excluded list.
                    if name in settings.core.exclude or
                    name not in settings.core.enable
                ]

            if settings.core.exclude:
                # Get only excluded
                modules = [
                    (name, info)
                    for name, info in modules
                    if name in settings.core.exclude
                ]

        # Sort modules
        modules = sorted(
            modules,
            key=lambda arg: arg[0])

        # Show Module Path
        if options.show_path:
            # Get the maximum length of module names for display purpose
            max_length = max(len(info[0]) for info in modules)
            name_template = '{name:<' + str(max_length) + '}'
            # Add the path at the end of the line
            template = col_sep.join([template, '{path}'])

        # Show Module Type (package or python module)
        if options.show_type:
            template = col_sep.join(['{module_type}', template])

        # Display list of modules with the line template
        for name, info in modules:
            path, module_type = info
            enabled = True
            if settings.core.enable:
                enabled = name in settings.core.enable
            if settings.core.exclude:
                enabled = name not in settings.core.exclude

            print(template.format(
                name=name_template.format(name=name),
                path=path,
                module_type=DISPLAY_TYPE.get(module_type, '?'),
                enabled=DISPLAY_ENABLE.get(enabled),
            ))

        return

    if action == 'show':
        module_name = options.module
        availables = loader.enumerate_modules(settings, show_all=True)
        if module_name not in availables:
            tools.stderr('No module named %s' % module_name)
            return 1

        module_path, module_type = availables[module_name]
        module, last_modified = loader.load_module(
            module_name, module_path, module_type)
        module_info = loader.clean_module(module, settings)

        if not any(module_info):
            print('Module %s does not define any Sopel trigger' % module_name)
            return 1

        callables, jobs, shutdowns, urls = module_info

        print('# Module Information')
        print('')
        print('Module name: %s' % module_name)
        print('Path: %s' % module_path)
        print('Last modified at: %s' % last_modified)
        print('Has shutdown: %s' % ('yes' if shutdowns else 'no'))
        print('Has job: %s' % ('yes' if jobs else 'no'))

        if callables:
            rule_callables = []
            print('')
            print('# Module Commands')
            for command in callables:
                print('')

                if command._docs.keys():
                    print('## %s' % ', '.join(command._docs.keys()))
                elif command.rule:
                    # display rules afters normal commands
                    rule_callables.append(command)
                    continue

                docstring = inspect.cleandoc(
                    command.__doc__ or 'No documentation provided.'
                ).splitlines()
                for line in docstring:
                    print('\t%s' % line)

            if rule_callables:
                print('')
                print('# Module Rules')

                for command in rule_callables:
                    print('')
                    for rule in command.rule:
                        print(rule.pattern)

                    docstring = inspect.cleandoc(
                        command.__doc__ or 'No documentation provided.'
                    ).splitlines()
                    for line in docstring:
                        print('\t%s' % line)

        if urls:
            print('')
            print('# URL Patterns')

            for url in urls:
                print('\t%s' % url.url_regex.pattern)
