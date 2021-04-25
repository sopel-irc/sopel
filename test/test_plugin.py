# coding=utf-8
"""Tests for sopel.plugin decorators"""
from __future__ import absolute_import, division, print_function, unicode_literals

from sopel import plugin
from sopel.tests import rawlist


TMP_CONFIG = """
[core]
owner = Bar
nick = Sopel
enable = coretasks
"""


def test_find():
    @plugin.find('.*')
    def mock(bot, trigger, match):
        return True
    assert mock.find_rules == ['.*']


def test_find_args():
    @plugin.find('.*', r'\d+')
    def mock(bot, trigger, match):
        return True
    assert mock.find_rules == ['.*', r'\d+']


def test_find_multiple():
    @plugin.find('.*', r'\d+')
    @plugin.find('.*')
    @plugin.find(r'\w+')
    def mock(bot, trigger, match):
        return True
    assert mock.find_rules == [r'\w+', '.*', r'\d+']


def test_label():
    @plugin.label('hello')
    def mock(bot, trigger):
        return True
    assert mock.rule_label == 'hello'


def test_search():
    @plugin.search('.*')
    def mock(bot, trigger, match):
        return True
    assert mock.search_rules == ['.*']


def test_search_args():
    @plugin.search('.*', r'\d+')
    def mock(bot, trigger, match):
        return True
    assert mock.search_rules == ['.*', r'\d+']


def test_search_multiple():
    @plugin.search('.*', r'\d+')
    @plugin.search('.*')
    @plugin.search(r'\w+')
    def mock(bot, trigger, match):
        return True
    assert mock.search_rules == [r'\w+', '.*', r'\d+']


def test_url_lazy():
    def loader(settings):
        return [r'\w+', '.*', r'\d+']

    @plugin.url_lazy(loader)
    def mock(bot, trigger, match):
        return True

    assert mock.url_lazy_loaders == [loader]
    assert not hasattr(mock, 'url_regex')


def test_url_lazy_args():
    def loader_1(settings):
        return [r'\w+', '.*', r'\d+']

    def loader_2(settings):
        return [r'[a-z]+']

    @plugin.url_lazy(loader_1, loader_2)
    def mock(bot, trigger, match):
        return True

    assert mock.url_lazy_loaders == [loader_1, loader_2]
    assert not hasattr(mock, 'url_regex')


def test_url_lazy_multiple():
    def loader_1(settings):
        return [r'\w+', '.*', r'\d+']

    def loader_2(settings):
        return [r'[a-z]+']

    @plugin.url_lazy(loader_2)
    @plugin.url_lazy(loader_1)
    def mock(bot, trigger, match):
        return True

    assert mock.url_lazy_loaders == [loader_1, loader_2]
    assert not hasattr(mock, 'url_regex')


def test_rule_lazy():
    def loader(settings):
        return [r'\w+', '.*', r'\d+']

    @plugin.rule_lazy(loader)
    def mock(bot, trigger):
        return True

    assert mock.rule_lazy_loaders == [loader]
    assert not hasattr(mock, 'rule')


def test_rule_lazy_args():
    def loader_1(settings):
        return [r'\w+', '.*', r'\d+']

    def loader_2(settings):
        return [r'[a-z]+']

    @plugin.rule_lazy(loader_1, loader_2)
    def mock(bot, trigger):
        return True

    assert mock.rule_lazy_loaders == [loader_1, loader_2]
    assert not hasattr(mock, 'rule')


def test_rule_lazy_multiple():
    def loader_1(settings):
        return [r'\w+', '.*', r'\d+']

    def loader_2(settings):
        return [r'[a-z]+']

    @plugin.rule_lazy(loader_2)
    @plugin.rule_lazy(loader_1)
    def mock(bot, trigger):
        return True

    assert mock.rule_lazy_loaders == [loader_1, loader_2]
    assert not hasattr(mock, 'rule')


def test_find_lazy():
    def loader(settings):
        return [r'\w+', '.*', r'\d+']

    @plugin.find_lazy(loader)
    def mock(bot, trigger):
        return True

    assert mock.find_rules_lazy_loaders == [loader]
    assert not hasattr(mock, 'rule')
    assert not hasattr(mock, 'find_rules')


def test_find_lazy_args():
    def loader_1(settings):
        return [r'\w+', '.*', r'\d+']

    def loader_2(settings):
        return [r'[a-z]+']

    @plugin.find_lazy(loader_1, loader_2)
    def mock(bot, trigger):
        return True

    assert mock.find_rules_lazy_loaders == [loader_1, loader_2]
    assert not hasattr(mock, 'rule')
    assert not hasattr(mock, 'find_rules')


def test_find_lazy_multiple():
    def loader_1(settings):
        return [r'\w+', '.*', r'\d+']

    def loader_2(settings):
        return [r'[a-z]+']

    @plugin.find_lazy(loader_2)
    @plugin.find_lazy(loader_1)
    def mock(bot, trigger):
        return True

    assert mock.find_rules_lazy_loaders == [loader_1, loader_2]
    assert not hasattr(mock, 'rule')
    assert not hasattr(mock, 'find_rules')


