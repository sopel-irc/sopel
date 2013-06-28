# coding=utf-8
"""This module has classes and functions that can help in writing tests.

test_tools.py - Willie misc tools
Copyright 2013, Ari Koivula, <ari@koivu.la>
Licensed under the Eiffel Forum License 2.

https://willie.dftba.net
"""
import sys
import re

import willie.config
import willie.bot
import willie.irc
import willie.tools


class MockWillie(object):
    def __init__(self, nick, admin=False, owner=False):
        self.nick = nick
        self.user = "willie"

        self.channels = ["#channel"]

        self.memory = willie.tools.WillieMemory()

        self.ops = {}
        self.halfplus = {}
        self.voices = {}

        self.config = willie.config.Config('', load=False)
        self._init_config()

        if admin:
            self.config.admins = self.nick
        if owner:
            self.config.owner = self.nick

    def _init_config(self):
        cfg = self.config
        cfg.parser.set('core', 'admins', '')
        cfg.parser.set('core', 'owner', '')


class MockWillieWrapper(object):
    def __init__(self, bot, origin):
        self.bot = bot
        self.origin = origin
        self.output = []

    def _store(self, string, recipent=None):
        self.output.append(string.strip())

    say = reply = action = _store

    def __getattr__(self, attr):
        return getattr(self.bot, attr)


def get_example_test(tested_func, msg, results, privmsg, admin,
        owner, repeat, use_regexp):
    """Get a function that calls tested_func with fake wrapper and trigger.

    Args:
        tested_func - A willie callable that accepts WillieWrapper and Trigger.
        msg - Message that is supposed to trigger the command.
        results - Expected output from the callable.
        privmsg - If true, make the message appear to have sent in a private
            message to the bot. If false, make it appear to have come from a
            channel.
        admin - If true, make the message appear to have come from an admin.
        owner - If true, make the message appear to have come from an owner.
        repeat - How many times to repeat the test. Usefull for tests that
            return random stuff.
        use_regexp = Bool. If true, results is in regexp format.
    """
    def test():
        bot = MockWillie("NickName", admin=admin, owner=owner)

        match = None
        if hasattr(tested_func, "commands"):
            for command in tested_func.commands:
                regexp = willie.tools.get_command_regexp(".", command)
                match = regexp.match(msg)
                if match:
                    break
        assert match, "Example did not match any command."

        sender = bot.nick if privmsg else "#channel"
        hostmask = "%s!%s@%s" % (bot.nick, "UserName", "example.com")
        origin_args = ["PRIVMSG", sender, msg]

        origin = willie.irc.Origin(bot, hostmask, origin_args)
        trigger = willie.bot.Willie.Trigger(
                msg, origin, msg, match, origin_args[0], origin_args, bot)

        module = sys.modules[tested_func.__module__]
        if hasattr(module, 'setup'):
            module.setup(bot)

        for _i in xrange(repeat):
            wrapper = MockWillieWrapper(bot, origin)
            tested_func(wrapper, trigger)
            assert len(wrapper.output) == len(results)
            for result, output in zip(results, wrapper.output):
                if use_regexp:
                    assert re.match(result, output) is not None
                else:
                    assert result == output

    return test


def insert_into_module(func, module_name, base_name, prefix):
    """Add a function into a module
    """
    func.__module__ = module_name
    module = sys.modules[module_name]
    # Make sure the func method does not overwrite anything.
    for i in xrange(1000):
        func.__name__ = "%s_%s_%s" % (prefix, base_name, i)
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
