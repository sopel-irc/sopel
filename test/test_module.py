# coding=utf-8
"""Tests for message formatting"""
from __future__ import unicode_literals, absolute_import, print_function, division

import re

import pytest

from sopel.trigger import PreTrigger, Trigger
from sopel.test_tools import MockSopel, MockSopelWrapper
from sopel.tools import Identifier
from sopel import module


@pytest.fixture
def sopel():
    bot = MockSopel('Sopel')
    bot.config.core.owner = 'Bar'
    return bot


@pytest.fixture
def bot(sopel, pretrigger):
    bot = MockSopelWrapper(sopel, pretrigger)
    bot.channels[Identifier('#Sopel')].privileges[Identifier('Foo')] = module.VOICE
    return bot


@pytest.fixture
def pretrigger():
    line = ':Foo!foo@example.com PRIVMSG #Sopel :Hello, world'
    return PreTrigger(Identifier('Foo'), line)


@pytest.fixture
def pretrigger_pm():
    line = ':Foo!foo@example.com PRIVMSG Sopel :Hello, world'
    return PreTrigger(Identifier('Foo'), line)


@pytest.fixture
def trigger_owner(bot):
    line = ':Bar!bar@example.com PRIVMSG #Sopel :Hello, world'
    return Trigger(bot.config, PreTrigger(Identifier('Bar'), line), None)


@pytest.fixture
def trigger(bot, pretrigger):
    return Trigger(bot.config, pretrigger, None)


@pytest.fixture
def trigger_pm(bot, pretrigger_pm):
    return Trigger(bot.config, pretrigger_pm, None)


def test_unblockable():
    @module.unblockable
    def mock(bot, trigger, match):
        return True
    assert mock.unblockable is True


def test_interval():
    @module.interval(5)
    def mock(bot, trigger, match):
        return True
    assert mock.interval == [5]


def test_interval_args():
    @module.interval(5, 10)
    def mock(bot, trigger, match):
        return True
    assert mock.interval == [5, 10]


def test_interval_multiple():
    @module.interval(5, 10)
    @module.interval(5)
    @module.interval(20)
    def mock(bot, trigger, match):
        return True
    assert mock.interval == [20, 5, 10]


def test_rule():
    @module.rule('.*')
    def mock(bot, trigger, match):
        return True
    assert mock.rule == ['.*']


def test_rule_args():
    @module.rule('.*', r'\d+')
    def mock(bot, trigger, match):
        return True
    assert mock.rule == ['.*', r'\d+']


def test_rule_multiple():
    @module.rule('.*', r'\d+')
    @module.rule('.*')
    @module.rule(r'\w+')
    def mock(bot, trigger, match):
        return True
    assert mock.rule == [r'\w+', '.*', r'\d+']


def test_thread():
    @module.thread(True)
    def mock(bot, trigger, match):
        return True
    assert mock.thread is True


def test_url():
    @module.url('pattern')
    def mock(bot, trigger, match):
        return True
    assert mock.url_regex == [re.compile('pattern')]


def test_url_args():
    @module.url('first', 'second')
    def mock(bot, trigger, match):
        return True
    assert mock.url_regex == [re.compile('first'), re.compile('second')]


def test_url_multiple():
    @module.url('first', 'second')
    @module.url('second')
    @module.url('third')
    def mock(bot, trigger, match):
        return True
    assert mock.url_regex == [
        re.compile('third'),
        re.compile('second'),
        re.compile('first')
    ]


def test_echo():
    # test decorator with parentheses
    @module.echo()
    def mock(bot, trigger, match):
        return True
    assert mock.echo is True

    # test decorator without parentheses
    @module.echo
    def mock(bot, trigger, match):
        return True
    assert mock.echo is True

    # test without decorator
    def mock(bot, trigger, match):
        return True
    # on undecorated callables, the attr only exists after the loader loads them
    # so this cannot `assert mock.echo is False` here
    assert not hasattr(mock, 'echo')


def test_commands():
    @module.commands('sopel')
    def mock(bot, trigger, match):
        return True
    assert mock.commands == ['sopel']


def test_commands_args():
    @module.commands('sopel', 'bot')
    def mock(bot, trigger, match):
        return True
    assert mock.commands == ['sopel', 'bot']


