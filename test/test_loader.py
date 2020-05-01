# coding=utf-8
"""Tests for the ``sopel.loader`` module."""
from __future__ import unicode_literals, absolute_import, print_function, division

import inspect
import re

import pytest

from sopel import loader, module, plugins


MOCK_MODULE_CONTENT = """# coding=utf-8
import sopel.module


@sopel.module.commands("first")
def first_command(bot, trigger):
    pass


@sopel.module.commands("second")
def second_command(bot, trigger):
    pass


@sopel.module.interval(5)
def interval5s(bot):
    pass


@sopel.module.interval(10)
def interval10s(bot):
    pass


@sopel.module.url(r'.\\.example\\.com')
def example_url(bot):
    pass


@sopel.module.event('TOPIC')
def on_topic_command(bot):
    pass


def shutdown():
    pass


def ignored():
    pass

"""


@pytest.fixture
def func():
    """Pytest fixture to get a function that will return True all the time"""
    def bot_command():
        """Test callable defined as a pytest fixture."""
        return True
    return bot_command


TMP_CONFIG = """
[core]
owner = testnick
nick = TestBot
"""


@pytest.fixture
def tmpconfig(configfactory):
    return configfactory('conf.ini', TMP_CONFIG)


@pytest.fixture
def testplugin(tmpdir):
    root = tmpdir.mkdir('loader_mods')
    mod_file = root.join('file_mod.py')
    mod_file.write(MOCK_MODULE_CONTENT)

    return plugins.handlers.PyFilePlugin(mod_file.strpath)


def test_is_limitable(testplugin):
    """Test is_limitable behavior before clean_module is called."""
    testplugin.load()
    test_mod = testplugin._module

    assert loader.is_limitable(test_mod.first_command)
    assert loader.is_limitable(test_mod.second_command)
    assert loader.is_limitable(test_mod.on_topic_command)

    assert not loader.is_limitable(test_mod.interval5s)
    assert not loader.is_limitable(test_mod.interval10s)
    assert not loader.is_limitable(test_mod.shutdown)

    assert loader.is_limitable(test_mod.example_url)


def test_is_triggerable(testplugin):
    """Test is_triggerable behavior before clean_module is called."""
    testplugin.load()
    test_mod = testplugin._module

    assert loader.is_triggerable(test_mod.first_command)
    assert loader.is_triggerable(test_mod.second_command)
    assert loader.is_triggerable(test_mod.on_topic_command)

    assert not loader.is_triggerable(test_mod.interval5s)
    assert not loader.is_triggerable(test_mod.interval10s)

    assert not loader.is_triggerable(test_mod.shutdown)
    assert not loader.is_triggerable(test_mod.example_url)


def test_clean_module(testplugin, tmpconfig):
    testplugin.load()
    test_mod = testplugin._module

    callables, jobs, shutdowns, urls = loader.clean_module(
        test_mod, tmpconfig)

    assert len(callables) == 3
    assert test_mod.first_command in callables
    assert test_mod.second_command in callables
    assert test_mod.on_topic_command in callables
    assert len(jobs) == 2
    assert test_mod.interval5s in jobs
    assert test_mod.interval10s in jobs
    assert len(shutdowns)
    assert test_mod.shutdown in shutdowns
    assert len(urls) == 1
    assert test_mod.example_url in urls

    # assert is_triggerable behavior *after* clean_module has been called
    assert loader.is_triggerable(test_mod.first_command)
    assert loader.is_triggerable(test_mod.second_command)
    assert loader.is_triggerable(test_mod.on_topic_command)

    assert not loader.is_triggerable(test_mod.interval5s)
    assert not loader.is_triggerable(test_mod.interval10s)

    assert not loader.is_triggerable(test_mod.shutdown)
    assert not loader.is_triggerable(test_mod.example_url)

    # ignored function is ignored
    assert test_mod.ignored not in callables
    assert test_mod.ignored not in jobs
    assert test_mod.ignored not in shutdowns
    assert test_mod.ignored not in urls


