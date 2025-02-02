"""Tests for Sopel's ``url`` plugin"""
from __future__ import annotations

import re

import pytest

from sopel import bot, loader, plugin, plugins, trigger
from sopel.builtins import url


TMP_CONFIG = """
[core]
owner = testnick
nick = TestBot
enable = coretasks
"""


INVALID_URLS = (
    "http://.example.com/",  # empty label
    "http://example..com/",  # empty label
    "http://?",  # no host
)


@pytest.fixture
def mockbot(configfactory):
    tmpconfig = configfactory('test.cfg', TMP_CONFIG)
    url_plugin = plugins.handlers.PyModulePlugin('url', 'sopel.builtins')

    # setup the bot
    sopel = bot.Sopel(tmpconfig)
    url_plugin.load()
    url_plugin.setup(sopel)
    url_plugin.register(sopel)

    @plugin.url(re.escape('https://example.com/') + r'(.+)')
    @plugin.label('handle_urls_https')
    def url_callback_https(bot, trigger, match):
        pass

    @plugin.url(re.escape('http://example.com/') + r'(.+)')
    @plugin.label('handle_urls_http')
    def url_callback_http(bot, trigger, match):
        pass

    # prepare callables to be registered
    callables = [
        url_callback_https,
        url_callback_http,
    ]

    # clean callables and set plugin name by hand
    # since the loader and plugin handlers are excluded here
    for handler in callables:
        loader.clean_callable(handler, tmpconfig)
        handler.plugin_name = 'testplugin'

    # register callables
    sopel.register_urls(callables)

    # manually register URL Callback
    pattern = re.escape('https://help.example.com/') + r'(.+)'

    def callback(bot, trigger, match):
        pass

    sopel.register_url_callback(pattern, callback)
    return sopel


PRELOADED_CONFIG = """
[core]
owner = testnick
nick = TestBot
enable =
    coretasks
    url
"""


@pytest.fixture
def preloadedbot(configfactory, botfactory):
    tmpconfig = configfactory('preloaded.cfg', PRELOADED_CONFIG)
    return botfactory.preloaded(tmpconfig, ['url'])


@pytest.mark.parametrize("site", INVALID_URLS)
def test_find_title_invalid(site):
    # All local for invalid ones
    assert url.find_title(site) is None


def test_check_callbacks(mockbot):
    """Test that check_callbacks works with both new & legacy URL callbacks."""
    assert url.check_callbacks(mockbot, 'https://example.com/test')
    assert url.check_callbacks(mockbot, 'http://example.com/test')
    assert url.check_callbacks(mockbot, 'https://help.example.com/test')
    assert not url.check_callbacks(mockbot, 'https://not.example.com/test')


def test_url_triggers_rules_and_auto_title(mockbot):
    line = ':Foo!foo@example.com PRIVMSG #sopel :https://not.example.com/test'
    pretrigger = trigger.PreTrigger(mockbot.nick, line)
    results = mockbot.rules.get_triggered_rules(mockbot, pretrigger)

    assert len(results) == 1, 'Only one should match'
    result = results[0]
    assert isinstance(result[0], plugins.rules.Rule)
    assert result[0].get_rule_label() == 'title_auto'

    line = ':Foo!foo@example.com PRIVMSG #sopel :https://example.com/test'
    pretrigger = trigger.PreTrigger(mockbot.nick, line)
    results = mockbot.rules.get_triggered_rules(mockbot, pretrigger)

    assert len(results) == 2, (
        'Two rules should match: title_auto and handle_urls_https')
    labels = sorted(result[0].get_rule_label() for result in results)
    expected = ['handle_urls_https', 'title_auto']
    assert labels == expected


@pytest.mark.parametrize('level, result', (
    ('NOTHING', False),
    ('VOICE', False),
    ('HALFOP', False),
    ('OP', True),
    ('ADMIN', True),
    ('OWNER', True),
))
def test_url_ban_privilege(preloadedbot, ircfactory, triggerfactory, level, result):
    """Make sure the urlban command privilege check functions correctly."""
    irc = ircfactory(preloadedbot)
    irc.channel_joined('#test', [
        'Unothing', 'Uvoice', 'Uhalfop', 'Uop', 'Uadmin', 'Uowner'])
    irc.mode_set('#test', '+vhoaq', [
        'Uvoice', 'Uhalfop', 'Uop', 'Uadmin', 'Uowner'])

    nick = f'U{level.title()}'
    user = level.lower()
    line = f':{nick}!{user}@example.com PRIVMSG #test :.urlban *'
    wrapper = triggerfactory.wrapper(preloadedbot, line)
    match = triggerfactory(preloadedbot, line)

    # parameter matrix assumes the default `url.exclude_required_access` config
    # value, which was 'OP' at the time of test creation
    assert url._user_can_change_excludes(wrapper, match) == result
