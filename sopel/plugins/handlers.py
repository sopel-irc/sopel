# coding=utf-8
"""Sopel's plugin handlers

.. versionadded:: 7.0

Between a plugin and Sopel's core, Plugin Handlers are used. It is an interface
(defined by the :class:`AbstractPluginHandler` abstract class), that acts as a
proxy between Sopel and the plugin, making a clear separation between
how the bot behave and how the plugins works.

From the :class:`~sopel.bot.Sopel` class, a plugin must be:

* loaded, using :meth:`~AbstractPluginHandler.load`
* setup (if required), using :meth:`~AbstractPluginHandler.setup`
* and eventually registered using :meth:`~AbstractPluginHandler.register`

Each subclass of :class:`AbstractPluginHandler` must implement its methods in
order to be used in the application.

At the moment, only two types of plugin are handled:

* :class:`PyModulePlugin`: manage plugins that can be imported as Python
  module from a python package, ie. where ``from package import name`` works
* :class:`PyFilePlugin`: manage plugins that are Python files on the filesystem
  or Python directory (with an ``__init__.py`` file inside), that can not be
  directly imported and extra steps are necessary

Both exposes the same interface and hide the internal implementation to the
rest of the application.
"""
from __future__ import unicode_literals, absolute_import, print_function, division

import inspect
import importlib

from sopel import loader

try:
    from importlib import reload
except ImportError:
    # py2: no reload function
    from imp import reload


class AbstractPluginHandler(object):
    """Base class for plugin handlers.

    This abstract class defines the Sopel's interface to handle plugins to:
    configure, load, shutdown, etc. a Sopel's plugin (or "module").

    It is through this interface that Sopel will interact with its plugin,
    being internals (from ``sopel.modules``) or externals (from the python
    files in a directory, to ``sopel_modules.*`` subpackages).

    A "Plugin Handler" will be created by Sopel's loader for each plugin it
    finds, and it'll delegate it to load the plugin, to list its functions
    (commands, jobs, etc.), to configure it, and to take any required actions
    on shutdown.
    """
    def load(self):
        """Load the plugin

        This method must be called first, in order to setup, register, shutdown
        or configure the plugin later.
        """
        raise NotImplementedError

    def reload(self):
        """Reload the plugin

        This method can be called once the plugin is already loaded. It will
        take care of reloading the plugin from its source.
        """
        raise NotImplementedError

    def get_label(self):
        """Retrieve a display label for the plugin

        :return: A human readable label for display purpose
        :rtype: str

        This method should, at least, return ``module_name + S + "module"``.
        """
        raise NotImplementedError

    def is_loaded(self):
        """Tell if the plugin is loaded or not

        :return: ``True`` if the plugin is loaded, ``False`` otherwise
        :rtype: boolean

        This must return ``True`` if the :meth:`load` method has been called
        with success.
        """
        raise NotImplementedError

    def setup(self, bot):
        """Setup the plugin with the ``bot``

        :param bot: instance of Sopel
        :type bot: :class:`sopel.bot.Sopel`
        """
        raise NotImplementedError

    def has_setup(self):
        """Tell if the plugin has a setup action

        :return: ``True`` if the plugin has a setup, ``False`` otherwise
        :rtype: boolean
        """
        raise NotImplementedError

    def register(self, bot):
        """Register the plugin with the ``bot``

        :param bot: instance of Sopel
        :type bot: :class:`sopel.bot.Sopel`
        """
        raise NotImplementedError

    def unregister(self, bot):
        """Unregister the plugin from the ``bot``

        :param bot: instance of Sopel
        :type bot: :class:`sopel.bot.Sopel`
        """
        raise NotImplementedError

    def shutdown(self, bot):
        """Take action on bot's shutdown

        :param bot: instance of Sopel
        :type bot: :class:`sopel.bot.Sopel`
        """
        raise NotImplementedError

    def has_shutdown(self):
        """Tell if the plugin has a shutdown action

        :return: ``True`` if the plugin has a shutdown, ``False`` otherwise
        :rtype: boolean
        """
        raise NotImplementedError

    def configure(self, settings):
        """Configure Sopel's ``settings`` for this plugin

        :param settings: Sopel's configuration
        :type settings: :class:`sopel.config.Config`

        This method will be called by the Sopel's configuration wizard.
        """
        raise NotImplementedError

    def has_configure(self):
        """Tell if the plugin has a configure action

        :return: ``True`` if the plugin has a configure, ``False`` otherwise
        :rtype: boolean
        """
        raise NotImplementedError