def test_clean_module_idempotency(testplugin, tmpconfig):
    testplugin.load()
    test_mod = testplugin._module

    callables, jobs, shutdowns, urls = loader.clean_module(
        test_mod, tmpconfig)

    # sanity assertions: check test_clean_module if any of these fails
    assert len(callables) == 3
    assert len(jobs) == 2
    assert len(shutdowns) == 1
    assert len(urls) == 1

    # recall clean_module, we should have the same result
    new_callables, new_jobs, new_shutdowns, new_urls = loader.clean_module(
        test_mod, tmpconfig)

    assert new_callables == callables
    assert new_jobs == jobs
    assert new_shutdowns == shutdowns
    assert new_urls == urls

    # assert is_triggerable behavior
    assert loader.is_triggerable(test_mod.first_command)
    assert loader.is_triggerable(test_mod.second_command)
    assert loader.is_triggerable(test_mod.on_topic_command)

    assert not loader.is_triggerable(test_mod.interval5s)
    assert not loader.is_triggerable(test_mod.interval10s)

    assert not loader.is_triggerable(test_mod.shutdown)
    assert not loader.is_triggerable(test_mod.example_url)


def test_clean_callable_default(tmpconfig, func):
    loader.clean_callable(func, tmpconfig)

    # Default values
    assert hasattr(func, 'thread')
    assert func.thread is True

    # Not added by default
    assert not hasattr(func, 'unblockable')
    assert not hasattr(func, 'priority')
    assert not hasattr(func, 'rate')
    assert not hasattr(func, 'channel_rate')
    assert not hasattr(func, 'global_rate')
    assert not hasattr(func, 'event')
    assert not hasattr(func, 'rule')
    assert not hasattr(func, 'commands')
    assert not hasattr(func, 'nickname_commands')
    assert not hasattr(func, 'action_commands')
    assert not hasattr(func, 'intents')


def test_clean_callable_command(tmpconfig, func):
    setattr(func, 'commands', ['test'])
    loader.clean_callable(func, tmpconfig)

    # Default values
    assert hasattr(func, 'unblockable')
    assert func.unblockable is False
    assert hasattr(func, 'priority')
    assert func.priority == 'medium'
    assert hasattr(func, 'thread')
    assert func.thread is True
    assert hasattr(func, 'rate')
    assert func.rate == 0
    assert hasattr(func, 'channel_rate')
    assert func.channel_rate == 0
    assert hasattr(func, 'global_rate')
    assert func.global_rate == 0
    assert hasattr(func, 'event')
    assert func.event == ['PRIVMSG']
    assert hasattr(func, 'rule')
    assert len(func.rule) == 1


def test_clean_callable_event(tmpconfig, func):
    setattr(func, 'event', ['low', 'UP', 'MiXeD'])
    loader.clean_callable(func, tmpconfig)

    assert hasattr(func, 'event')
    assert func.event == ['LOW', 'UP', 'MIXED']

    # Default values
    assert hasattr(func, 'unblockable')
    assert func.unblockable is False
    assert hasattr(func, 'priority')
    assert func.priority == 'medium'
    assert hasattr(func, 'thread')
    assert func.thread is True
    assert hasattr(func, 'rate')
    assert func.rate == 0
    assert hasattr(func, 'channel_rate')
    assert func.channel_rate == 0
    assert hasattr(func, 'global_rate')
    assert func.global_rate == 0

    # idempotency
    loader.clean_callable(func, tmpconfig)
    assert func.event == ['LOW', 'UP', 'MIXED']

    assert func.unblockable is False
    assert func.priority == 'medium'
    assert func.thread is True
    assert func.rate == 0
    assert func.channel_rate == 0
    assert func.global_rate == 0


def test_clean_callable_event_string(tmpconfig, func):
    setattr(func, 'event', 'some')
    loader.clean_callable(func, tmpconfig)

    assert hasattr(func, 'event')
    assert func.event == ['SOME']

    # idempotency
    loader.clean_callable(func, tmpconfig)
    assert func.event == ['SOME']


def test_clean_callable_rule(tmpconfig, func):
    setattr(func, 'rule', [r'abc'])
    loader.clean_callable(func, tmpconfig)

    assert hasattr(func, 'rule')
    assert len(func.rule) == 1

    # Test the regex is compiled properly
    regex = func.rule[0]
    assert regex.match('abc')
    assert regex.match('abcd')
    assert not regex.match('efg')

    # Default values
    assert hasattr(func, 'unblockable')
    assert func.unblockable is False
    assert hasattr(func, 'priority')
    assert func.priority == 'medium'
    assert hasattr(func, 'thread')
    assert func.thread is True
    assert hasattr(func, 'rate')
    assert func.rate == 0
    assert hasattr(func, 'channel_rate')
    assert func.channel_rate == 0
    assert hasattr(func, 'global_rate')
    assert func.global_rate == 0

    # idempotency
    loader.clean_callable(func, tmpconfig)
    assert len(func.rule) == 1
    assert regex in func.rule

    assert func.unblockable is False
    assert func.priority == 'medium'
    assert func.thread is True
    assert func.rate == 0
    assert func.channel_rate == 0
    assert func.global_rate == 0


