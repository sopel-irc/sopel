# coding=utf-8
from __future__ import unicode_literals, absolute_import, print_function, division


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