class PyModulePlugin(AbstractPluginHandler):
    """Sopel's Plugin loaded from a Python module or package

    A :class:`PyModulePlugin` represents a Sopel's Plugin that is a Python
    module (or package) that can be imported directly.

    This::

        >>> import sys
        >>> from sopel.plugins.handlers import PyModulePlugin
        >>> plugin = PyModulePlugin('xkcd', 'sopel.modules')
        >>> plugin.module_name
        'sopel.modules.xkcd'
        >>> plugin.load()
        >>> plugin.module_name in sys.modules
        True

    Is the same as this::

        >>> import sys
        >>> from sopel.modules import xkcd
        >>> 'sopel.modules.xkcd' in sys.modules
        True

    """
    def __init__(self, name, package=None):
        self.name = name
        self.package = package
        if package:
            self.module_name = self.package + '.' + self.name
        else:
            self.module_name = name

        self._module = None

    def get_label(self):
        default_label = '%s module' % self.name
        module_doc = getattr(self._module, '__doc__', None)

        if not self.is_loaded() or not module_doc:
            return default_label

        lines = inspect.cleandoc(module_doc).splitlines()
        return default_label if not lines else lines[0]

    def load(self):
        self._module = importlib.import_module(self.module_name)

    def reload(self):
        self._module = reload(self._module)

    def is_loaded(self):
        return self._module is not None

    def setup(self, bot):
        if self.has_setup():
            self._module.setup(bot)

    def has_setup(self):
        return hasattr(self._module, 'setup')

    def register(self, bot):
        relevant_parts = loader.clean_module(self._module, bot.config)
        bot.add_plugin(self, *relevant_parts)

    def unregister(self, bot):
        relevant_parts = loader.clean_module(self._module, bot.config)
        bot.remove_plugin(self, *relevant_parts)

    def shutdown(self, bot):
        if self.has_shutdown():
            self._module.shutdown(bot)

    def has_shutdown(self):
        return hasattr(self._module, 'shutdown')

    def configure(self, settings):
        if self.has_configure():
            self._module.configure(settings)

    def has_configure(self):
        return hasattr(self._module, 'configure')


class PyFilePlugin(PyModulePlugin):
    """Sopel's Plugin loaded from the filesystem outside of the Python Path

    This plugin handler can be used to load a Sopel's Plugin from the
    filesystem, being a Python ``.py`` file or a directory containing an
    ``__init__.py`` file, and behaves like a :class:`PyModulePlugin`::

        >>> from sopel.plugins.handlers import PyFilePlugin
        >>> plugin = PyFilePlugin('/home/sopel/.sopel/modules/custom.py')
        >>> plugin.load()
        >>> plugin.name
        'custom'

    In this example, the plugin ``custom`` is loaded from its filename albeit
    it is not in the Python path.
    """
    def __init__(self, filename):
        result = loader.get_module_description(filename)
        if result is None:
            # TODO: throw more specific exception
            raise Exception('Invalid Sopel plugin: %s' % filename)

        name, path, module_type = result
        self.filename = filename
        self.path = path
        self.module_type = module_type

        super(PyFilePlugin, self).__init__(name)

    def _load(self):
        # The current implementation of `sopel.loader.load_module` uses the
        # `imp.load_module` to perform the load action, which also reload the
        # module. However, `imp` is deprecated in Python 3, so that might need
        # to be changed when the support for Python 2 is dropped.
        #
        # However, the solution for Python 3 is non-trivial, since the
        # `importlib` built-in module does not have a similar function,
        # therefore requires to dive into its public internals
        # (``importlib.machinery`` and ``importlib.util``).
        #
        # All of that is doable, but represent a lot of works. As long as
        # Python 2 is supported, we can keep it for now.
        #
        # TODO: switch to ``importlib`` when Python2 support is dropped.
        mod, _ = loader.load_module(
            self.name, self.path, self.module_type
        )
        return mod

    def load(self):
        self._module = self._load()

    def reload(self):
        """Reload the plugin

        Unlike :class:`PyModulePlugin`, it is not possible to use the
        ``reload`` function (either from `imp` or `importlib`), because the
        module might not be available through ``sys.path``.
        """
        self._module = self._load()
