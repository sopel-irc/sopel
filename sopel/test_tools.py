# coding=utf-8
"""This module has classes and functions that can help in writing tests.

test_tools.py - Sopel misc tools
Copyright 2013, Ari Koivula, <ari@koivu.la>
Licensed under the Eiffel Forum License 2.

https://sopel.chat
"""
from __future__ import unicode_literals, absolute_import, print_function, division

import os
import re
import sys
import tempfile

try:
    import ConfigParser
except ImportError:
    import configparser as ConfigParser

import sopel.config
import sopel.config.core_section
import sopel.tools
import sopel.trigger


class MockConfig(sopel.config.Config):
    def __init__(self):
        self.filename = tempfile.mkstemp()[1]
        #self._homedir = tempfile.mkdtemp()
        #self.filename = os.path.join(self._homedir, 'test.cfg')
        self.parser = ConfigParser.RawConfigParser(allow_no_value=True)
        self.parser.add_section('core')
        self.parser.set('core', 'owner', 'Embolalia')
        self.define_section('core', sopel.config.core_section.CoreSection)
        self.get = self.parser.get

    def define_section(self, name, cls_):
        if not self.parser.has_section(name):
            self.parser.add_section(name)
        setattr(self, name, cls_(self, name))


class MockSopel(object):
    def __init__(self, nick, admin=False, owner=False):
        self.nick = nick
        self.user = "sopel"

        channel = sopel.tools.Identifier("#Sopel")
        self.channels = sopel.tools.SopelMemory()
        self.channels[channel] = sopel.tools.target.Channel(channel)

        self.memory = sopel.tools.SopelMemory()

        self.ops = {}
        self.halfplus = {}
        self.voices = {}

        self.config = MockConfig()
        self._init_config()

        if admin:
            self.config.core.admins = [self.nick]
        if owner:
            self.config.core.owner = self.nick

    def _init_config(self):
        cfg = self.config
        cfg.parser.set('core', 'admins', '')
        cfg.parser.set('core', 'owner', '')
        home_dir = os.path.join(os.path.expanduser('~'), '.sopel')
        if not os.path.exists(home_dir):
            os.mkdir(home_dir)
        cfg.parser.set('core', 'homedir', home_dir)


class MockSopelWrapper(object):
    def __init__(self, bot, pretrigger):
        self.bot = bot
        self.pretrigger = pretrigger
        self.output = []

    def _store(self, string, recipent=None):
        self.output.append(string.strip())

    say = reply = action = _store

    def __getattr__(self, attr):
        return getattr(self.bot, attr)


def get_example_test(tested_func, msg, results, privmsg, admin,
                     owner, repeat, use_regexp, ignore=[]):
    """Get a function that calls tested_func with fake wrapper and trigger.

    Args:
        tested_func - A sopel callable that accepts SopelWrapper and Trigger.
        msg - Message that is supposed to trigger the command.
        results - Expected output from the callable.
        privmsg - If true, make the message appear to have sent in a private
            message to the bot. If false, make it appear to have come from a
            channel.
        admin - If true, make the message appear to have come from an admin.
        owner - If true, make the message appear to have come from an owner.
        repeat - How many times to repeat the test. Useful for tests that
            return random stuff.
        use_regexp = Bool. If true, results is in regexp format.
        ignore - List of strings to ignore.

    """
    def test():
        bot = MockSopel("NickName", admin=admin, owner=owner)

        match = None
        if hasattr(tested_func, "commands"):
            for command in tested_func.commands:
                regexp = sopel.tools.get_command_regexp(".", command)
                match = regexp.match(msg)
                if match:
                    break
        assert match, "Example did not match any command."

        sender = bot.nick if privmsg else "#channel"
        hostmask = "%s!%s@%s " % (bot.nick, "UserName", "example.com")
        # TODO enable message tags
        full_message = ':{} PRIVMSG {} :{}'.format(hostmask, sender, msg)

        pretrigger = sopel.trigger.PreTrigger(bot.nick, full_message)
        trigger = sopel.trigger.Trigger(bot.config, pretrigger, match)

        module = sys.modules[tested_func.__module__]
        if hasattr(module, 'setup'):
            module.setup(bot)

        def isnt_ignored(value):
            """Return True if value doesn't match any re in ignore list."""
            for ignored_line in ignore:
                if re.match(ignored_line, value):
                    return False
            return True

        for _i in range(repeat):
            wrapper = MockSopelWrapper(bot, trigger)
            tested_func(wrapper, trigger)
            wrapper.output = list(filter(isnt_ignored, wrapper.output))
            assert len(wrapper.output) == len(results)
            for result, output in zip(results, wrapper.output):
                if type(output) is bytes:
                    output = output.decode('utf-8')
                if use_regexp:
                    if not re.match(result, output):
                        assert result == output
                else:
                    assert result == output

    return test


def get_disable_setup():
    import pytest
    import py

    @pytest.fixture(autouse=True)
    def disable_setup(request, monkeypatch):
        setup = getattr(request.module, "setup", None)
        isfixture = hasattr(setup, "_pytestfixturefunction")
        if setup is not None and not isfixture and py.builtin.callable(setup):
            monkeypatch.setattr(setup, "_pytestfixturefunction", pytest.fixture(), raising=False)
    return disable_setup


def insert_into_module(func, module_name, base_name, prefix):
    """Add a function into a module."""
    func.__module__ = module_name
    module = sys.modules[module_name]
    # Make sure the func method does not overwrite anything.
    for i in range(1000):
        func.__name__ = str("%s_%s_%s" % (prefix, base_name, i))
        if not hasattr(module, func.__name__):
            break
    setattr(module, func.__name__, func)


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
