"""Sopel's plugins interface.

.. versionadded:: 7.0

Sopel uses what are called Plugin Handlers as an interface between the bot and
its plugins (formerly called "modules"). This interface is defined by the
:class:`~.handlers.AbstractPluginHandler` abstract class.

Plugins that can be used by Sopel are provided by :func:`~.get_usable_plugins`
in an :class:`ordered dict<collections.OrderedDict>`. This dict contains one
and only one plugin per unique name, using a specific order:

* extra directories defined in the settings
* homedir's ``plugins`` directory
* ``sopel.plugins`` entry point group
* ``sopel_modules``'s subpackages
* ``sopel.builtins``'s core plugins

(The ``coretasks`` plugin is *always* the one from ``sopel.coretasks`` and
cannot be overridden.)

To find all plugins (no matter their sources), the :func:`~.enumerate_plugins`
function can be used. For a more fine-grained search, ``find_*`` functions
exist for each type of plugin.
"""
# Copyright 2019, Florian Strzelecki <florian.strzelecki@gmail.com>
#
# Licensed under the Eiffel Forum License 2.
from __future__ import annotations

import collections
import importlib
import itertools
import logging
import os
from typing import TYPE_CHECKING

# TODO: use stdlib importlib.metadata when possible, after dropping py3.9.
# Stdlib does not support `entry_points(group='filter')` until py3.10, but
# fallback logic is more trouble than it's worth when e.g. clean Ubuntu
# py3.10 envs include old versions of this backport.
import importlib_metadata

from sopel.lifecycle import deprecated

from . import callables, exceptions, handlers, rules  # noqa


if TYPE_CHECKING:
    from collections.abc import Iterable


LOGGER = logging.getLogger(__name__)


def _list_plugin_filenames(
    directory: str | os.PathLike,
) -> Iterable[tuple[str, str]]:
    # list plugin filenames from a directory
    # yield 2-value tuples: (name, absolute path)
    base = os.path.abspath(directory)
    for filename in os.listdir(base):
        abspath = os.path.realpath(os.path.join(base, filename))
        if not os.path.exists(abspath):
            LOGGER.warning("Plugin path does not exist, skipping: %r", abspath)
            continue

        if os.path.isdir(abspath):
            if os.path.isfile(os.path.join(abspath, '__init__.py')):
                yield os.path.basename(filename), abspath
        else:
            name, ext = os.path.splitext(filename)
            if ext == '.py' and name != '__init__':
                yield name, abspath


def find_internal_plugins():
    """List internal plugins.

    :return: yield instances of :class:`~.handlers.PyModulePlugin`
             configured for ``sopel.builtins.*``

    Internal plugins can be found under ``sopel.builtins``. This list does not
    include the ``coretasks`` plugin.
    """
    builtins = importlib.util.find_spec('sopel.builtins')
    if builtins is None or builtins.submodule_search_locations is None:
        raise RuntimeError('Cannot resolve internal plugins')
    plugin_list = itertools.chain.from_iterable(
        _list_plugin_filenames(path)
        for path in builtins.submodule_search_locations
    )

    for name, _ in set(plugin_list):
        yield handlers.PyModulePlugin(name, 'sopel.builtins')


def find_sopel_modules_plugins():
    """List plugins from ``sopel_modules.*``.

    :return: yield instances of :class:`~.handlers.PyModulePlugin`
             configured for ``sopel_modules.*``

    Before entry point plugins, the only way to package a plugin was to follow
    :pep:`382` by using the ``sopel_modules`` namespace. This function is
    responsible to load such plugins.

    .. deprecated:: 8.1

        This method is deprecated as ``sopel_modules.*`` style of plugins is
        deprecated. It will be removed in Sopel 9.0.

    """
    try:
        import sopel_modules  # type: ignore[import]
    except ImportError:
        return

    for plugin_dir in set(sopel_modules.__path__):
        for name, abspath in _list_plugin_filenames(plugin_dir):
            handler = handlers.PyModulePlugin(name, 'sopel_modules')

            deprecated(
                'sopel_modules namespace is deprecated; '
                'Sopel 9 won\'t be able to load plugin "%s" (%s)' % (
                    name, abspath
                ),
                version='8.1',
                removed_in='9.0',
                stack_output=False,
                func=lambda *args: ...,
            )()

            yield handler


