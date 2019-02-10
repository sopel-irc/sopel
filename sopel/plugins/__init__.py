# coding=utf-8
from __future__ import unicode_literals, absolute_import, print_function, division

import imp
import itertools
import os

from . import handlers  # noqa


def _list_plugin_filenames(directory):
    # list plugin filenames from a directory
    # yield 2-values tuples: (name, absolute path)
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

    :return: Yield instance of :class:`sopel.plugins.handlers.PyModulePlugin`
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

    :return: Yield instance of :class:`sopel.plugins.handlers.PyModulePlugin`
             configured for ``sopel_modules.*``
    """
    try:
        import sopel_modules
    except:  # noqa
        return

    for plugin_dir in set(sopel_modules.__path__):
        for name, _ in _list_plugin_filenames(plugin_dir):
            yield handlers.PyModulePlugin(name, 'sopel_modules')


def find_directory_plugins(directory):
    """List plugins from a ``directory``

    :return: Yield instance of :class:`sopel.plugins.handlers.PyFilePlugin`
             found in ``directory``
    """
    for _, abspath in _list_plugin_filenames(directory):
        yield handlers.PyFilePlugin(abspath)


def enumerate_plugins(settings):
    """Yield Sopel's plugins

    :param settings: Sopel's configuration
    :type settings: :class:`sopel.config.Config`
    :return: yield 2-values tuple: an instance of
             :class:`sopel.plugins.handlers.AbstractPluginHandler`, and
             if the plugin is active or not

    This function uses the find functions to find all the available Sopel's
    plugins. It uses the bot's ``settings`` to determine if the plugin is
    enabled or disabled.

    .. seealso::

       The find functions used are:

       * :func:`find_internal_plugins` for internal plugins
       * :func:`find_sopel_modules_plugins` for sopel_modules.* plugins
       * :func:`find_directory_plugins` for modules in ``$homedir/modules``
         and in extra directories, as defined by ``settings.core.extra``

    """
    from_internals = find_internal_plugins()
    from_sopel_modules = find_sopel_modules_plugins()
    # load from directories
    source_dirs = [os.path.join(settings.homedir, 'modules')]
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
        *from_directories)

    # Get setting's details
    enabled = settings.core.enable
    disabled = settings.core.exclude

    # Yield all found plugins with their enable status (yes/no)
    for plugin in all_plugins:
        name = plugin.name
        is_enabled = name not in disabled and (not enabled or name in enabled)
        yield plugin, is_enabled

    # And always yield coretasks
    yield handlers.PyModulePlugin('coretasks', 'sopel'), True
