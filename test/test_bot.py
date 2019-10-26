# coding=utf-8
"""Tests for core ``sopel.bot`` module"""
from __future__ import unicode_literals, absolute_import, print_function, division

import re

import pytest

from sopel import bot, config, plugins, trigger
from sopel.test_tools import MockIRCBackend, rawlist


@pytest.fixture
def tmpconfig(tmpdir):
    conf_file = tmpdir.join('conf.ini')
    conf_file.write("\n".join([
        "[core]",
        "owner = testnick",
        "nick = TestBot",
        "enable = coretasks"
        ""
    ]))
    return config.Config(conf_file.strpath)


@pytest.fixture
def mockbot(tmpconfig):
    obj = bot.Sopel(tmpconfig, daemon=False)
    obj.backend = MockIRCBackend(obj)
    return obj


def line(sopel, raw):
    return trigger.Trigger(
        sopel.settings,
        trigger.PreTrigger(sopel.nick, raw),
        re.match('.*', raw))


def test_wrapper_say(mockbot):
    message = line(
        mockbot, ':Test!test@example.com PRIVMSG #channel :test message')
    wrapper = bot.SopelWrapper(mockbot, message)
    wrapper.say('Hi!')

    assert mockbot.backend.message_sent == rawlist(
        'PRIVMSG #channel :Hi!'
    )


def test_wrapper_say_override_destination(mockbot):
    message = line(
        mockbot, ':Test!test@example.com PRIVMSG #channel :test message')
    wrapper = bot.SopelWrapper(mockbot, message)
    wrapper.say('Hi!', destination='#different')

    assert mockbot.backend.message_sent == rawlist(
        'PRIVMSG #different :Hi!'
    )


def test_wrapper_notice(mockbot):
    message = line(
        mockbot, ':Test!test@example.com PRIVMSG #channel :test message')
    wrapper = bot.SopelWrapper(mockbot, message)
    wrapper.notice('Hi!')

    assert mockbot.backend.message_sent == rawlist(
        'NOTICE #channel :Hi!'
    )


def test_wrapper_notice_override_destination(mockbot):
    message = line(
        mockbot, ':Test!test@example.com PRIVMSG #channel :test message')
    wrapper = bot.SopelWrapper(mockbot, message)
    wrapper.notice('Hi!', destination='#different')

    assert mockbot.backend.message_sent == rawlist(
        'NOTICE #different :Hi!'
    )


def test_wrapper_action(mockbot):
    message = line(
        mockbot, ':Test!test@example.com PRIVMSG #channel :test message')
    wrapper = bot.SopelWrapper(mockbot, message)
    wrapper.action('Hi!')

    assert mockbot.backend.message_sent == rawlist(
        'PRIVMSG #channel :\x01ACTION Hi!\x01'
    )


def test_wrapper_action_override_destination(mockbot):
    message = line(
        mockbot, ':Test!test@example.com PRIVMSG #channel :test message')
    wrapper = bot.SopelWrapper(mockbot, message)
    wrapper.action('Hi!', destination='#different')

    assert mockbot.backend.message_sent == rawlist(
        'PRIVMSG #different :\x01ACTION Hi!\x01'
    )


def test_wrapper_reply(mockbot):
    message = line(
        mockbot, ':Test!test@example.com PRIVMSG #channel :test message')
    wrapper = bot.SopelWrapper(mockbot, message)
    wrapper.reply('Hi!')

    assert mockbot.backend.message_sent == rawlist(
        'PRIVMSG #channel :Test: Hi!'
    )


def test_wrapper_reply_override_destination(mockbot):
    message = line(
        mockbot, ':Test!test@example.com PRIVMSG #channel :test message')
    wrapper = bot.SopelWrapper(mockbot, message)
    wrapper.reply('Hi!', destination='#another')

    assert mockbot.backend.message_sent == rawlist(
        'PRIVMSG #another :Test: Hi!'
    )


def test_wrapper_reply_override_reply_to(mockbot):
    message = line(
        mockbot, ':Test!test@example.com PRIVMSG #channel :test message')
    wrapper = bot.SopelWrapper(mockbot, message)
    wrapper.reply('Hi!', reply_to='Admin')

    assert mockbot.backend.message_sent == rawlist(
        'PRIVMSG #channel :Admin: Hi!'
    )


def test_wrapper_reply_override_destination_reply_to(mockbot):
    message = line(
        mockbot, ':Test!test@example.com PRIVMSG #channel :test message')
    wrapper = bot.SopelWrapper(mockbot, message)
    wrapper.reply('Hi!', destination='#another', reply_to='Admin')

    assert mockbot.backend.message_sent == rawlist(
        'PRIVMSG #another :Admin: Hi!'
    )


def test_wrapper_kick(mockbot):
    message = line(
        mockbot, ':Test!test@example.com PRIVMSG #channel :test message')
    wrapper = bot.SopelWrapper(mockbot, message)
    wrapper.kick('SpamUser')

    assert mockbot.backend.message_sent == rawlist(
        'KICK #channel SpamUser'
    )


def test_wrapper_kick_message(mockbot):
    message = line(
        mockbot, ':Test!test@example.com PRIVMSG #channel :test message')
    wrapper = bot.SopelWrapper(mockbot, message)
    wrapper.kick('SpamUser', message='Test reason')

    assert mockbot.backend.message_sent == rawlist(
        'KICK #channel SpamUser :Test reason'
    )


def test_wrapper_kick_error_nick(mockbot):
    message = line(
        mockbot, ':Test!test@example.com PRIVMSG #channel :test message')
    wrapper = bot.SopelWrapper(mockbot, message)
    with pytest.raises(RuntimeError):
        wrapper.kick(None)

    assert mockbot.backend.message_sent == []


def test_wrapper_kick_error_channel(mockbot):
    message = line(
        mockbot, ':Test!test@example.com PRIVMSG OtherUser :test message')
    wrapper = bot.SopelWrapper(mockbot, message)
    with pytest.raises(RuntimeError):
        wrapper.kick('SpamUser')

    assert mockbot.backend.message_sent == []


def test_wrapper_kick_override_destination(mockbot):
    message = line(
        mockbot, ':Test!test@example.com PRIVMSG #channel :test message')
    wrapper = bot.SopelWrapper(mockbot, message)
    wrapper.kick('SpamUser', channel='#another')

    assert mockbot.backend.message_sent == rawlist(
        'KICK #another SpamUser'
    )


def test_wrapper_kick_override_destination_message(mockbot):
    message = line(
        mockbot, ':Test!test@example.com PRIVMSG #channel :test message')
    wrapper = bot.SopelWrapper(mockbot, message)
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
