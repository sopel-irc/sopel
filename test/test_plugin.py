"""Tests for sopel.plugin decorators"""
from __future__ import annotations

import pytest

from sopel import plugin
from sopel.tests import rawlist


TMP_CONFIG = """
[core]
owner = Bar
nick = Sopel
enable = coretasks
"""


CAP_ACK_MESSAGE = 'CAP * ACK :away-notify'


@pytest.fixture
def cap_ack_wrapped(configfactory, botfactory, triggerfactory):
    settings = configfactory('default.cfg', TMP_CONFIG)
    return triggerfactory.wrapper(botfactory(settings), CAP_ACK_MESSAGE)


def test_capability(cap_ack_wrapped):
    handler = plugin.capability('away-notify')
    assert isinstance(handler, plugin.Capability)
    assert handler.cap_req == ('away-notify',)

    result = handler.callback(cap_ack_wrapped, True)
    assert result == (True, None)


def test_capability_as_string():
    handler = plugin.capability('batch')
    assert str(handler).startswith('<capability')
    assert str(handler).endswith("'batch'>")

    def _batch_callback(cap_req, bot, acknowledged):
        ...

    handler = plugin.capability('batch', handler=_batch_callback)

    assert '(_batch_callback())' in str(handler)


def test_capability_handler_define_once():
    @plugin.capability('away-notify')
    def handler(name, bot, acknowledged):
        ...

    assert isinstance(handler, plugin.Capability)

    # cannot redefine a handler
    with pytest.raises(RuntimeError):
        handler(lambda x, y, z: None)


def test_capability_handler_continue(cap_ack_wrapped):
    @plugin.capability('away-notify')
    def handler(name, bot, acknowledged):
        return plugin.CapabilityNegotiation.CONTINUE

    assert isinstance(handler, plugin.Capability)
    assert handler.cap_req == ('away-notify',)
    result = handler.callback(cap_ack_wrapped, True)
    assert result == (False, plugin.CapabilityNegotiation.CONTINUE)


def test_capability_handler_done(cap_ack_wrapped):
    @plugin.capability('away-notify')
    def handler(name, bot, acknowledged):
        return plugin.CapabilityNegotiation.DONE

    result = handler.callback(cap_ack_wrapped, True)
    assert result == (True, plugin.CapabilityNegotiation.DONE)


def test_capability_handler_raises(cap_ack_wrapped):
    @plugin.capability('away-notify')
    def handler(name, bot, acknowledged):
        raise RuntimeError('Cap Error')

    with pytest.raises(RuntimeError):
        handler.callback(cap_ack_wrapped, True)


def test_capability_too_long():
    cap_reqs = ('example/cap',) * 41
    assert len(' '.join(cap_reqs).encode('utf-8')) <= 500, 'Example too long'
    plugin.capability(*cap_reqs)  # nothing happens

    cap_reqs = ('example/cap',) * 42
    assert len(' '.join(cap_reqs).encode('utf-8')) > 500, 'Example too short'

    with pytest.raises(ValueError):
        plugin.capability(*cap_reqs)


def test_allow_bots():
    # test decorator with parentheses
    @plugin.allow_bots()
    def mock(bot, trigger, match):
        return True
    assert mock.allow_bots is True

    # test decorator without parentheses
    @plugin.allow_bots
    def mock(bot, trigger, match):
        return True
    assert mock.allow_bots is True

    # test without decorator
    def mock(bot, trigger, match):
        return True
    # on undecorated callables, the attr only exists after the loader loads them
    # so this cannot `assert mock.allow_bots is False` here
    assert not hasattr(mock, 'allow_bots')


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
    assert mock.url_regex == []


def test_url_lazy_args():
    def loader_1(settings):
        return [r'\w+', '.*', r'\d+']

    def loader_2(settings):
        return [r'[a-z]+']

    @plugin.url_lazy(loader_1, loader_2)
    def mock(bot, trigger, match):
        return True

    assert mock.url_lazy_loaders == [loader_1, loader_2]
    assert mock.url_regex == []


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
    assert mock.url_regex == []


def test_rule_lazy():
    def loader(settings):
        return [r'\w+', '.*', r'\d+']

    @plugin.rule_lazy(loader)
    def mock(bot, trigger):
        return True

    assert mock.rule_lazy_loaders == [loader]
    assert mock.rules == []


def test_rule_lazy_args():
    def loader_1(settings):
        return [r'\w+', '.*', r'\d+']

    def loader_2(settings):
        return [r'[a-z]+']

    @plugin.rule_lazy(loader_1, loader_2)
    def mock(bot, trigger):
        return True

    assert mock.rule_lazy_loaders == [loader_1, loader_2]
    assert mock.rules == []


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
    assert mock.rules == []


def test_find_lazy():
    def loader(settings):
        return [r'\w+', '.*', r'\d+']

    @plugin.find_lazy(loader)
    def mock(bot, trigger):
        return True

    assert mock.find_rules_lazy_loaders == [loader]
    assert mock.rules == []
    assert mock.find_rules == []


