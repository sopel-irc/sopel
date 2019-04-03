# coding=utf-8
"""Test for Sopel core tasks."""
from __future__ import unicode_literals, absolute_import, print_function, division

import pytest

from sopel import coretasks
from sopel.test_tools import MockSopel, MockSopelWrapper
from sopel.tools import Identifier
from sopel.trigger import PreTrigger, Trigger

# Constants
AUTH_USERNAME = "BotUsername"
AUTH_PASSWORD = "Password123"


@pytest.fixture
def nick():
    return Identifier('Sopel')


@pytest.fixture
def sopel(nick):
    bot = MockSopel(nick)
    bot.config.core.owner = 'Bar'

    return bot


@pytest.fixture
def bot(sopel):
    def _fn(pretrigger):
        return MockSopelWrapper(sopel, pretrigger)
    return _fn


@pytest.fixture
def get_bot_trigger(bot, nick):
    def _fn(line):
        pretrigger = PreTrigger(nick, line)
        _bot = bot(pretrigger)
        return _bot, Trigger(_bot.config, pretrigger, None)
    return _fn


@pytest.fixture
def dummy_bot_trigger(get_bot_trigger):
    line = ':Foo!foo@fake-server.example.net PRIVMSG #Sopel :fake news...'
    return get_bot_trigger(line)


@pytest.fixture
def bot_with_auth(dummy_bot_trigger):
    def _fn(auth_method=None, auth_username=None, auth_password=None, auth_target=None):
        bot, _ = dummy_bot_trigger
        bot.config.core.auth_method = auth_method
        bot.config.core.auth_username = auth_username
        bot.config.core.auth_password = auth_password
        bot.config.core.auth_target = auth_target
        return bot
    return _fn


def test_pass(dummy_bot_trigger):
    bot, trigger = dummy_bot_trigger
    assert True


def test_auth_nickserv(bot_with_auth, mocker):
    bot = bot_with_auth(
        auth_method='nickserv',
        auth_password=AUTH_PASSWORD,
    )

    mocker.patch.object(bot, 'msg', autospec=True)

    coretasks.auth_after_register(bot)

    bot.msg.assert_called_once_with('NickServ', 'IDENTIFY {}'.format(AUTH_PASSWORD))


def test_auth_authserv(bot_with_auth, mocker):
    bot = bot_with_auth(
        auth_method='authserv',
        auth_username=AUTH_USERNAME,
        auth_password=AUTH_PASSWORD,
    )

    mocker.patch.object(bot, 'write', autospec=True)

    coretasks.auth_after_register(bot)

    bot.write.assert_called_once_with(('AUTHSERV auth', '{} {}'.format(AUTH_USERNAME, AUTH_PASSWORD)))


def test_auth_Q(bot_with_auth, mocker):
    bot = bot_with_auth(
        auth_method='Q',
        auth_username=AUTH_USERNAME,
        auth_password=AUTH_PASSWORD,
    )

    mocker.patch.object(bot, 'write', autospec=True)

    coretasks.auth_after_register(bot)

    bot.write.assert_called_once_with(('AUTH', '{} {}'.format(AUTH_USERNAME, AUTH_PASSWORD)))


def test_auth_userserv(bot_with_auth, mocker):
    bot = bot_with_auth(
        auth_method='userserv',
        auth_username=AUTH_USERNAME,
        auth_password=AUTH_PASSWORD,
    )

    mocker.patch.object(bot, 'msg', autospec=True)

    coretasks.auth_after_register(bot)

    bot.msg.assert_called_once_with('UserServ', 'LOGIN {} {}'.format(AUTH_USERNAME, AUTH_PASSWORD))