def test_commands_multiple():
    @module.commands('sopel', 'bot')
    @module.commands('bot')
    @module.commands('robot')
    def mock(bot, trigger, match):
        return True
    assert mock.commands == ['robot', 'bot', 'sopel']


def test_nickname_commands():
    @module.nickname_commands('sopel')
    def mock(bot, trigger, match):
        return True
    assert mock.nickname_commands == ['sopel']


def test_nickname_commands_args():
    @module.nickname_commands('sopel', 'bot')
    def mock(bot, trigger, match):
        return True
    assert mock.nickname_commands == ['sopel', 'bot']


def test_nickname_commands_multiple():
    @module.nickname_commands('sopel', 'bot')
    @module.nickname_commands('bot')
    @module.nickname_commands('robot')
    def mock(bot, trigger, match):
        return True
    assert mock.nickname_commands == ['robot', 'bot', 'sopel']


def test_priority():
    @module.priority('high')
    def mock(bot, trigger, match):
        return True
    assert mock.priority == 'high'


def test_event():
    @module.event('301')
    def mock(bot, trigger, match):
        return True
    assert mock.event == ['301']


def test_event_args():
    @module.event('301', '302')
    def mock(bot, trigger, match):
        return True
    assert mock.event == ['301', '302']


def test_event_multiple():
    @module.event('301', '302')
    @module.event('301')
    @module.event('466')
    def mock(bot, trigger, match):
        return True
    assert mock.event == ['466', '301', '302']


def test_intent():
    @module.intent('ACTION')
    def mock(bot, trigger, match):
        return True
    assert mock.intents == ['ACTION']


def test_intent_args():
    @module.intent('ACTION', 'OTHER')
    def mock(bot, trigger, match):
        return True
    assert mock.intents == ['ACTION', 'OTHER']


def test_intent_multiple():
    @module.intent('ACTION', 'OTHER')
    @module.intent('OTHER')
    @module.intent('PING',)
    def mock(bot, trigger, match):
        return True
    assert mock.intents == ['PING', 'OTHER', 'ACTION']


def test_rate():
    @module.rate(5)
    def mock(bot, trigger, match):
        return True
    assert mock.rate == 5


def test_require_privmsg(bot, trigger, trigger_pm):
    @module.require_privmsg('Try again in a PM')
    def mock(bot, trigger, match=None):
        return True
    assert mock(bot, trigger) is not True
    assert mock(bot, trigger_pm) is True

    @module.require_privmsg
    def mock_(bot, trigger, match=None):
        return True
    assert mock_(bot, trigger) is not True
    assert mock_(bot, trigger_pm) is True


def test_require_chanmsg(bot, trigger, trigger_pm):
    @module.require_chanmsg('Try again in a channel')
    def mock(bot, trigger, match=None):
        return True
    assert mock(bot, trigger) is True
    assert mock(bot, trigger_pm) is not True

    @module.require_chanmsg
    def mock_(bot, trigger, match=None):
        return True
    assert mock(bot, trigger) is True
    assert mock(bot, trigger_pm) is not True


def test_require_privilege(bot, trigger):
    @module.require_privilege(module.VOICE)
    def mock_v(bot, trigger, match=None):
        return True
    assert mock_v(bot, trigger) is True

    @module.require_privilege(module.OP, 'You must be at least opped!')
    def mock_o(bot, trigger, match=None):
        return True
    assert mock_o(bot, trigger) is not True


def test_require_admin(bot, trigger, trigger_owner):
    @module.require_admin('You must be an admin')
    def mock(bot, trigger, match=None):
        return True
    assert mock(bot, trigger) is not True

    @module.require_admin
    def mock_(bot, trigger, match=None):
        return True
    assert mock_(bot, trigger_owner) is True


def test_require_owner(bot, trigger, trigger_owner):
    @module.require_owner('You must be an owner')
    def mock(bot, trigger, match=None):
        return True
    assert mock(bot, trigger) is not True

    @module.require_owner
    def mock_(bot, trigger, match=None):
        return True
    assert mock_(bot, trigger_owner) is True


def test_example(bot, trigger):
    @module.commands('mock')
    @module.example('.mock', 'True')
    def mock(bot, trigger, match=None):
        return True
    assert mock(bot, trigger) is True
