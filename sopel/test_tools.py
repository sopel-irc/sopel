# coding=utf-8
"""This module provided tools that helped to write tests.

.. deprecated:: 7.1

    This module will be **removed in Sopel 8**.

    It formerly contained mock classes for the bot, its wrapper, and its config
    object. As the module is deprecated, so are they, and they will be removed
    as well.

    New code should use the :mod:`pytest plugin <sopel.tests.pytest_plugin>`
    for Sopel; or should take advantage of the :mod:`~sopel.tests.mocks` and
    :mod:`~sopel.tests.factories` modules, both added in Sopel 7.0.

"""
# Copyright 2013, Ari Koivula, <ari@koivu.la>
# Copyright 2019, Florian Strzelecki <florian.strzelecki@gmail.com>
# Licensed under the Eiffel Forum License 2.
from __future__ import absolute_import, division, print_function, unicode_literals

import os
import re
import sys
import tempfile

try:
    import ConfigParser
except ImportError:
    import configparser as ConfigParser

from sopel import bot, config, tools


__all__ = [
    'MockConfig',
    'MockSopel',
    'MockSopelWrapper',
    'get_example_test',
    'get_disable_setup',
    'insert_into_module',
    'run_example_tests',
]

if sys.version_info.major >= 3:
    basestring = str


class MockConfig(config.Config):
    @tools.deprecated('use configfactory fixture instead', '7.0', '8.0')
    def __init__(self):
        self.filename = tempfile.mkstemp()[1]
        self.parser = ConfigParser.RawConfigParser(allow_no_value=True)
        self.parser.add_section('core')
        self.parser.set('core', 'owner', 'Embolalia')
        self.define_section('core', config.core_section.CoreSection)
        self.get = self.parser.get

    def define_section(self, name, cls_):
        if not self.parser.has_section(name):
            self.parser.add_section(name)
        setattr(self, name, cls_(self, name))


class MockSopel(object):
    @tools.deprecated('use botfactory fixture instead', '7.0', '8.0')
    def __init__(self, nick, admin=False, owner=False):
        self.nick = nick
        self.user = "sopel"

        channel = tools.Identifier("#Sopel")
        self.channels = tools.SopelIdentifierMemory()
        self.channels[channel] = tools.target.Channel(channel)

        self.users = tools.SopelIdentifierMemory()
        self.privileges = tools.SopelMemory()

        self.memory = tools.SopelMemory()
        self.memory['url_callbacks'] = tools.SopelMemory()

        self.config = MockConfig()
        self._init_config()

        self.output = []

        if admin:
            self.config.core.admins = [self.nick]
        if owner:
            self.config.core.owner = self.nick

    def _store(self, string, *args, **kwargs):
        self.output.append(string.strip())

    write = msg = say = notice = action = reply = _store

    def _init_config(self):
        cfg = self.config
        cfg.parser.set('core', 'admins', '')
        cfg.parser.set('core', 'owner', '')
        home_dir = os.path.join(os.path.expanduser('~'), '.sopel')
        if not os.path.exists(home_dir):
            os.mkdir(home_dir)
        cfg.parser.set('core', 'homedir', home_dir)

    def register_url_callback(self, pattern, callback):
        if isinstance(pattern, basestring):
            pattern = re.compile(pattern)

        self.memory['url_callbacks'][pattern] = callback

    def unregister_url_callback(self, pattern, callback):
        if isinstance(pattern, basestring):
            pattern = re.compile(pattern)

        try:
            del self.memory['url_callbacks'][pattern]
        except KeyError:
            pass

    def search_url_callbacks(self, url):
        for regex, function in tools.iteritems(self.memory['url_callbacks']):
            match = regex.search(url)
            if match:
                yield function, match


class MockSopelWrapper(bot.SopelWrapper):
    @tools.deprecated('use sopel.bot.SopelWrapper instead', '7.0', '8.0')
    def __init__(self, *args, **kwargs):
        super(MockSopelWrapper, self).__init__(*args, **kwargs)


TEST_CONFIG = """
[core]
nick = {name}
owner = {owner}
admin = {admin}
"""


@tools.deprecated('this is now part of sopel.tests.pytest_plugin', '7.1', '8.0')
def get_example_test(*args, **kwargs):
    """Get a function that calls ``tested_func`` with fake wrapper and trigger.

    .. deprecated:: 7.1

        This is now part of the Sopel pytest plugin at
        :mod:`sopel.tests.pytest_plugin`.

    """
    from sopel.tests import pytest_plugin
    return pytest_plugin.get_example_test(*args, **kwargs)


@tools.deprecated('this is now part of sopel.tests.pytest_plugin', '7.1', '8.0')
def get_disable_setup():
    """Get a function to prevent conflict between pytest and plugin's setup.

    .. deprecated:: 7.1

        This is now part of the Sopel pytest plugin at
        :mod:`sopel.tests.pytest_plugin`.

    """
    from sopel.tests import pytest_plugin
    return pytest_plugin.get_disable_setup()


@tools.deprecated('this is now part of sopel.tests.pytest_plugin', '7.1', '8.0')
def insert_into_module(*args, **kwargs):
    """Add a function into a module.

    .. deprecated:: 7.1

        This is now part of the Sopel pytest plugin at
        :mod:`sopel.tests.pytest_plugin`.

    """
    from sopel.tests import pytest_plugin
    return pytest_plugin.insert_into_module(*args, **kwargs)


@tools.deprecated('pytest now runs @plugin.example tests directly', '7.1', '8.0')
def run_example_tests(filename, tb='native', multithread=False, verbose=False):
    # These are only required when running tests, so import them here rather
    # than at the module level.
    import pytest
    from multiprocessing import cpu_count

    args = [filename, "-s"]
    args.extend(['--tb', tb])
    if verbose:
        args.extend(['-v'])
    if multithread and cpu_count() > 1:
        args.extend(["-n", str(cpu_count())])

    pytest.main(args)
