# coding=utf-8
"""Pytest plugin for Sopel.

.. versionadded:: 7.0
"""
from __future__ import unicode_literals, absolute_import, print_function, division

import pytest

from .factories import BotFactory, ConfigFactory, TriggerFactory, IRCFactory, UserFactory


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

            irc.say(user, '#test', '.mycommand'))

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
