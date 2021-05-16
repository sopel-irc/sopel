# coding=utf-8
"""Pytest plugin for Sopel.

.. versionadded:: 7.0
"""
from __future__ import absolute_import, division, print_function, unicode_literals

import re
import sys

import pytest

from sopel import bot, loader, plugins, trigger
from .factories import BotFactory, ConfigFactory, IRCFactory, TriggerFactory, UserFactory


TEMPLATE_TEST_CONFIG = """
[core]
nick = {name}
owner = {owner}
admin = {admin}
"""


def get_disable_setup():
    """Generate a pytest fixture to setup the plugin before running its tests.

    When using ``@example`` for a plugin callable with an expected output,
    pytest will be used to run it as a test. In order to work, this fixture
    must be added to the plugin to set up the plugin before running the test.
    """
    @pytest.fixture(autouse=True)
    def disable_setup(request, monkeypatch):
        setup = getattr(request.module, "setup", None)
        isfixture = hasattr(setup, "_pytestfixturefunction")
        if setup is not None and not isfixture and callable(setup):
            monkeypatch.setattr(
                setup,
                "_pytestfixturefunction",
                pytest.fixture(),
                raising=False,
            )
    return disable_setup


def get_example_test(tested_func, msg, results, privmsg, admin,
                     owner, repeat, use_regexp, ignore=[]):
    """Get a function that calls ``tested_func`` with fake wrapper and trigger.

    :param callable tested_func: a Sopel callable that accepts a
                                 :class:`~.bot.SopelWrapper` and a
                                 :class:`~.trigger.Trigger`
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
        test_config = TEMPLATE_TEST_CONFIG.format(
            name='NickName',
            admin=admin,
            owner=owner,
        )
        settings = configfactory('default.cfg', test_config)
        url_schemes = settings.core.auto_url_schemes
        mockbot = botfactory(settings)
        server = ircfactory(mockbot)
        server.channel_joined('#Sopel')

        if not hasattr(tested_func, 'commands'):
            raise AssertionError('Function is not a command.')

        loader.clean_callable(tested_func, settings)
        test_rule = plugins.rules.Command.from_callable(settings, tested_func)
        parse_results = list(test_rule.parse(msg))
        assert parse_results, "Example did not match any command."

        match = parse_results[0]
        sender = mockbot.nick if privmsg else "#channel"
        hostmask = "%s!%s@%s" % (mockbot.nick, "UserName", "example.com")

        # TODO enable message tags
        full_message = ':{} PRIVMSG {} :{}'.format(hostmask, sender, msg)
        pretrigger = trigger.PreTrigger(
            mockbot.nick, full_message, url_schemes=url_schemes)
        test_trigger = trigger.Trigger(mockbot.settings, pretrigger, match)
        pattern = re.compile(r'^%s: ' % re.escape(mockbot.nick))

        # setup module
        module = sys.modules[tested_func.__module__]
        if hasattr(module, 'setup'):
            module.setup(mockbot)

        def isnt_ignored(value):
            """Return True if value doesn't match any re in ignore list."""
            return not any(
                re.match(ignored_line, value)
                for ignored_line in ignore)

        expected_output_count = 0
        for _i in range(repeat):
            expected_output_count += len(results)
            wrapper = bot.SopelWrapper(mockbot, test_trigger)
            tested_func(wrapper, test_trigger)

            output_triggers = (
                trigger.PreTrigger(
                    mockbot.nick,
                    message.decode('utf-8'),
                    url_schemes=url_schemes,
                )
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
                    message = (
                        "Output does not match the regex:\n"
                        "Pattern: %s\n"
                        "Output: %s"
                    ) % (expected, output)
                    if not re.match(expected, output):
                        raise AssertionError(message)
                else:
                    assert expected == output

    return test


def insert_into_module(func, module_name, base_name, prefix):
    """Add a function into a module.

    This can be used to add a test function, a setup function, or a fixture
    to an existing module to be used with pytest.
    """
    func.__module__ = module_name
    module = sys.modules[module_name]
    # Make sure the func method does not overwrite anything.
    for i in range(1000):
        func.__name__ = str("%s_%s_%s" % (prefix, base_name, i))
        if not hasattr(module, func.__name__):
            break
    else:
        # 1000 variations of this function's name already exist
        raise RuntimeError('Unable to insert function %s into module %s' % (
            func.__name__, func.__module__
        ))
    setattr(module, func.__name__, func)


@pytest.fixture
def botfactory():
    """Fixture to get a Bot factory.

    :return: a factory to create a mocked bot instance
    :rtype: :class:`sopel.tests.factories.BotFactory`

    This is very useful in unit tests::

        def test_bot(configfactory, botfactory):
            settings = configfactory('... skip for clarity ...')
            bot = botfactory(settings) # no plugins loaded
            # ... do something with the bot

        def test_bot_loaded(configfactory, botfactory):
            settings = configfactory('... skip for clarity ...')
            bot = botfactory.preloaded(settings, ['myplugin'])
            # now the bot has `coretasks` and `myplugin` loaded
    """
    return BotFactory()


@pytest.fixture
def configfactory(tmpdir):
    """Fixture to get a config factory.

    :return: a factory to create test settings
    :rtype: :class:`sopel.tests.factories.ConfigFactory`

    The factory will be automatically configured with a ``tmpdir`` object.
    """
    return ConfigFactory(tmpdir)


@pytest.fixture
def triggerfactory():
    """Fixture to get a trigger factory.

    :return: a factory to create triggers
    :rtype: :class:`sopel.tests.factories.TriggerFactory`
    """
    return TriggerFactory()


@pytest.fixture
def ircfactory():
    """Fixture to get an IRC factory.

    :return: a factory to create mock IRC servers
    :rtype: :class:`sopel.tests.factories.IRCFactory`

    For example, a plugin command could be tested with this::

        from sopel.tests import rawlist

        def test_mycommand(configfactory, botfactory, ircfactory, userfactory):
            settings = configfactory('... skip for clarity ...')
            bot = botfactory(settings, ['myplugin'])
            irc = ircfactory(bot)
            user = userfactory('User')

            irc.say(user, '#test', '.mycommand')

            assert bot.backend.message_sent == rawlist(
                'PRIVMSG #test :My plugin replied this.'
            )
    """
    return IRCFactory()


@pytest.fixture
def userfactory():
    """Fixture to get a user factory.

    :return: a factory to create mock users
    :rtype: :class:`sopel.tests.factories.UserFactory`

    ::

        def test_mycommand(userfactory):
            user = userfactory('User')

            assert user.nick == 'User'
            assert user.user == 'user'
            assert user.host == 'example.com'
            assert user.prefix == 'User!user@example.com'
    """
    return UserFactory()