def test_clean_callable_rule_string(tmpconfig, func):
    setattr(func, 'rule', r'abc')
    loader.clean_callable(func, tmpconfig)

    assert hasattr(func, 'rule')
    assert len(func.rule) == 1

    # Test the regex is compiled properly
    regex = func.rule[0]
    assert regex.match('abc')
    assert regex.match('abcd')
    assert not regex.match('efg')

    # idempotency
    loader.clean_callable(func, tmpconfig)
    assert len(func.rule) == 1
    assert regex in func.rule


def test_clean_callable_rule_nick(tmpconfig, func):
    """Assert ``$nick`` in a rule will match ``TestBot: `` or ``TestBot, ``."""
    setattr(func, 'rule', [r'$nickhello'])
    loader.clean_callable(func, tmpconfig)

    assert hasattr(func, 'rule')
    assert len(func.rule) == 1

    # Test the regex is compiled properly
    regex = func.rule[0]
    assert regex.match('TestBot: hello')
    assert regex.match('TestBot, hello')
    assert not regex.match('TestBot not hello')

    # idempotency
    loader.clean_callable(func, tmpconfig)
    assert len(func.rule) == 1
    assert regex in func.rule


def test_clean_callable_rule_nickname(tmpconfig, func):
    """Assert ``$nick`` in a rule will match ``TestBot``."""
    setattr(func, 'rule', [r'$nickname\s+hello'])
    loader.clean_callable(func, tmpconfig)

    assert hasattr(func, 'rule')
    assert len(func.rule) == 1

    # Test the regex is compiled properly
    regex = func.rule[0]
    assert regex.match('TestBot hello')
    assert not regex.match('TestBot not hello')

    # idempotency
    loader.clean_callable(func, tmpconfig)
    assert len(func.rule) == 1
    assert regex in func.rule


def test_clean_callable_nickname_command(tmpconfig, func):
    setattr(func, 'nickname_commands', ['hello!'])
    loader.clean_callable(func, tmpconfig)

    assert hasattr(func, 'nickname_commands')
    assert len(func.nickname_commands) == 1
    assert func.nickname_commands == ['hello!']
    assert hasattr(func, 'rule')
    assert len(func.rule) == 1

    regex = func.rule[0]
    assert regex.match('TestBot hello!')
    assert regex.match('TestBot, hello!')
    assert regex.match('TestBot: hello!')
    assert not regex.match('TestBot not hello')

    # Default values
    assert hasattr(func, 'unblockable')
    assert func.unblockable is False
    assert hasattr(func, 'priority')
    assert func.priority == 'medium'
    assert hasattr(func, 'thread')
    assert func.thread is True
    assert hasattr(func, 'rate')
    assert func.rate == 0
    assert hasattr(func, 'channel_rate')
    assert func.channel_rate == 0
    assert hasattr(func, 'global_rate')
    assert func.global_rate == 0

    # idempotency
    loader.clean_callable(func, tmpconfig)
    assert len(func.rule) == 1
    assert regex in func.rule

    assert func.unblockable is False
    assert func.priority == 'medium'
    assert func.thread is True
    assert func.rate == 0
    assert func.channel_rate == 0
    assert func.global_rate == 0


def test_clean_callable_action_command(tmpconfig, func):
    setattr(func, 'action_commands', ['bots'])
    loader.clean_callable(func, tmpconfig)

    assert hasattr(func, 'action_commands')
    assert len(func.action_commands) == 1
    assert func.action_commands == ['bots']
    assert hasattr(func, 'rule')
    assert len(func.rule) == 1

    regex = func.rule[0]
    assert regex.match('bots bottingly')
    assert not regex.match('spams spammingly')

    # idempotency
    loader.clean_callable(func, tmpconfig)
    assert len(func.rule) == 1
    assert regex in func.rule


