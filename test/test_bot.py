# coding=utf-8
"""Tests for core ``sopel.bot`` module"""
from __future__ import unicode_literals, absolute_import, print_function, division

import re

import pytest

from sopel import bot, plugins
from sopel.tests import rawlist
from sopel.tools import SopelMemory


TMP_CONFIG = """
[core]
owner = testnick
nick = TestBot
enable = coretasks
"""


@pytest.fixture
def tmpconfig(configfactory):
    return configfactory('test.cfg', TMP_CONFIG)


@pytest.fixture
def mockbot(tmpconfig, botfactory):
    return botfactory(tmpconfig)


def test_wrapper_say(mockbot, triggerfactory):
    wrapper = triggerfactory.wrapper(
        mockbot, ':Test!test@example.com PRIVMSG #channel :test message')
    wrapper.say('Hi!')

    assert mockbot.backend.message_sent == rawlist(
        'PRIVMSG #channel :Hi!'
    )


def test_wrapper_say_override_destination(mockbot, triggerfactory):
    wrapper = triggerfactory.wrapper(
        mockbot, ':Test!test@example.com PRIVMSG #channel :test message')
    wrapper.say('Hi!', destination='#different')

    assert mockbot.backend.message_sent == rawlist(
        'PRIVMSG #different :Hi!'
    )


def test_wrapper_notice(mockbot, triggerfactory):
    wrapper = triggerfactory.wrapper(
        mockbot, ':Test!test@example.com PRIVMSG #channel :test message')
    wrapper.notice('Hi!')

    assert mockbot.backend.message_sent == rawlist(
        'NOTICE #channel :Hi!'
    )


def test_wrapper_notice_override_destination(mockbot, triggerfactory):
    wrapper = triggerfactory.wrapper(
        mockbot, ':Test!test@example.com PRIVMSG #channel :test message')
    wrapper.notice('Hi!', destination='#different')

    assert mockbot.backend.message_sent == rawlist(
        'NOTICE #different :Hi!'
    )


def test_wrapper_action(mockbot, triggerfactory):
    wrapper = triggerfactory.wrapper(
        mockbot, ':Test!test@example.com PRIVMSG #channel :test message')
    wrapper.action('Hi!')

    assert mockbot.backend.message_sent == rawlist(
        'PRIVMSG #channel :\x01ACTION Hi!\x01'
    )


def test_wrapper_action_override_destination(mockbot, triggerfactory):
    wrapper = triggerfactory.wrapper(
        mockbot, ':Test!test@example.com PRIVMSG #channel :test message')
    wrapper.action('Hi!', destination='#different')

    assert mockbot.backend.message_sent == rawlist(
        'PRIVMSG #different :\x01ACTION Hi!\x01'
    )


def test_wrapper_reply(mockbot, triggerfactory):
    wrapper = triggerfactory.wrapper(
        mockbot, ':Test!test@example.com PRIVMSG #channel :test message')
    wrapper.reply('Hi!')

    assert mockbot.backend.message_sent == rawlist(
        'PRIVMSG #channel :Test: Hi!'
    )


def test_wrapper_reply_override_destination(mockbot, triggerfactory):
    wrapper = triggerfactory.wrapper(
        mockbot, ':Test!test@example.com PRIVMSG #channel :test message')
    wrapper.reply('Hi!', destination='#another')

    assert mockbot.backend.message_sent == rawlist(
        'PRIVMSG #another :Test: Hi!'
    )


def test_wrapper_reply_override_reply_to(mockbot, triggerfactory):
    wrapper = triggerfactory.wrapper(
        mockbot, ':Test!test@example.com PRIVMSG #channel :test message')
    wrapper.reply('Hi!', reply_to='Admin')

    assert mockbot.backend.message_sent == rawlist(
        'PRIVMSG #channel :Admin: Hi!'
    )


