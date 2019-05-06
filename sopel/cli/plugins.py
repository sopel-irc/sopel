# coding=utf-8
"""Sopel Plugins Command Line Interface (CLI): ``sopel-plugins``"""
from __future__ import unicode_literals, absolute_import, print_function, division

import argparse

from sopel import plugins, tools

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

    # sopel-plugin disable
    disable_parser = subparsers.add_parser(
        'disable',
        help="Disable a Sopel plugins",
        description="""
            Disable a Sopel plugin by its name, no matter where it comes from.
            It is not possible to disable the ``coretasks`` plugin.
        """)
    utils.add_common_arguments(disable_parser)
    disable_parser.add_argument('name', help='Name of the plugin to disable')
    disable_parser.add_argument(
        '-f', '--force', action='store_true', default=False,
        help="""
            Force exclusion of the plugin. When ``core.enable`` is defined, a
            plugin may be disabled without being excluded. In this case, use
            this option to force its exclusion.
        """)
    disable_parser.add_argument(
        '-r', '--remove', action='store_true', default=False,
        help="""
            Remove from ``core.enable`` list if applicable.
        """)

    # sopel-plugin enable
    enable_parser = subparsers.add_parser(
        'enable',
        help="Enable a Sopel plugins",
        description="""
            Enable a Sopel plugin by its name, no matter where it comes from.
            The ``coretasks`` plugin is always enabled. By default, a plugin
            that is not excluded is enabled, unless at least one plugin is
            defined in the ``core.enable`` list. In that case, Sopel uses
            a "allow-only" policy for plugins, and enabled plugins must be
            added to this list.
        """)
    utils.add_common_arguments(enable_parser)
    enable_parser.add_argument('name', help='Name of the plugin to enable')
    enable_parser.add_argument(
        '-a', '--allow-only',
        dest='allow_only',
        action='store_true',
        default=False,
        help="""
            Enforce allow-only policy, adding the plugin to the ``core.enable``
            list.
        """)

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


def handle_disable(options):
    """Disable a Sopel plugin"""
    plugin_name = options.name
    settings = utils.load_settings(options)
    usable_plugins = plugins.get_usable_plugins(settings)
    excluded = settings.core.exclude

    # coretasks is sacred
    if plugin_name == 'coretasks':
        tools.stderr('Plugin coretasks cannot be disabled')
        return 1

    # plugin does not exist
    if plugin_name not in usable_plugins:
        tools.stderr('No plugin named %s' % plugin_name)
        return 1

    # remove from enabled if asked
    if options.remove and plugin_name in settings.core.enable:
        settings.core.enable = [
            name
            for name in settings.core.enable
            if name != plugin_name
        ]
        settings.save()

    # nothing left to do if already excluded
    if plugin_name in excluded:
        tools.stderr('Plugin %s already disabled' % plugin_name)
        return 0

    # recalculate state: at the moment, the plugin is not in the excluded list
    # however, with options.remove, the enable list may be empty, so we have
    # to compute the plugin's state here, and not use what comes from
    # plugins.get_usable_plugins
    is_enabled = (
        not settings.core.enable or
        plugin_name in settings.core.enable
    )

    # if not enabled at this point, exclude if options.force is used
    if not is_enabled and not options.force:
        tools.stderr(
            'Plugin %s is disabled but not excluded; '
            'use -f/--force to force its exclusion'
            % plugin_name)
        return 0

    settings.core.exclude = excluded + [plugin_name]
    settings.save()

    print('Plugin %s disabled' % plugin_name)


def handle_enable(options):
    """Enable a Sopel plugin"""
    plugin_name = options.name
    settings = utils.load_settings(options)
    usable_plugins = plugins.get_usable_plugins(settings)
    enabled = settings.core.enable
    excluded = settings.core.exclude

    # coretasks is sacred
    if plugin_name == 'coretasks':
        tools.stderr('Plugin coretasks is always enabled')
        return 0

    # plugin does not exist
    if plugin_name not in usable_plugins:
        tools.stderr('No plugin named %s' % plugin_name)
        return 1

    # is it already enabled, but should we enforce anything?
    is_enabled = usable_plugins[plugin_name][1]
    if is_enabled and not options.allow_only:
        # already enabled, and no allow-only option: all good
        if plugin_name not in enabled:
            tools.stderr(
                'Plugin %s is enabled; '
                'use option -a/--allow-only to enforce allow only policy'
                % plugin_name)
        return 0

    # not enabled, or options.allow_only to enforce
    if plugin_name in excluded:
        # remove from excluded
        settings.core.exclude = [
            name
            for name in settings.core.exclude
            if name != plugin_name
        ]
    elif plugin_name in enabled:
        # not excluded, and already in enabled list: all good
        tools.stderr('Plugin %s is already enabled' % plugin_name)
        return 0

    if plugin_name not in enabled:
        if enabled or options.allow_only:
            # not excluded, but not enabled either: allow-only mode required
            # either because of the current configuration, or by request
            settings.core.enable = enabled + [plugin_name]

    settings.save()
    tools.stderr('Plugin %s enabled' % plugin_name)
    return 0


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
    elif action == 'disable':
        return handle_disable(options)
    elif action == 'enable':
        return handle_enable(options)