def test_search_lazy():
    def loader(settings):
        return [r'\w+', '.*', r'\d+']

    @plugin.search_lazy(loader)
    def mock(bot, trigger):
        return True

    assert mock.search_rules_lazy_loaders == [loader]
    assert not hasattr(mock, 'rule')
    assert not hasattr(mock, 'search_rules')


def test_search_lazy_args():
    def loader_1(settings):
        return [r'\w+', '.*', r'\d+']

    def loader_2(settings):
        return [r'[a-z]+']

    @plugin.search_lazy(loader_1, loader_2)
    def mock(bot, trigger):
        return True

    assert mock.search_rules_lazy_loaders == [loader_1, loader_2]
    assert not hasattr(mock, 'rule')
    assert not hasattr(mock, 'search_rules')


def test_search_lazy_multiple():
    def loader_1(settings):
        return [r'\w+', '.*', r'\d+']

    def loader_2(settings):
        return [r'[a-z]+']

    @plugin.search_lazy(loader_2)
    @plugin.search_lazy(loader_1)
    def mock(bot, trigger):
        return True

    assert mock.search_rules_lazy_loaders == [loader_1, loader_2]
    assert not hasattr(mock, 'rule')
    assert not hasattr(mock, 'search_rules')


def test_ctcp():
    @plugin.ctcp('ACTION')
    def mock(bot, trigger, match):
        return True
    assert mock.intents == ['ACTION']


def test_ctcp_empty():
    @plugin.ctcp()
    def mock(bot, trigger, match):
        return True
    assert mock.intents == ['ACTION']


def test_ctcp_direct():
    @plugin.ctcp
    def mock(bot, trigger, match):
        return True
    assert mock.intents == ['ACTION']


BAN_MESSAGE = ':Foo!foo@example.com PRIVMSG #chan :.ban ExiClone'
BAN_PRIVATE_MESSAGE = ':Foo!foo@example.com PRIVMSG Sopel :.ban #chan ExiClone'


def test_require_bot_privilege(configfactory,
                               botfactory,
                               triggerfactory,
                               ircfactory):
    settings = configfactory('default.cfg', TMP_CONFIG)
    mockbot = botfactory.preloaded(settings)
    mockserver = ircfactory(mockbot)

    bot = triggerfactory.wrapper(mockbot, BAN_MESSAGE)
    mockserver.channel_joined('#chan')
    mockserver.join('Foo', '#chan')
    mockserver.mode_set('#chan', '+vo', ['Foo', bot.nick])

    @plugin.command('ban')
    @plugin.require_bot_privilege(plugin.VOICE)
    def mock(bot, trigger):
        return True

    assert mock(bot, bot._trigger) is True, (
        'Bot must meet the requirement when having a higher privilege level.')

    @plugin.command('ban')
    @plugin.require_bot_privilege(plugin.OP)
    def mock(bot, trigger):
        return True

    assert mock(bot, bot._trigger) is True

    @plugin.command('ban')
    @plugin.require_bot_privilege(plugin.OWNER)
    def mock(bot, trigger):
        return True

    assert mock(bot, bot._trigger) is not True
    assert not bot.backend.message_sent

    @plugin.command('ban')
    @plugin.require_bot_privilege(plugin.OWNER, message='Nope')
    def mock(bot, trigger):
        return True

    assert mock(bot, bot._trigger) is not True
    assert bot.backend.message_sent == rawlist('PRIVMSG #chan :Nope')

    @plugin.command('ban')
    @plugin.require_bot_privilege(plugin.OWNER, message='Nope', reply=True)
    def mock(bot, trigger):
        return True

    assert mock(bot, bot._trigger) is not True
    assert bot.backend.message_sent[1:] == rawlist('PRIVMSG #chan :Foo: Nope')


def test_require_bot_privilege_private_message(configfactory,
                                               botfactory,
                                               triggerfactory,
                                               ircfactory):
    settings = configfactory('default.cfg', TMP_CONFIG)
    mockbot = botfactory.preloaded(settings)
    mockserver = ircfactory(mockbot)

    bot = triggerfactory.wrapper(mockbot, BAN_PRIVATE_MESSAGE)
    mockserver.channel_joined('#chan')
    mockserver.join('Foo', '#chan')
    mockserver.mode_set('#chan', '+vo', ['Foo', bot.nick])

    @plugin.command('ban')
    @plugin.require_bot_privilege(plugin.VOICE)
    def mock(bot, trigger):
        return True

    assert mock(bot, bot._trigger) is True

    @plugin.command('ban')
    @plugin.require_bot_privilege(plugin.OP)
    def mock(bot, trigger):
        return True

    assert mock(bot, bot._trigger) is True

    @plugin.command('ban')
    @plugin.require_bot_privilege(plugin.OWNER)
    def mock(bot, trigger):
        return True

    assert mock(bot, bot._trigger) is True, (
        'There must not be privilege check for a private message.')
