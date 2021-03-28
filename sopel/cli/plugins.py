# coding=utf-8
"""Sopel Plugins Command Line Interface (CLI): ``sopel-plugins``"""
from __future__ import absolute_import, division, print_function, unicode_literals

import argparse
import inspect
import operator

from sopel import config, plugins, tools
from . import utils


ERR_CODE = 1
"""Error code: program exited with an error"""


def build_parser():
    """Configure an argument parser for ``sopel-plugins``.

    :return: the argument parser
    :rtype: :class:`argparse.ArgumentParser`
    """
    parser = argparse.ArgumentParser(
        description='Sopel plugins tool')

    # Subparser: sopel-plugins <sub-parser> <sub-options>
    subparsers = parser.add_subparsers(
        help='Action to perform',
        dest='action')

    # sopel-plugins show <name>
    show_parser = subparsers.add_parser(
        'show',
        formatter_class=argparse.RawTextHelpFormatter,
        help="Show plugin details",
        description="Show detailed information about a plugin.")
    utils.add_common_arguments(show_parser)
    show_parser.add_argument('name', help='Plugin name')

    # sopel-plugins configure <name>
    config_parser = subparsers.add_parser(
        'configure',
        formatter_class=argparse.RawTextHelpFormatter,
        help="Configure plugin with a config wizard",
        description=inspect.cleandoc("""
            Run a config wizard to configure a plugin.

            This can be used whether the plugin is enabled or not.
        """))
    utils.add_common_arguments(config_parser)
    config_parser.add_argument('name', help='Plugin name')

    # sopel-plugins list
    list_parser = subparsers.add_parser(
        'list',
        formatter_class=argparse.RawTextHelpFormatter,
        help="List available Sopel plugins",
        description=inspect.cleandoc("""
            List available Sopel plugins from all possible sources.

            Plugin sources are: built-in, from ``sopel_modules.*``,
            from ``sopel.plugins`` entry points, or Sopel's plugin directories.

            Enabled plugins are displayed in green; disabled, in red.
        """))
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
    list_parser.add_argument(
        '-n', '--name-only',
        help='Display only plugin names',
        dest='name_only',
        action='store_true',
        default=False)

    # sopel-plugins disable
    disable_parser = subparsers.add_parser(
        'disable',
        formatter_class=argparse.RawTextHelpFormatter,
        help="Disable a Sopel plugins",
        description=inspect.cleandoc("""
            Disable a Sopel plugin by its name, no matter where it comes from.

            It is not possible to disable the ``coretasks`` plugin.
        """))
    utils.add_common_arguments(disable_parser)
    disable_parser.add_argument(
        'names', metavar='name', nargs='+',
        help=inspect.cleandoc("""
            Name of the plugin to disable.
            Can be used multiple times to disable multiple plugins at once.
            In case of error, configuration is not modified.
        """))
    disable_parser.add_argument(
        '-f', '--force', action='store_true', default=False,
        help=inspect.cleandoc("""
            Force exclusion of the plugin.
            When ``core.enable`` is defined, a plugin may be disabled without
            being excluded. In this case, use this option to force
            its exclusion.
        """))
    disable_parser.add_argument(
        '-r', '--remove', action='store_true', default=False,
        help="Remove from ``core.enable`` list if applicable.")

    # sopel-plugins enable
    enable_parser = subparsers.add_parser(
        'enable',
        formatter_class=argparse.RawTextHelpFormatter,
        help="Enable a Sopel plugin",
        description=inspect.cleandoc("""
            Enable a Sopel plugin by its name, no matter where it comes from.

            The ``coretasks`` plugin is always enabled.

            By default, a plugin that is not excluded is enabled, unless at
            least one plugin is defined in the ``core.enable`` list.
            In that case, Sopel uses an "allow-only" policy for plugins, and
            all desired plugins must be added to this list.
        """))
    utils.add_common_arguments(enable_parser)
    enable_parser.add_argument(
        'names', metavar='name', nargs='+',
        help=inspect.cleandoc("""
            Name of the plugin to enable.
            Can be used multiple times to enable multiple plugins at once.
            In case of error, configuration is not modified.
        """))
    enable_parser.add_argument(
        '-a', '--allow-only',
        dest='allow_only',
        action='store_true',
        default=False,
        help=inspect.cleandoc("""
            Enforce allow-only policy.
            It makes sure the plugin is added to the ``core.enable`` list.
        """))

    return parser


