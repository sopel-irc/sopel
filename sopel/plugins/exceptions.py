# coding=utf-8
from __future__ import unicode_literals, absolute_import, print_function, division


class PluginError(Exception):
    pass


class PluginNotRegistered(PluginError):
    def __init__(self, name):
        message = 'Plugin "%s" not registered' % name
        self.plugin_name = name
        super(PluginNotRegistered, self).__init__(message)