def test_wrapper_reply_override_destination_reply_to(mockbot, triggerfactory):
    wrapper = triggerfactory.wrapper(
        mockbot, ':Test!test@example.com PRIVMSG #channel :test message')
    wrapper.reply('Hi!', destination='#another', reply_to='Admin')

    assert mockbot.backend.message_sent == rawlist(
        'PRIVMSG #another :Admin: Hi!'
    )


def test_wrapper_kick(mockbot, triggerfactory):
    wrapper = triggerfactory.wrapper(
        mockbot, ':Test!test@example.com PRIVMSG #channel :test message')
    wrapper.kick('SpamUser')

    assert mockbot.backend.message_sent == rawlist(
        'KICK #channel SpamUser'
    )


def test_wrapper_kick_message(mockbot, triggerfactory):
    wrapper = triggerfactory.wrapper(
        mockbot, ':Test!test@example.com PRIVMSG #channel :test message')
    wrapper.kick('SpamUser', message='Test reason')

    assert mockbot.backend.message_sent == rawlist(
        'KICK #channel SpamUser :Test reason'
    )


def test_wrapper_kick_error_nick(mockbot, triggerfactory):
    wrapper = triggerfactory.wrapper(
        mockbot, ':Test!test@example.com PRIVMSG #channel :test message')
    with pytest.raises(RuntimeError):
        wrapper.kick(None)

    assert mockbot.backend.message_sent == []


def test_wrapper_kick_error_channel(mockbot, triggerfactory):
    wrapper = triggerfactory.wrapper(
        mockbot, ':Test!test@example.com PRIVMSG OtherUser :test message')
    with pytest.raises(RuntimeError):
        wrapper.kick('SpamUser')

    assert mockbot.backend.message_sent == []


def test_wrapper_kick_override_destination(mockbot, triggerfactory):
    wrapper = triggerfactory.wrapper(
        mockbot, ':Test!test@example.com PRIVMSG #channel :test message')
    wrapper.kick('SpamUser', channel='#another')

    assert mockbot.backend.message_sent == rawlist(
        'KICK #another SpamUser'
    )


def test_wrapper_kick_override_destination_message(mockbot, triggerfactory):
    wrapper = triggerfactory.wrapper(
        mockbot, ':Test!test@example.com PRIVMSG #channel :test message')
    wrapper.kick('SpamUser', channel='#another', message='Test reason')

    assert mockbot.backend.message_sent == rawlist(
        'KICK #another SpamUser :Test reason'
    )


def test_register_unregister_plugin(tmpconfig):
    sopel = bot.Sopel(tmpconfig, daemon=False)

    # since `setup` hasn't been run, there is no registered plugin
    assert not sopel.has_plugin('coretasks')

    # register the plugin
    plugin = plugins.handlers.PyModulePlugin('coretasks', 'sopel')
    plugin.load()
    plugin.register(sopel)

    # and now there is!
    assert sopel.has_plugin('coretasks')

    # unregister it
    plugin.unregister(sopel)
    assert not sopel.has_plugin('coretasks')


def test_remove_plugin_unknown_plugin(tmpconfig):
    sopel = bot.Sopel(tmpconfig, daemon=False)

    plugin = plugins.handlers.PyModulePlugin('admin', 'sopel.modules')
    with pytest.raises(plugins.exceptions.PluginNotRegistered):
        sopel.remove_plugin(plugin, [], [], [], [])


def test_remove_plugin_unregistered_plugin(tmpconfig):
    sopel = bot.Sopel(tmpconfig, daemon=False)

    # register the plugin
    plugin = plugins.handlers.PyModulePlugin('coretasks', 'sopel')
    plugin.load()
    plugin.register(sopel)

    # Unregister the plugin
    plugin.unregister(sopel)

    # And now it must raise an exception
    with pytest.raises(plugins.exceptions.PluginNotRegistered):
        sopel.remove_plugin(plugin, [], [], [], [])


def test_reload_plugin_unregistered_plugin(tmpconfig):
    sopel = bot.Sopel(tmpconfig, daemon=False)

    # register the plugin
    plugin = plugins.handlers.PyModulePlugin('coretasks', 'sopel')
    plugin.load()
    plugin.register(sopel)

    # Unregister the plugin
    plugin.unregister(sopel)

    # And now it must raise an exception
    with pytest.raises(plugins.exceptions.PluginNotRegistered):
        sopel.reload_plugin(plugin.name)