def handle_list(options):
    """List Sopel plugins.

    :param options: parsed arguments
    :type options: :class:`argparse.Namespace`
    :return: 0 if everything went fine
    """
    settings = utils.load_settings(options)
    no_color = options.no_color
    name_only = options.name_only
    enabled_only = options.enabled_only
    disabled_only = options.disabled_only

    # get usable plugins
    items = (
        (name, info[0], info[1])
        for name, info in plugins.get_usable_plugins(settings).items()
    )
    items = (
        (name, plugin, is_enabled)
        for name, plugin, is_enabled in items
    )
    # filter on enabled/disabled if required
    if enabled_only:
        items = (
            (name, plugin, is_enabled)
            for name, plugin, is_enabled in items
            if is_enabled
        )
    elif disabled_only:
        items = (
            (name, plugin, is_enabled)
            for name, plugin, is_enabled in items
            if not is_enabled
        )
    # sort plugins
    items = sorted(items, key=operator.itemgetter(0))

    for name, plugin, is_enabled in items:
        description = {
            'name': name,
            'status': 'enabled' if is_enabled else 'disabled',
        }

        # optional meta description from the plugin itself
        try:
            plugin.load()
            description.update(plugin.get_meta_description())

            # colorize name for display purpose
            if not no_color:
                if is_enabled:
                    description['name'] = utils.green(name)
                else:
                    description['name'] = utils.red(name)
        except Exception as error:
            label = ('%s' % error) or 'unknown loading exception'
            error_status = 'error'
            description.update({
                'label': 'Error: %s' % label,
                'type': 'unknown',
                'source': 'unknown',
                'status': error_status,
            })
            if not no_color:
                if is_enabled:
                    # yellow instead of green
                    description['name'] = utils.yellow(name)
                else:
                    # keep it red for disabled plugins
                    description['name'] = utils.red(name)
                description['status'] = utils.red(error_status)

        template = '{name}/{type} {label} ({source}) [{status}]'
        if name_only:
            template = '{name}'

        print(template.format(**description))

    return 0  # successful operation


def handle_show(options):
    """Show plugin details.

    :param options: parsed arguments
    :type options: :class:`argparse.Namespace`
    :return: 0 if everything went fine;
             1 if the plugin doesn't exist or can't be loaded
    """
    plugin_name = options.name
    settings = utils.load_settings(options)
    usable_plugins = plugins.get_usable_plugins(settings)

    # plugin does not exist
    if plugin_name not in usable_plugins:
        tools.stderr('No plugin named %s' % plugin_name)
        return ERR_CODE

    plugin, is_enabled = usable_plugins[plugin_name]
    description = {
        'name': plugin_name,
        'status': 'enabled' if is_enabled else 'disabled',
    }

    # optional meta description from the plugin itself
    loaded = False
    try:
        plugin.load()
        description.update(plugin.get_meta_description())
        loaded = True
    except Exception as error:
        label = ('%s' % error) or 'unknown loading exception'
        error_status = 'error'
        description.update({
            'label': 'Error: %s' % label,
            'type': 'unknown',
            'source': 'unknown',
            'status': error_status,
        })

    print('Plugin:', description['name'])
    print('Status:', description['status'])
    print('Type:', description['type'])
    print('Source:', description['source'])
    print('Label:', description['label'])

    if not loaded:
        print('Loading failed')
        return ERR_CODE

    print('Loaded successfully')
    print('Setup:', 'yes' if plugin.has_setup() else 'no')
    print('Shutdown:', 'yes' if plugin.has_shutdown() else 'no')
    print('Configure:', 'yes' if plugin.has_configure() else 'no')
    return 0  # successful operation


