# coding=utf-8
from __future__ import unicode_literals, absolute_import, print_function, division

import inspect
import importlib

from sopel import loader


class AbstractPluginHandler(object):
    """Base class for plugin handlers.

    This abstract class defines the Sopel's interface to handle plugins to:
    configure, load, shutdown, etc. a Sopel's plugin (or "module").

    It is through this interface that Sopel will interact with its plugin,
    being internals (from `sopel.modules`) or externals (from the python files
    in a directory, to ``sopel_modules.*` subpackages).

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
        """Setup the plugin with the ``bot``"""
        raise NotImplementedError

    def has_setup(self):
        """Tell if the plugin has a setup action

        :return: ``True`` if the plugin has a setup, ``False`` otherwise
        :rtype: boolean
        """
        raise NotImplementedError

    def register(self, bot):
        """Register the plugin with the ``bot``"""
        raise NotImplementedError

    def shutdown(self, bot):
        """Take action on bot's shutdown"""
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

    A :class:`sopel.plugins.handlers.PyModulePlugin` represents a Sopel's
    Plugin that is a Python module (or package) that can be imported directly.

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

    def is_loaded(self):
        return self._module is not None

    def setup(self, bot):
        if self.has_setup():
            self._module.setup(bot)

    def has_setup(self):
        return hasattr(self._module, 'setup')

    def register(self, bot):
        relevant_parts = loader.clean_module(self._module, bot.config)
        bot.register(*relevant_parts)

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

    def load(self):
        self._module, _ = loader.load_module(
            self.name, self.path, self.module_type
        )
