"""Tests for the ``sopel.plugins.callables`` module."""
from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from sopel.plugins.callables import PluginCallable, PluginGeneric, PluginJob
from sopel.tests import rawlist


if TYPE_CHECKING:
    from sopel.bot import Sopel, SopelWrapper
    from sopel.config import Config
    from sopel.tests.factories import BotFactory, ConfigFactory, TriggerFactory
    from sopel.trigger import Trigger


TMP_CONFIG = """
[core]
owner = testnick
nick = TestBot
alias_nicks =
    AliasBot
    SupBot
enable = coretasks
"""


@pytest.fixture
def tmpconfig(configfactory: ConfigFactory) -> Config:
    return configfactory('test.cfg', TMP_CONFIG)


@pytest.fixture
def mockbot(tmpconfig: Config, botfactory: BotFactory) -> Sopel:
    return botfactory(tmpconfig)


# Test plugin generic

def test_generic_ensure_callable_function():
    def handler(bot: SopelWrapper, trigger: Trigger) -> str:
        return 'test value: %s' % str(trigger)

    plugin_generic = PluginGeneric.ensure_callable(handler)
    assert isinstance(plugin_generic, PluginGeneric)

    # shared meta data
    assert plugin_generic.plugin_name is None
    assert plugin_generic.label == handler.__name__
    assert plugin_generic.threaded is True
    assert plugin_generic.doc is None
    assert plugin_generic.get_handler() is handler


def test_generic_ensure_callable_generic():
    def handler(bot: SopelWrapper, trigger: Trigger) -> str:
        return 'test value: %s' % str(trigger)

    plugin_generic = PluginGeneric(handler)

    new_generic = PluginGeneric.ensure_callable(plugin_generic)
    assert new_generic is plugin_generic


def test_generic_ensure_callable_callable():
    def handler(bot: SopelWrapper, trigger: Trigger) -> str:
        return 'test value: %s' % str(trigger)

    plugin_callable = PluginCallable(handler)

    new_generic = PluginGeneric.ensure_callable(plugin_callable)
    assert new_generic is plugin_callable


def test_generic_ensure_callable_job():
    def handler(bot: Sopel) -> str:
        return 'test value'

    plugin_job = PluginJob(handler)

    new_generic = PluginGeneric.ensure_callable(plugin_job)
    assert new_generic is plugin_job


# Test plugin callable

def test_callable_call(
    mockbot: Sopel,
    triggerfactory: TriggerFactory,
):
    wrapped = triggerfactory.wrapper(
        mockbot, ':Foo!foo@example.com PRIVMSG #channel :test message')
    expected = 'test value: test message'

    def handler(bot: SopelWrapper, trigger: Trigger):
        return 'test value: %s' % str(trigger)

    plugin_callable = PluginCallable(handler)
    assert plugin_callable(wrapped, wrapped._trigger) == expected


def test_callable_from_plugin_object_generic(
    mockbot: Sopel,
    triggerfactory: TriggerFactory,
):
    # create a plugin generic
    def handler(bot: SopelWrapper, trigger: Trigger) -> str:
        return 'test value: %s' % str(trigger)

    plugin_generic = PluginGeneric(handler)

    # convert to a plugin callable
    wrapped = triggerfactory.wrapper(
        mockbot, ':Foo!foo@example.com PRIVMSG #channel :test message')
    expected = 'test value: test message'

    plugin_callable = PluginCallable.from_plugin_object(plugin_generic)
    assert plugin_callable(wrapped, wrapped._trigger) == expected


def test_callable_call_guarded(
    mockbot: Sopel,
    triggerfactory: TriggerFactory,
):
    wrapped = triggerfactory.wrapper(
        mockbot, ':Foo!foo@example.com PRIVMSG #channel :test message')
    expected = 'test value: test message'

    def handler(bot: SopelWrapper, trigger: Trigger):
        return 'test value: %s' % str(trigger)

    def predicate(bot: SopelWrapper, trigger: Trigger):
        bot.say('guarded')
        return False

    def free(bot: SopelWrapper, trigger: Trigger):
        bot.say('free')
        return True

    n = len(mockbot.backend.message_sent)

    plugin_callable = PluginCallable(handler)
    plugin_callable.predicates.append(free)
    assert plugin_callable(wrapped, wrapped._trigger) == expected, (
        'All predicates return true, the handler should execute.'
    )
    assert mockbot.backend.message_sent[n:] == rawlist(
        'PRIVMSG #channel :free'
    ), 'Predicates can send messages.'

    n = len(mockbot.backend.message_sent)

    plugin_callable.predicates.append(predicate)
    assert plugin_callable(wrapped, wrapped._trigger) is None, (
        'One predicate returns false, the handler must not execute.'
    )
    assert mockbot.backend.message_sent[n:] == rawlist(
        'PRIVMSG #channel :free',
        'PRIVMSG #channel :guarded',
    ), 'Both predicates can send messages.'

    n = len(mockbot.backend.message_sent)

    plugin_callable.predicates.append(free)
    assert plugin_callable(wrapped, wrapped._trigger) is None, (
        'One predicate returns false, the handler must not execute.'
    )
    assert mockbot.backend.message_sent[n:] == rawlist(
        'PRIVMSG #channel :free',
        'PRIVMSG #channel :guarded',
    ), 'Predicates after the first to return false are never called.'


