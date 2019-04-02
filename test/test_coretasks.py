# coding=utf-8
"""Test for Sopel core tasks."""
from __future__ import unicode_literals, absolute_import, print_function, division

import pytest

from sopel.test_tools import MockSopel, MockSopelWrapper
from sopel.tools import Identifier
from sopel.trigger import PreTrigger, Trigger


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


def test_pass(dummy_bot_trigger):
    bot, trigger = dummy_bot_trigger
    assert True