def test_clean_callable_events(tmpconfig, func):
    setattr(func, 'event', ['TOPIC'])
    loader.clean_callable(func, tmpconfig)

    assert hasattr(func, 'event')
    assert func.event == ['TOPIC']

    setattr(func, 'event', ['TOPIC', 'JOIN'])
    loader.clean_callable(func, tmpconfig)

    assert hasattr(func, 'event')
    assert func.event == ['TOPIC', 'JOIN']

    setattr(func, 'event', ['TOPIC', 'join', 'Nick'])
    loader.clean_callable(func, tmpconfig)

    assert hasattr(func, 'event')
    assert func.event == ['TOPIC', 'JOIN', 'NICK']


def test_clean_callable_events_basestring(tmpconfig, func):
    setattr(func, 'event', 'topic')
    loader.clean_callable(func, tmpconfig)

    assert hasattr(func, 'event')
    assert func.event == ['TOPIC']

    setattr(func, 'event', 'JOIN')
    loader.clean_callable(func, tmpconfig)

    assert hasattr(func, 'event')
    assert func.event == ['JOIN']


def test_clean_callable_example(tmpconfig, func):
    module.commands('test')(func)
    module.example('.test hello')(func)

    loader.clean_callable(func, tmpconfig)

    assert hasattr(func, '_docs')
    assert len(func._docs) == 1
    assert 'test' in func._docs

    docs = func._docs['test']
    assert len(docs) == 2
    assert docs[0] == inspect.cleandoc(func.__doc__).splitlines()
    assert docs[1] == ['.test hello']


def test_clean_callable_example_not_set(tmpconfig, func):
    module.commands('test')(func)

    loader.clean_callable(func, tmpconfig)

    assert hasattr(func, '_docs')
    assert len(func._docs) == 1
    assert 'test' in func._docs

    docs = func._docs['test']
    assert len(docs) == 2
    assert docs[0] == inspect.cleandoc(func.__doc__).splitlines()
    assert docs[1] == []


def test_clean_callable_example_multi_commands(tmpconfig, func):
    module.commands('test')(func)
    module.commands('unit')(func)
    module.example('.test hello')(func)

    loader.clean_callable(func, tmpconfig)

    assert hasattr(func, '_docs')
    assert len(func._docs) == 2
    assert 'test' in func._docs
    assert 'unit' in func._docs

    test_docs = func._docs['test']
    unit_docs = func._docs['unit']
    assert len(test_docs) == 2
    assert test_docs == unit_docs

    assert test_docs[0] == inspect.cleandoc(func.__doc__).splitlines()
    assert test_docs[1] == ['.test hello']


def test_clean_callable_example_first_only(tmpconfig, func):
    module.commands('test')(func)
    module.example('.test hello')(func)
    module.example('.test bonjour')(func)

    loader.clean_callable(func, tmpconfig)

    assert len(func._docs) == 1
    assert 'test' in func._docs

    docs = func._docs['test']
    assert len(docs) == 2
    assert docs[0] == inspect.cleandoc(func.__doc__).splitlines()
    assert docs[1] == ['.test hello']


def test_clean_callable_example_first_only_multi_commands(tmpconfig, func):
    module.commands('test')(func)
    module.commands('unit')(func)
    module.example('.test hello')(func)
    module.example('.test bonjour')(func)

    loader.clean_callable(func, tmpconfig)

    assert hasattr(func, '_docs')
    assert len(func._docs) == 2
    assert 'test' in func._docs
    assert 'unit' in func._docs

    test_docs = func._docs['test']
    unit_docs = func._docs['unit']
    assert len(test_docs) == 2
    assert test_docs == unit_docs

    assert test_docs[0] == inspect.cleandoc(func.__doc__).splitlines()
    assert test_docs[1] == ['.test hello']


def test_clean_callable_example_user_help(tmpconfig, func):
    module.commands('test')(func)
    module.example('.test hello', user_help=True)(func)

    loader.clean_callable(func, tmpconfig)

    assert len(func._docs) == 1
    assert 'test' in func._docs

    docs = func._docs['test']
    assert len(docs) == 2
    assert docs[0] == inspect.cleandoc(func.__doc__).splitlines()
    assert docs[1] == ['.test hello']


def test_clean_callable_example_user_help_multi(tmpconfig, func):
    module.commands('test')(func)
    module.example('.test hello', user_help=True)(func)
    module.example('.test bonjour', user_help=True)(func)

    loader.clean_callable(func, tmpconfig)

    assert len(func._docs) == 1
    assert 'test' in func._docs

    docs = func._docs['test']
    assert len(docs) == 2
    assert docs[0] == inspect.cleandoc(func.__doc__).splitlines()
    assert docs[1] == ['.test hello', '.test bonjour']