def handle_configure(options):
    """Configure a Sopel plugin with a config wizard.

    :param options: parsed arguments
    :type options: :class:`argparse.Namespace`
    :return: 0 if everything went fine;
             1 if the plugin doesn't exist or can't be loaded
    """
    plugin_name = options.name
    settings = utils.load_settings(options)
    usable_plugins = plugins.get_usable_plugins(settings)

    # plugin does not exist
    if plugin_name not in usable_plugins:
        tools.stderr('No plugin named %s' % plugin_name)
        return ERR_CODE

    plugin, is_enabled = usable_plugins[plugin_name]
    try:
        plugin.load()
    except Exception as error:
        tools.stderr('Cannot load plugin %s: %s' % (plugin_name, error))
        return ERR_CODE

    if not plugin.has_configure():
        tools.stderr('Nothing to configure for plugin %s' % plugin_name)
        return 0  # nothing to configure is not exactly an error case

    print('Configure %s' % plugin.get_label())
    try:
        plugin.configure(settings)
    except KeyboardInterrupt:
        tools.stderr(
            '\nOperation cancelled; the config file has not been modified.')
        return ERR_CODE  # cancelled operation

    settings.save()

    if not is_enabled:
        tools.stderr(
            "Plugin {0} has been configured but is not enabled. "
            "Use 'sopel-plugins enable {0}' to enable it".format(plugin_name)
        )

    return 0  # successful operation


def _handle_disable_plugin(settings, plugin_name, force):
    excluded = settings.core.exclude
    # nothing left to do if already excluded
    if plugin_name in excluded:
        tools.stderr('Plugin %s already disabled.' % plugin_name)
        return False

    # recalculate state: at the moment, the plugin is not in the excluded list
    # however, with ensure_remove, the enable list may be empty, so we have
    # to compute the plugin's state here, and not use what comes from
    # plugins.get_usable_plugins
    is_enabled = (
        not settings.core.enable or
        plugin_name in settings.core.enable
    )

    # if not enabled at this point, exclude if options.force is used
    if not is_enabled and not force:
        tools.stderr(
            'Plugin %s is disabled but not excluded; '
            'use -f/--force to force its exclusion.'
            % plugin_name)
        return False

    settings.core.exclude = excluded + [plugin_name]
    return True


def display_unknown_plugins(unknown_plugins):
    """Print an error message when one or more plugins are unknown.

    :param list unknown_plugins: list of unknown plugins
    """
    # at least one of the plugins does not exist
    tools.stderr(utils.get_many_text(
        unknown_plugins,
        one='No plugin named {item}.',
        two='No plugin named {first} or {second}.',
        many='No plugin named {left}, or {last}.'
    ))


def handle_disable(options):
    """Disable Sopel plugins.

    :param options: parsed arguments
    :type options: :class:`argparse.Namespace`
    :return: 0 if everything went fine;
             1 if the plugin doesn't exist,
             or if attempting to disable coretasks (required)
    """
    plugin_names = options.names
    force = options.force
    ensure_remove = options.remove
    settings = utils.load_settings(options)
    usable_plugins = plugins.get_usable_plugins(settings)
    actually_disabled = []

    # coretasks is sacred
    if 'coretasks' in plugin_names:
        tools.stderr('Plugin coretasks cannot be disabled.')
        return ERR_CODE  # do nothing and return an error code

    unknown_plugins = [
        name
        for name in plugin_names
        if name not in usable_plugins
    ]
    if unknown_plugins:
        display_unknown_plugins(unknown_plugins)
        return ERR_CODE  # do nothing and return an error code

    # remove from enabled if asked
    if ensure_remove:
        settings.core.enable = [
            name
            for name in settings.core.enable
            if name not in plugin_names
        ]
        settings.save()

    # disable plugin (when needed)
    actually_disabled = tuple(
        name
        for name in plugin_names
        if _handle_disable_plugin(settings, name, force)
    )

    # save if required
    if actually_disabled:
        settings.save()
    else:
        return 0  # nothing to disable or save, but not an error case

    # display plugins actually disabled by the command
    print(utils.get_many_text(
        actually_disabled,
        one='Plugin {item} disabled.',
        two='Plugins {first} and {second} disabled.',
        many='Plugins {left}, and {last} disabled.'
    ))

    return 0


