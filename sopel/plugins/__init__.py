# coding=utf-8
"""Sopel's plugins interface

.. versionadded:: 7.0

Sopel uses plugins (also called "modules") and uses what are called
Plugin Handlers as an interface between the bot and its plugins. This interface
is defined by the :class:`~.handlers.AbstractPluginHandler` abstract class.

Plugins that can be used by Sopel are provided by :func:`~.get_usable_plugins`
in an :class:`ordered dict<collections.OrderedDict>`. This dict contains one
and only one plugin per unique name, using a specific order:

* extra directories defined in the settings
* homedir's ``plugins`` directory
* homedir's ``modules`` directory
* ``sopel.plugins`` setuptools entry points
* ``sopel_modules``'s subpackages
* ``sopel.modules``'s core plugins

(The ``coretasks`` plugin is *always* the one from ``sopel.coretasks`` and
cannot be overridden.)

To find all plugins (no matter their sources), the :func:`~.enumerate_plugins`
function can be used. For a more fine-grained search, ``find_*`` functions
exist for each type of plugin.
"""
# Copyright 2019, Florian Strzelecki <florian.strzelecki@gmail.com>
#
# Licensed under the Eiffel Forum License 2.
from __future__ import unicode_literals, absolute_import, print_function, division

import collections
import imp
import itertools
import os

import pkg_resources

from . import exceptions, handlers  # noqa


def _list_plugin_filenames(directory):
    # list plugin filenames from a directory
    # yield 2-value tuples: (name, absolute path)
    base = os.path.abspath(directory)
    for filename in os.listdir(base):
        abspath = os.path.join(base, filename)

        if os.path.isdir(abspath):
            if os.path.isfile(os.path.join(abspath, '__init__.py')):
                yield os.path.basename(filename), abspath
        else:
            name, ext = os.path.splitext(filename)
            if ext == '.py' and name != '__init__':
                yield name, abspath


def find_internal_plugins():
    """List internal plugins

    :return: Yield instance of :class:`~.handlers.PyModulePlugin`
             configured for ``sopel.modules.*``
    """
    plugin_dir = imp.find_module(
        'modules',
        [imp.find_module('sopel')[1]]
    )[1]

    for name, _ in _list_plugin_filenames(plugin_dir):
        yield handlers.PyModulePlugin(name, 'sopel.modules')


def find_sopel_modules_plugins():
    """List plugins from ``sopel_modules.*``

    :return: Yield instance of :class:`~.handlers.PyModulePlugin`
             configured for ``sopel_modules.*``
    """
    try:
        import sopel_modules
    except ImportError:
        return

    for plugin_dir in set(sopel_modules.__path__):
        for name, _ in _list_plugin_filenames(plugin_dir):
            yield handlers.PyModulePlugin(name, 'sopel_modules')


def find_entry_point_plugins(group='sopel.plugins'):
    """List plugins from a setuptools entry point group

    :param str group: setuptools entry point group to look for
                      (defaults to ``sopel.plugins``)
    :return: Yield instance of :class:`~.handlers.EntryPointPlugin`
             created from setuptools entry point given ``group``
    """
    for entry_point in pkg_resources.iter_entry_points(group):
        yield handlers.EntryPointPlugin(entry_point)


def find_directory_plugins(directory):
    """List plugins from a ``directory``

    :param str directory: Directory path to search
    :return: Yield instance of :class:`~.handlers.PyFilePlugin`
             found in ``directory``
    """
    for _, abspath in _list_plugin_filenames(directory):
        yield handlers.PyFilePlugin(abspath)


def enumerate_plugins(settings):
    """Yield Sopel's plugins

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
       * :func:`find_entry_point_plugins` for plugins exposed by setuptools
         entry points
       * :func:`find_directory_plugins` for plugins in ``$homedir/modules``,
         ``$homedir/plugins``, and in extra directories, as defined by
         ``settings.core.extra``

    .. versionchanged:: 7.0

       Previously, plugins were called "modules", so this would load plugins
       from the ``$homedir/modules`` directory. Now it also loads plugins
       from the ``$homedir/plugins`` directory.

    """
    from_internals = find_internal_plugins()
    from_sopel_modules = find_sopel_modules_plugins()
    from_entry_points = find_entry_point_plugins()
    # load from directories
    source_dirs = [
        os.path.join(settings.homedir, 'modules'),
        os.path.join(settings.homedir, 'plugins'),
    ]
    if settings.core.extra:
        source_dirs = source_dirs + list(settings.core.extra)

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
    """Get usable plugins, unique per name

    :param settings: Sopel's configuration
    :type settings: :class:`sopel.config.Config`
    :return: an ordered dict of usable plugins
    :rtype: collections.OrderedDict

    This function provides the plugins Sopel can use to load, enable,
    or disable, as an :class:`ordered dict<collections.OrderedDict>`. This dict
    contains one and only one plugin per unique name, using a specific order:

    * extra directories defined in the settings
    * homedir's ``modules`` directory
    * ``sopel.plugins`` setuptools entry points
    * ``sopel_modules``'s subpackages
    * ``sopel.modules``'s core plugins

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
    # Python 2's OrderedDict does not have a `move_to_end` method
    # TODO: replace by plugins_info.move_to_end('coretasks') for Python 3
    core_info = plugins_info.pop('coretasks')
    plugins_info['coretasks'] = core_info

    return plugins_info
