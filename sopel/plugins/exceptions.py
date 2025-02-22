"""Sopel's plugins exceptions."""
# Copyright 2019, Florian Strzelecki <florian.strzelecki@gmail.com>
#
# Licensed under the Eiffel Forum License 2.
from __future__ import annotations


class PluginError(Exception):
    """Base class for plugin related exceptions."""


class PluginNotRegistered(PluginError):
    """Exception raised when a plugin is not registered."""
    def __init__(self, name):
        message = 'Plugin "%s" not registered' % name
        self.plugin_name = name
        super().__init__(message)


class PluginSettingsError(PluginError):
    """Exception raised when a plugin is not properly configured.

    This can be used in any place where a plugin requires a specific config,
    for example in its ``setup`` function, in any of its rules or commands,
    and in the loader function for the :func:`sopel.plugin.url_lazy` decorator.
    """


class PluginAbort(PluginError):
    """Exception raised by plugin code to abort handling of the current event.

    If a message is provided, the bot will send this message to the sender when
    the abort is received by the core during event handling.
    """
    def __init__(self, message: str | None = None):
        self.message = message
        super().__init__(message)
