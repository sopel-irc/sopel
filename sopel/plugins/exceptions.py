# coding=utf-8
"""Sopel's plugins exceptions."""
# Copyright 2019, Florian Strzelecki <florian.strzelecki@gmail.com>
#
# Licensed under the Eiffel Forum License 2.
from __future__ import (
    absolute_import,
    division,
    print_function,
    unicode_literals
)


class PluginError(Exception):
    """Base class for plugin related exceptions."""


class PluginNotRegistered(PluginError):
    """Exception raised when a plugin is not registered."""
    def __init__(self, name):
        message = 'Plugin "%s" not registered' % name
        self.plugin_name = name
        super(PluginNotRegistered, self).__init__(message)