def test_search_url_callbacks(tmpconfig):
    """Test search_url_callbacks for a registered URL."""
    sopel = bot.Sopel(tmpconfig, daemon=False)

    def url_handler(*args, **kwargs):
        return None

    sopel.register_url_callback(r'https://example\.com', url_handler)
    results = list(sopel.search_url_callbacks('https://example.com'))
    assert len(results) == 1, 'Expected 1 handler; found %d' % len(results)
    assert url_handler in results[0], 'Once registered, handler must be found'


def test_search_url_callbacks_pattern(tmpconfig):
    """Test search_url_callbacks for a registered regex pattern."""
    sopel = bot.Sopel(tmpconfig, daemon=False)

    def url_handler(*args, **kwargs):
        return None

    sopel.register_url_callback(r'https://(www\.)?example\.com', url_handler)
    results = list(sopel.search_url_callbacks('https://example.com'))
    assert len(results) == 1, 'Expected 1 handler; found %d' % len(results)
    assert url_handler in results[0], 'Once registered, handler must be found'

    results = list(sopel.search_url_callbacks('https://www.example.com'))
    assert len(results) == 1, 'Regex pattern must match both URLs'
    assert url_handler in results[0]


def test_search_url_callbacks_compiled_pattern(tmpconfig):
    """Test search_url_callbacks for a registered compiled regex pattern."""
    sopel = bot.Sopel(tmpconfig, daemon=False)
    url_regex = re.compile(r'https://(www\.)?example\.com')

    def url_handler(*args, **kwargs):
        return None

    sopel.register_url_callback(url_regex, url_handler)
    results = list(sopel.search_url_callbacks('https://example.com'))
    assert len(results) == 1, 'Expected 1 handler; found %d' % len(results)
    assert url_handler in results[0], 'Once registered, handler must be found'

    results = list(sopel.search_url_callbacks('https://www.example.com'))
    assert len(results) == 1, 'Regex pattern must match both URLs'
    assert url_handler in results[0]


def test_search_url_callbacks_not_found(tmpconfig):
    """Test search_url_callbacks when pattern does not match."""
    sopel = bot.Sopel(tmpconfig, daemon=False)
    results = sopel.search_url_callbacks('https://example.com')
    assert not list(results), 'No handler registered; must return an empty list'

    def url_handler(*args, **kwargs):
        return None

    sopel.register_url_callback(r'https://(www\.)?example\.com', url_handler)

    results = sopel.search_url_callbacks('https://not-example.com')
    assert not list(results), 'URL must not match any pattern'


def test_register_url_callback_multiple(tmpconfig):
    """Test register_url_callback replace URL callbacks for a pattern."""
    test_pattern = r'https://(www\.)?example\.com'

    def url_handler(*args, **kwargs):
        return None

    def url_handler_replacement(*args, **kwargs):
        return None

    sopel = bot.Sopel(tmpconfig, daemon=False)
    sopel.register_url_callback(test_pattern, url_handler)

    results = list(sopel.search_url_callbacks('https://www.example.com'))
    assert url_handler in results[0]

    sopel.register_url_callback(test_pattern, url_handler_replacement)

    results = list(sopel.search_url_callbacks('https://www.example.com'))
    assert len(results) == 1, 'There must be one and only one callback'
    assert url_handler_replacement in results[0], (
        'Handler must have been replaced')


def test_unregister_url_callback(tmpconfig):
    """Test unregister_url_callback removes URL callback for a pattern."""
    test_pattern = r'https://(www\.)?example\.com'

    def url_handler(*args, **kwargs):
        return None

    sopel = bot.Sopel(tmpconfig, daemon=False)

    # now register a pattern, make sure it still work
    sopel.register_url_callback(test_pattern, url_handler)
    assert list(sopel.search_url_callbacks('https://www.example.com'))

    # unregister this pattern
    sopel.unregister_url_callback(test_pattern, url_handler)

    # now it is not possible to find a callback for this pattern
    results = list(sopel.search_url_callbacks('https://www.example.com'))
    assert not results, 'Unregistered URL callback must not work anymore'