def test_callable_ensure_callable_function():
    def handler(bot: SopelWrapper, trigger: Trigger) -> str:
        return 'test value: %s' % str(trigger)

    plugin_callable = PluginCallable.ensure_callable(handler)
    assert isinstance(plugin_callable, PluginCallable)

    # shared meta data
    assert plugin_callable.plugin_name is None
    assert plugin_callable.label == handler.__name__
    assert plugin_callable.threaded is True
    assert plugin_callable.doc is None
    assert plugin_callable.get_handler() is handler

    # documentation
    assert plugin_callable.examples == []

    # rules
    assert plugin_callable.events == []
    assert plugin_callable.ctcp == []
    assert plugin_callable.commands == []
    assert plugin_callable.nickname_commands == []
    assert plugin_callable.action_commands == []
    assert plugin_callable.rules == []
    assert plugin_callable.rule_lazy_loaders == []
    assert plugin_callable.find_rules == []
    assert plugin_callable.find_rules_lazy_loaders == []
    assert plugin_callable.search_rules == []
    assert plugin_callable.search_rules_lazy_loaders == []
    assert plugin_callable.url_regex == []
    assert plugin_callable.url_lazy_loaders == []

    # allow special conditions
    assert plugin_callable.allow_bots is False
    assert plugin_callable.allow_echo is False

    # how to run it
    assert plugin_callable.priority == 'medium'
    assert plugin_callable.unblockable is False

    # rate limiting
    assert plugin_callable.user_rate is None
    assert plugin_callable.channel_rate is None
    assert plugin_callable.global_rate is None
    assert plugin_callable.default_rate_message is None
    assert plugin_callable.user_rate_message is None
    assert plugin_callable.channel_rate_message is None
    assert plugin_callable.global_rate_message is None

    # output management
    assert plugin_callable.output_prefix == ''


def test_callable_ensure_callable_callable():
    def handler(bot: SopelWrapper, trigger: Trigger) -> str:
        return 'test value: %s' % str(trigger)

    plugin_callable = PluginCallable(handler)

    new_callable = PluginCallable.ensure_callable(plugin_callable)
    assert new_callable is plugin_callable


def test_callable_ensure_callable_generic():
    def handler(bot: SopelWrapper, trigger: Trigger) -> str:
        return 'test value: %s' % str(trigger)

    # check old-style job definition
    setattr(handler, 'rule', ['(hello)|(hi)'])
    setattr(handler, 'thread', False)

    plugin_generic = PluginGeneric(handler)
    plugin_generic.label = 'Custom Label'

    plugin_callable = PluginCallable.ensure_callable(plugin_generic)
    assert plugin_callable is not plugin_generic
    assert isinstance(plugin_callable, PluginCallable)

    assert plugin_callable.label == 'Custom Label'
    assert plugin_callable.rules == ['(hello)|(hi)']
    assert plugin_callable.threaded is False
    assert plugin_callable.get_handler() is handler


# Test plugin job

def test_job_call(mockbot: Sopel):
    expected = 'job executed'

    def handler(bot: Sopel):
        return 'job executed'

    plugin_job = PluginJob(handler)
    assert plugin_job(mockbot) == expected


def test_job_from_plugin_object_generic(
    mockbot: Sopel,
):
    # create a plugin generic
    def handler(bot: Sopel):
        return 'job executed'

    plugin_generic = PluginGeneric(handler)

    # convert to a plugin callable
    expected = 'job executed'

    plugin_job = PluginJob.from_plugin_object(plugin_generic)
    assert plugin_job(mockbot) == expected


def test_job_ensure_callable_function():
    def handler(bot: Sopel) -> str:
        return 'test value'

    plugin_job = PluginJob.ensure_callable(handler)
    assert isinstance(plugin_job, PluginJob)

    # shared meta data
    assert plugin_job.plugin_name is None
    assert plugin_job.label == handler.__name__
    assert plugin_job.threaded is True
    assert plugin_job.doc is None
    assert plugin_job.get_handler() is handler

    # jobs
    assert plugin_job.intervals == []


def test_job_ensure_callable_job():
    def handler(bot: Sopel) -> str:
        return 'test value'

    plugin_job = PluginJob(handler)

    new_job = PluginJob.ensure_callable(plugin_job)
    assert new_job is plugin_job


def test_job_ensure_callable_generic():
    def handler(bot: Sopel) -> str:
        return 'test value'

    # check old-style job definition
    setattr(handler, 'interval', [5, 10])
    setattr(handler, 'thread', False)

    plugin_generic = PluginGeneric(handler)
    plugin_generic.label = 'Custom Label'

    plugin_job = PluginJob.ensure_callable(plugin_generic)
    assert plugin_job is not plugin_generic
    assert isinstance(plugin_job, PluginJob)

    assert plugin_job.label == 'Custom Label'
    assert plugin_job.intervals == [5, 10]
    assert plugin_job.threaded is False
    assert plugin_job.get_handler() is handler