def test_find_lazy_args():
    def loader_1(settings):
        return [r'\w+', '.*', r'\d+']

    def loader_2(settings):
        return [r'[a-z]+']

    @plugin.find_lazy(loader_1, loader_2)
    def mock(bot, trigger):
        return True

    assert mock.find_rules_lazy_loaders == [loader_1, loader_2]
    assert mock.rules == []
    assert mock.find_rules == []


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
    assert mock.rules == []
    assert mock.find_rules == []


def test_search_lazy():
    def loader(settings):
        return [r'\w+', '.*', r'\d+']

    @plugin.search_lazy(loader)
    def mock(bot, trigger):
        return True

    assert mock.search_rules_lazy_loaders == [loader]
    assert mock.rules == []
    assert mock.search_rules == []


def test_search_lazy_args():
    def loader_1(settings):
        return [r'\w+', '.*', r'\d+']

    def loader_2(settings):
        return [r'[a-z]+']

    @plugin.search_lazy(loader_1, loader_2)
    def mock(bot, trigger):
        return True

    assert mock.search_rules_lazy_loaders == [loader_1, loader_2]
    assert mock.rules == []
    assert mock.search_rules == []


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
    assert mock.rules == []
    assert mock.search_rules == []


def test_ctcp():
    @plugin.ctcp('ACTION')
    def mock(bot, trigger, match):
        return True
    assert mock.ctcp == ['ACTION']


def test_ctcp_empty():
    @plugin.ctcp()
    def mock(bot, trigger, match):
        return True
    assert mock.ctcp == ['ACTION']


def test_ctcp_direct():
    @plugin.ctcp
    def mock(bot, trigger, match):
        return True
    assert mock.ctcp == ['ACTION']


def test_rate_user():
    @plugin.rate_user(10)
    def mock(bot, trigger):
        return True
    assert mock.user_rate == 10
    assert mock.user_rate_message is None
    assert mock.channel_rate is None
    assert mock.global_rate is None
    assert mock.default_rate_message is None

    @plugin.rate_user(20, 'User rate message.')
    def mock(bot, trigger):
        return True
    assert mock.user_rate == 20
    assert mock.user_rate_message == 'User rate message.'
    assert mock.channel_rate is None
    assert mock.global_rate is None
    assert mock.default_rate_message is None


def test_rate_channel():
    @plugin.rate_channel(10)
    def mock(bot, trigger):
        return True
    assert mock.user_rate is None
    assert mock.user_rate_message is None
    assert mock.channel_rate == 10
    assert mock.channel_rate_message is None
    assert mock.default_rate_message is None

    @plugin.rate_channel(20, 'Channel rate message.')
    def mock(bot, trigger):
        return True
    assert mock.user_rate is None
    assert mock.user_rate_message is None
    assert mock.channel_rate == 20
    assert mock.channel_rate_message == 'Channel rate message.'
    assert mock.default_rate_message is None


def test_rate_global():
    @plugin.rate_global(10)
    def mock(bot, trigger):
        return True

    assert mock.user_rate is None
    assert mock.user_rate_message is None
    assert mock.channel_rate is None
    assert mock.channel_rate_message is None
    assert mock.global_rate == 10
    assert mock.global_rate_message is None

    @plugin.rate_global(20, 'Server rate message.')
    def mock(bot, trigger):
        return True

    assert mock.user_rate is None
    assert mock.user_rate_message is None
    assert mock.channel_rate is None
    assert mock.channel_rate_message is None
    assert mock.global_rate == 20
    assert mock.global_rate_message == 'Server rate message.'


def test_rate_combine_rate_decorators():
    @plugin.rate(400, 500, 600, message='Last default rate message')
    @plugin.rate_global(2, 'Server rate message')
    @plugin.rate_channel(5, 'Channel rate message')
    @plugin.rate_user(10, 'User rate message')
    @plugin.rate(40, 50, 60, message='Initial default rate message')
    def mock(bot, trigger):
        return True
    assert mock.user_rate == 10
    assert mock.user_rate_message == 'User rate message'
    assert mock.channel_rate == 5
    assert mock.channel_rate_message == 'Channel rate message'
    assert mock.global_rate == 2
    assert mock.global_rate_message == 'Server rate message'
    assert mock.default_rate_message == 'Last default rate message'


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

    assert mock(bot, bot._trigger) is not True, (
        'Callable requiring bot channel privilege must be ignored in private.')

    @plugin.command('ban')
    @plugin.require_bot_privilege(plugin.OP)
    def mock(bot, trigger):
        return True

    assert mock(bot, bot._trigger) is not True, (
        'Callable requiring bot channel privilege must be ignored in private.')

    @plugin.command('ban')
    @plugin.require_bot_privilege(plugin.OWNER)
    def mock(bot, trigger):
        return True

    assert mock(bot, bot._trigger) is not True, (
        'Callable requiring bot channel privilege must be ignored in private.')
