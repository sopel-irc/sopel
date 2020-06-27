# coding=utf-8
"""Tests for sopel.module decorators

.. important::

    These tests are kept here as a proof that ``sopel.module`` is backward
    compatible up to Sopel 9, when it will be removed.

"""
from __future__ import absolute_import, division, print_function, unicode_literals

import pytest

from sopel import module, tools
from sopel.trigger import PreTrigger, Trigger


TMP_CONFIG = """
[core]
owner = Bar
nick = Sopel
enable = coretasks
"""


FOO_MESSAGE = ':Foo!foo@example.com PRIVMSG #Sopel :Hello, world'
FOO_PRIV_MESSAGE = ':Foo!foo@example.com PRIVMSG Sopel :Hello, world'


@pytest.fixture
def bot(configfactory, botfactory, triggerfactory, ircfactory):
    settings = configfactory('default.cfg', TMP_CONFIG)
    mockbot = botfactory.preloaded(settings)
    mockserver = ircfactory(mockbot)

    bot = triggerfactory.wrapper(mockbot, FOO_MESSAGE)
    mockserver.channel_joined('#Sopel')
    mockserver.join('Foo', '#Sopel')
    mockserver.mode_set('#Sopel', '+v', ['Foo'])

    return bot


@pytest.fixture
def pretrigger():
    return PreTrigger(tools.Identifier('Foo'), FOO_MESSAGE)


@pytest.fixture
def pretrigger_pm():
    return PreTrigger(tools.Identifier('Foo'), FOO_PRIV_MESSAGE)


@pytest.fixture
def trigger_owner(bot):
    line = ':Bar!bar@example.com PRIVMSG #Sopel :Hello, world'
    return Trigger(bot.config, PreTrigger(tools.Identifier('Bar'), line), None)


@pytest.fixture
def trigger_account(bot):
    line = '@account=egg :egg!egg@eg.gs PRIVMSG #Sopel :Hello, world'
    return Trigger(
        bot.config,
        PreTrigger(tools.Identifier('egg'), line),
        None,
        'egg')


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
    patterns = [regex.pattern for regex in mock.url_regex]
    assert len(patterns) == 1
    assert 'pattern' in patterns


def test_url_args():
    @module.url('first', 'second')
    def mock(bot, trigger, match):
        return True

    patterns = [regex.pattern for regex in mock.url_regex]
    assert len(patterns) == 2
    assert 'first' in patterns
    assert 'second' in patterns


def test_url_multiple():
    @module.url('first', 'second')
    @module.url('second')
    @module.url('third')
    def mock(bot, trigger, match):
        return True

    patterns = [regex.pattern for regex in mock.url_regex]
    assert len(patterns) == 3
    assert 'first' in patterns
    assert 'second' in patterns
    assert 'third' in patterns


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
    assert not hasattr(mock, 'rule')


def test_commands_args():
    @module.commands('sopel', 'bot')
    def mock(bot, trigger, match):
        return True
    assert mock.commands == ['sopel', 'bot']
    assert not hasattr(mock, 'rule')


def test_commands_multiple():
    @module.commands('sopel', 'bot')
    @module.commands('bot')
    @module.commands('robot')
    def mock(bot, trigger, match):
        return True
    assert mock.commands == ['robot', 'bot', 'sopel']
    assert not hasattr(mock, 'rule')


def test_nickname_commands():
    @module.nickname_commands('sopel')
    def mock(bot, trigger, match):
        return True
    assert mock.nickname_commands == ['sopel']
    assert not hasattr(mock, 'rule')


def test_nickname_commands_args():
    @module.nickname_commands('sopel', 'bot')
    def mock(bot, trigger, match):
        return True
    assert mock.nickname_commands == ['sopel', 'bot']
    assert not hasattr(mock, 'rule')


def test_nickname_commands_multiple():
    @module.nickname_commands('sopel', 'bot')
    @module.nickname_commands('bot')
    @module.nickname_commands('robot')
    def mock(bot, trigger, match):
        return True
    assert mock.nickname_commands == ['robot', 'bot', 'sopel']
    assert not hasattr(mock, 'rule')


def test_action_commands():
    @module.action_commands('sopel')
    def mock(bot, trigger, match):
        return True
    assert mock.action_commands == ['sopel']
    assert not hasattr(mock, 'intents')
    assert not hasattr(mock, 'rule')


def test_action_commands_args():
    @module.action_commands('sopel', 'bot')
    def mock(bot, trigger, match):
        return True
    assert mock.action_commands == ['sopel', 'bot']
    assert not hasattr(mock, 'intents')
    assert not hasattr(mock, 'rule')


def test_action_commands_multiple():
    @module.action_commands('sopel', 'bot')
    @module.action_commands('bot')
    @module.action_commands('robot')
    def mock(bot, trigger, match):
        return True
    assert mock.action_commands == ['robot', 'bot', 'sopel']
    assert not hasattr(mock, 'intents')
    assert not hasattr(mock, 'rule')


def test_all_commands():
    @module.commands('sopel')
    @module.action_commands('me_sopel')
    @module.nickname_commands('name_sopel')
    def mock(bot, trigger, match):
        return True

    assert mock.commands == ['sopel']
    assert mock.action_commands == ['me_sopel']
    assert mock.nickname_commands == ['name_sopel']
    assert not hasattr(mock, 'intents')
    assert not hasattr(mock, 'rule')


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
    assert mock_(bot, trigger) is True
    assert mock_(bot, trigger_pm) is not True


def test_require_account(bot, trigger, trigger_account):
    @module.require_account('You need to authenticate to services first.')
    def mock(bot, trigger, match=None):
        return True
    assert mock(bot, trigger) is not True
    assert mock(bot, trigger_account) is True

    @module.require_account
    def mock_(bot, trigger, match=None):
        return True
    assert mock_(bot, trigger) is not True
    assert mock_(bot, trigger_account) is True


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


def test_output_prefix():
    @module.commands('mock')
    @module.output_prefix('[MOCK] ')
    def mock(bot, trigger, match):
        return True
    assert mock.output_prefix == '[MOCK] '