def _handle_enable_plugin(settings, usable_plugins, plugin_name, allow_only):
    enabled = settings.core.enable
    excluded = settings.core.exclude

    # coretasks is sacred
    if plugin_name == 'coretasks':
        tools.stderr('Plugin coretasks is always enabled.')
        return False

    # is it already enabled, but should we enforce anything?
    is_enabled = usable_plugins[plugin_name][1]
    if is_enabled and not allow_only:
        # already enabled, and no allow-only option: all good
        if plugin_name in enabled:
            tools.stderr('Plugin %s is already enabled.' % plugin_name)
        else:
            # suggest to use --allow-only option
            tools.stderr(
                'Plugin %s is enabled; '
                'use option -a/--allow-only to enforce allow only policy.'
                % plugin_name)

        return False

    # not enabled, or option allow_only to enforce
    if plugin_name in excluded:
        # remove from excluded
        settings.core.exclude = [
            name
            for name in settings.core.exclude
            if plugin_name != name
        ]
    elif plugin_name in enabled:
        # not excluded, and already in enabled list: all good
        tools.stderr('Plugin %s is already enabled' % plugin_name)
        return False

    if plugin_name not in enabled and (enabled or allow_only):
        # not excluded, but not enabled either: allow-only mode required
        # either because of the current configuration, or by request
        settings.core.enable = enabled + [plugin_name]

    return True


def handle_enable(options):
    """Enable a Sopel plugin.

    :param options: parsed arguments
    :type options: :class:`argparse.Namespace`
    :return: 0 if everything went fine;
             1 if the plugin doesn't exist
    """
    plugin_names = options.names
    allow_only = options.allow_only
    settings = utils.load_settings(options)
    usable_plugins = plugins.get_usable_plugins(settings)

    # plugin does not exist
    unknown_plugins = [
        name
        for name in plugin_names
        if name not in usable_plugins
    ]
    if unknown_plugins:
        display_unknown_plugins(unknown_plugins)
        return ERR_CODE  # do nothing and return an error code

    actually_enabled = tuple(
        name
        for name in plugin_names
        if _handle_enable_plugin(settings, usable_plugins, name, allow_only)
    )

    # save if required
    if actually_enabled:
        settings.save()
    else:
        return 0  # nothing to disable or save, but not an error case

    # display plugins actually disabled by the command
    print(utils.get_many_text(
        actually_enabled,
        one='Plugin {item} enabled.',
        two='Plugins {first} and {second} enabled.',
        many='Plugins {left}, and {last} enabled.'
    ))
    return 0


def main():
    """Console entry point for ``sopel-plugins``."""
    parser = build_parser()
    options = parser.parse_args()
    action = options.action

    if not action:
        parser.print_help()
        return ERR_CODE

    try:
        if action == 'list':
            return handle_list(options)
        elif action == 'show':
            return handle_show(options)
        elif action == 'configure':
            return handle_configure(options)
        elif action == 'disable':
            return handle_disable(options)
        elif action == 'enable':
            return handle_enable(options)
    except KeyboardInterrupt:
        tools.stderr('Bye!')
        return ERR_CODE
    except config.ConfigurationNotFound as err:
        tools.stderr(err)
        tools.stderr('Use `sopel-config init` to create a new config file.')
        return ERR_CODE