def find_entry_point_plugins(group='sopel.plugins'):
    """List plugins from an entry point group.

    :param str group: entry point group to search in (defaults to
                      ``sopel.plugins``)
    :return: yield instances of :class:`~.handlers.EntryPointPlugin`
             created from each entry point in the ``group``

    This function finds plugins declared under an entry point group; by
    default it looks in the ``sopel.plugins`` group.
    """
    for entry_point in importlib_metadata.entry_points(group=group):
        yield handlers.EntryPointPlugin(entry_point)


def find_directory_plugins(directory):
    """List plugins from a ``directory``.

    :param str directory: directory path to search
    :return: yield instances of :class:`~.handlers.PyFilePlugin`
             found in ``directory``

    This function looks for single file and folder plugins in a directory.
    """
    for _, abspath in _list_plugin_filenames(directory):
        yield handlers.PyFilePlugin(abspath)


def enumerate_plugins(settings):
    """Yield Sopel's plugins.

    :param settings: Sopel's configuration
    :type settings: :class:`sopel.config.Config`
    :return: yield 2-value tuple: an instance of
             :class:`~.handlers.AbstractPluginHandler`, and if the plugin is
             active or not

    This function uses the find functions to find all of Sopel's available
    plugins. It uses the bot's ``settings`` to determine if the plugin is
    enabled or disabled.

    .. seealso::

        The find functions used are:

        * :func:`find_internal_plugins` for internal plugins
        * :func:`find_sopel_modules_plugins` for ``sopel_modules.*`` plugins
        * :func:`find_entry_point_plugins` for plugins exposed via packages'
          entry points
        * :func:`find_directory_plugins` for plugins in ``$homedir/plugins``,
          and in extra directories as defined by ``settings.core.extra``

    .. versionchanged:: 8.0

        Looks in ``$homedir/plugins`` instead of the ``$homedir/modules``
        directory, reflecting Sopel's shift away from calling them "modules".

    """
    from_internals = find_internal_plugins()
    from_sopel_modules = find_sopel_modules_plugins()
    from_entry_points = find_entry_point_plugins()
    # load from directories
    source_dirs = [
        os.path.join(settings.homedir, 'plugins'),
    ]
    if settings.core.extra:
        source_dirs = source_dirs + settings.core.extra

    from_directories = [
        find_directory_plugins(source_dir)
        for source_dir in source_dirs
        if os.path.isdir(source_dir)
    ]

    # Retrieve all plugins
    all_plugins = itertools.chain(
        from_internals,
        from_sopel_modules,
        from_entry_points,
        *from_directories)

    # Get plugin settings
    enabled = settings.core.enable
    disabled = settings.core.exclude

    # Yield all found plugins with their enabled status (True/False)
    for plugin in all_plugins:
        name = plugin.name
        is_enabled = name not in disabled and (not enabled or name in enabled)
        yield plugin, is_enabled

    # And always yield coretasks
    yield handlers.PyModulePlugin('coretasks', 'sopel'), True


def get_usable_plugins(settings):
    """Get usable plugins, unique per name.

    :param settings: Sopel's configuration
    :type settings: :class:`sopel.config.Config`
    :return: an ordered dict of usable plugins
    :rtype: collections.OrderedDict

    This function provides the plugins Sopel can use to load, enable,
    or disable, as an :class:`ordered dict<collections.OrderedDict>`. This dict
    contains one and only one plugin per unique name, using a specific order:

    * extra directories defined in the settings
    * homedir's ``plugins`` directory
    * ``sopel.plugins`` entry point group
    * ``sopel_modules``'s subpackages
    * ``sopel.builtins``'s core plugins

    (The ``coretasks`` plugin is *always* the one from ``sopel.coretasks`` and
    cannot be overridden.)

    .. seealso::

        The :func:`~.enumerate_plugins` function is used to generate a list
        of all possible plugins, and its return value is used to populate
        the :class:`ordered dict<collections.OrderedDict>`.

    """
    # Use an OrderedDict to get one and only one plugin per name
    # based on what plugins.enumerate_plugins does, external plugins are
    # allowed to override internal plugins
    plugins_info = collections.OrderedDict(
        (plugin.name, (plugin, is_enabled))
        for plugin, is_enabled in enumerate_plugins(settings))
    # reset coretasks's position at the end of the loading queue
    plugins_info.move_to_end('coretasks')

    return plugins_info