def test_clean_callable_example_user_help_mixed(tmpconfig, func):
    module.commands('test')(func)
    module.example('.test hello')(func)
    module.example('.test bonjour', user_help=True)(func)

    loader.clean_callable(func, tmpconfig)

    assert len(func._docs) == 1
    assert 'test' in func._docs

    docs = func._docs['test']
    assert len(docs) == 2
    assert docs[0] == inspect.cleandoc(func.__doc__).splitlines()
    assert docs[1] == ['.test bonjour']


def test_clean_callable_example_default_prefix(tmpconfig, func):
    module.commands('test')(func)
    module.example('.test hello')(func)

    tmpconfig.core.help_prefix = '!'
    loader.clean_callable(func, tmpconfig)

    assert len(func._docs) == 1
    assert 'test' in func._docs

    docs = func._docs['test']
    assert len(docs) == 2
    assert docs[0] == inspect.cleandoc(func.__doc__).splitlines()
    assert docs[1] == ['!test hello']


def test_clean_callable_example_nickname(tmpconfig, func):
    module.commands('test')(func)
    module.example('$nickname: hello')(func)

    loader.clean_callable(func, tmpconfig)

    assert len(func._docs) == 1
    assert 'test' in func._docs

    docs = func._docs['test']
    assert len(docs) == 2
    assert docs[0] == inspect.cleandoc(func.__doc__).splitlines()
    assert docs[1] == ['TestBot: hello']


def test_clean_callable_example_nickname_custom_prefix(tmpconfig, func):
    module.commands('test')(func)
    module.example('$nickname: hello')(func)

    tmpconfig.core.help_prefix = '!'
    loader.clean_callable(func, tmpconfig)

    assert len(func._docs) == 1
    assert 'test' in func._docs

    docs = func._docs['test']
    assert len(docs) == 2
    assert docs[0] == inspect.cleandoc(func.__doc__).splitlines()
    assert docs[1] == ['TestBot: hello']


def test_clean_callable_intents(tmpconfig, func):
    setattr(func, 'intents', [r'abc'])
    loader.clean_callable(func, tmpconfig)

    assert hasattr(func, 'intents')
    assert len(func.intents) == 1

    # Test the regex is compiled properly
    regex = func.intents[0]
    assert regex.match('abc')
    assert regex.match('abcd')
    assert regex.match('ABC')
    assert regex.match('AbCdE')
    assert not regex.match('efg')

    # Default values
    assert hasattr(func, 'unblockable')
    assert func.unblockable is False
    assert hasattr(func, 'priority')
    assert func.priority == 'medium'
    assert hasattr(func, 'thread')
    assert func.thread is True
    assert hasattr(func, 'rate')
    assert func.rate == 0
    assert hasattr(func, 'channel_rate')
    assert func.channel_rate == 0
    assert hasattr(func, 'global_rate')
    assert func.global_rate == 0

    # idempotency
    loader.clean_callable(func, tmpconfig)
    assert len(func.intents) == 1
    assert regex in func.intents

    assert func.unblockable is False
    assert func.priority == 'medium'
    assert func.thread is True
    assert func.rate == 0
    assert func.channel_rate == 0
    assert func.global_rate == 0


def test_clean_callable_url(tmpconfig, func):
    setattr(func, 'url_regex', [re.compile('.*')])
    loader.clean_callable(func, tmpconfig)

    assert hasattr(func, 'url_regex')
    assert len(func.url_regex) == 1

    # Don't test the regex; that's handled in a different module
    # Default values
    assert hasattr(func, 'unblockable')
    assert func.unblockable is False
    assert hasattr(func, 'thread')
    assert func.thread is True
    assert hasattr(func, 'rate')
    assert func.rate == 0
    assert hasattr(func, 'channel_rate')
    assert func.channel_rate == 0
    assert hasattr(func, 'global_rate')
    assert func.global_rate == 0

    # idempotency
    loader.clean_callable(func, tmpconfig)
    assert len(func.url_regex) == 1
    assert func.unblockable is False
    assert func.thread is True
    assert func.rate == 0
    assert func.channel_rate == 0
    assert func.global_rate == 0