def test_unregister_url_callback_no_memory(tmpconfig):
    """Test unregister_url_callback behavior when bot.memory empty"""
    test_pattern = r'https://(www\.)?example\.com'

    def url_handler(*args, **kwargs):
        return None

    sopel = bot.Sopel(tmpconfig, daemon=False)
    sopel.unregister_url_callback(test_pattern, url_handler)
    # no exception implies success


# Remove once manual callback management is deprecated (8.0)
def test_unregister_url_callback_manual(tmpconfig):
    """Test unregister_url_callback removes a specific callback that was added manually"""
    test_pattern = r'https://(www\.)?example\.com'

    def url_handler(*args, **kwargs):
        return None

    sopel = bot.Sopel(tmpconfig, daemon=False)
    sopel.memory["url_callbacks"] = SopelMemory()

    # register a callback manually
    sopel.memory["url_callbacks"][re.compile(test_pattern)] = url_handler
    results = list(sopel.search_url_callbacks("https://www.example.com"))
    assert results[0][0] == url_handler, "Callback must be present"

    # unregister it
    sopel.unregister_url_callback(test_pattern, url_handler)

    results = list(sopel.search_url_callbacks("https://www.example.com"))
    assert not results, "Callback should have been removed"


def test_unregister_url_callback_unknown_pattern(tmpconfig):
    """Test unregister_url_callback pass when pattern is unknown."""
    test_pattern = r'https://(www\.)?example\.com'

    def url_handler(*args, **kwargs):
        return None

    sopel = bot.Sopel(tmpconfig, daemon=False)

    # now register a pattern, make sure it still work
    sopel.register_url_callback(test_pattern, url_handler)
    assert list(sopel.search_url_callbacks('https://www.example.com'))

    # unregister another pattern (that doesn't exist)
    sopel.unregister_url_callback(r'http://localhost', url_handler)

    # the existing pattern still work
    assert list(sopel.search_url_callbacks('https://www.example.com'))


def test_unregister_url_callback_compiled_pattern(tmpconfig):
    """Test unregister_url_callback works with a compiled regex."""
    test_pattern = r'https://(www\.)?example\.com'
    url_regex = re.compile(test_pattern)

    def url_handler(*args, **kwargs):
        return None

    sopel = bot.Sopel(tmpconfig, daemon=False)

    # now register a pattern, make sure it still work
    sopel.register_url_callback(test_pattern, url_handler)
    assert list(sopel.search_url_callbacks('https://www.example.com'))

    # unregister using the compiled version
    sopel.unregister_url_callback(url_regex, url_handler)

    assert not list(sopel.search_url_callbacks('https://www.example.com'))


def test_multiple_url_callback(tmpconfig):
    """Test multiple URL callbacks for the same URL."""
    test_pattern_example = r'https://(www\.)?example\.com'
    test_pattern_global = r'https://.*\.com'

    def url_handler(*args, **kwargs):
        return None

    def url_handler_global(*args, **kwargs):
        return None

    sopel = bot.Sopel(tmpconfig, daemon=False)
    sopel.register_url_callback(test_pattern_example, url_handler)
    sopel.register_url_callback(test_pattern_global, url_handler_global)

    results = list(sopel.search_url_callbacks('https://example.com'))
    assert len(results) == 2
    handlers = [result[0] for result in results]

    assert url_handler in handlers
    assert url_handler_global in handlers

    # now unregister one of them: the other must still work
    sopel.unregister_url_callback(test_pattern_example, url_handler)

    results = list(sopel.search_url_callbacks('https://example.com'))
    assert len(results) == 1, 'Exactly one handler must remain'
    assert url_handler_global in results[0], 'Wrong remaining handler'
