# coding=utf-8
"""Sopel's plugins exceptions."""
from __future__ import unicode_literals, absolute_import, print_function, division


class PluginError(Exception):
    """Base class for plugin related exceptions."""


class PluginNotRegistered(PluginError):
    """Exception raised when a plugin is not registered."""
    def __init__(self, name):
        message = 'Plugin "%s" not registered' % name
        self.plugin_name = name
        super(PluginNotRegistered, self).__init__(message)
