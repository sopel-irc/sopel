# coding=utf-8
"""This module has classes and functions that can help in writing tests.

.. note::

   This module formerly contained mock classes for bot, bot wrapper, and config
   objects. Those are deprecated, and will be removed in Sopel 8.0. New code
   should use the new :mod:`.mocks`, :mod:`.factories`, and
   :mod:`.pytest_plugin` added in Sopel 7.0.

"""
# Copyright 2013, Ari Koivula, <ari@koivu.la>
# Copyright 2019, Florian Strzelecki <florian.strzelecki@gmail.com>
# Licensed under the Eiffel Forum License 2.
from __future__ import unicode_literals, absolute_import, print_function, division

import os
import re
import sys
import tempfile

try:
    import ConfigParser
except ImportError:
    import configparser as ConfigParser

from sopel.bot import SopelWrapper
import sopel.config
import sopel.config.core_section
import sopel.plugins
import sopel.tools
import sopel.tools.target
import sopel.trigger


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


class MockConfig(sopel.config.Config):
    @sopel.tools.deprecated('use configfactory fixture instead', '7.0', '8.0')
    def __init__(self):
        self.filename = tempfile.mkstemp()[1]
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
    @sopel.tools.deprecated('use botfactory fixture instead', '7.0', '8.0')
    def __init__(self, nick, admin=False, owner=False):
        self.nick = nick
        self.user = "sopel"

        channel = sopel.tools.Identifier("#Sopel")
        self.channels = sopel.tools.SopelMemory()
        self.channels[channel] = sopel.tools.target.Channel(channel)

        self.users = sopel.tools.SopelMemory()
        self.privileges = sopel.tools.SopelMemory()

        self.memory = sopel.tools.SopelMemory()
        self.memory['url_callbacks'] = sopel.tools.SopelMemory()

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
        for regex, function in sopel.tools.iteritems(self.memory['url_callbacks']):
            match = regex.search(url)
            if match:
                yield function, match


class MockSopelWrapper(SopelWrapper):
    @sopel.tools.deprecated('use sopel.bot.SopelWrapper instead', '7.0', '8.0')
    def __init__(self, *args, **kwargs):
        super(MockSopelWrapper, self).__init__(*args, **kwargs)


TEST_CONFIG = """
[core]
nick = {name}
owner = {owner}
admin = {admin}
"""


def get_example_test(tested_func, msg, results, privmsg, admin,
                     owner, repeat, use_regexp, ignore=[]):
    """Get a function that calls ``tested_func`` with fake wrapper and trigger.

    :param callable tested_func: a Sopel callable that accepts a
        :class:`~.bot.SopelWrapper` and a :class:`~.trigger.Trigger`
    :param str msg: message that is supposed to trigger the command
    :param list results: expected output from the callable
    :param bool privmsg: if ``True``, make the message appear to have arrived
                         in a private message to the bot; otherwise make it
                         appear to have come from a channel
    :param bool admin: make the message appear to have come from an admin
    :param bool owner: make the message appear to have come from an owner
    :param int repeat: how many times to repeat the test; useful for tests that
                       return random stuff
    :param bool use_regexp: pass ``True`` if ``results`` are in regexp format
    :param list ignore: strings to ignore
    :return: a test function for ``tested_func``
    :rtype: :term:`function`
    """
    def test(configfactory, botfactory, ircfactory):
        test_config = TEST_CONFIG.format(
            name='NickName',
            admin=admin,
            owner=owner,
        )
        settings = configfactory('default.cfg', test_config)
        bot = botfactory(settings)
        server = ircfactory(bot)
        server.channel_joined('#Sopel')

        match = None
        if hasattr(tested_func, "commands"):
            for command in tested_func.commands:
                regexp = sopel.tools.get_command_regexp(".", command)
                match = regexp.match(msg)
                if match:
                    break
        assert match, "Example did not match any command."

        sender = bot.nick if privmsg else "#channel"
        hostmask = "%s!%s@%s" % (bot.nick, "UserName", "example.com")

        # TODO enable message tags
        full_message = ':{} PRIVMSG {} :{}'.format(hostmask, sender, msg)
        pretrigger = sopel.trigger.PreTrigger(bot.nick, full_message)
        trigger = sopel.trigger.Trigger(bot.settings, pretrigger, match)
        pattern = re.compile(r'^%s: ' % re.escape(bot.nick))

        # setup module
        module = sys.modules[tested_func.__module__]
        if hasattr(module, 'setup'):
            module.setup(bot)

        def isnt_ignored(value):
            """Return True if value doesn't match any re in ignore list."""
            return not any(
                re.match(ignored_line, value)
                for ignored_line in ignore)

        expected_output_count = 0
        for _i in range(repeat):
            expected_output_count += len(results)
            wrapper = SopelWrapper(bot, trigger)
            tested_func(wrapper, trigger)

            output_triggers = (
                sopel.trigger.PreTrigger(bot.nick, message.decode('utf-8'))
                for message in wrapper.backend.message_sent
            )
            output_texts = (
                # subtract "Sopel: " when necessary
                pattern.sub('', output_trigger.args[-1])
                for output_trigger in output_triggers
            )
            outputs = [text for text in output_texts if isnt_ignored(text)]

            # output length
            assert len(outputs) == expected_output_count

            # output content
            for expected, output in zip(results, outputs):
                if use_regexp:
                    if not re.match(expected, output):
                        assert expected == output
                else:
                    assert expected == output

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
