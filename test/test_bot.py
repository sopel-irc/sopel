# coding=utf-8
"""Tests for core ``sopel.bot`` module"""
from __future__ import absolute_import, division, print_function, unicode_literals

import re

import pytest

from sopel import bot, loader, module, plugin, plugins, trigger
from sopel.plugins import rules
from sopel.tests import rawlist
from sopel.tools import Identifier, SopelMemory


TMP_CONFIG = """
[core]
owner = testnick
nick = TestBot
enable = coretasks
"""

MOCK_MODULE_CONTENT = """# coding=utf-8
import sopel.module


@sopel.module.commands("do")
def command_do(bot, trigger):
    pass


@sopel.module.nickname_commands("info")
def nick_command_info(bot, trigger):
    pass


@sopel.module.action_commands("tell")
def action_command_tell(bot, trigger):
    pass


@sopel.module.interval(5)
def interval5s(bot):
    pass


@sopel.module.interval(10)
def interval10s(bot):
    pass


@sopel.module.url(r'(.+\\.)?example\\.com')
def example_url(bot):
    pass


@sopel.module.rule(r'Hello \\w+')
def rule_hello(bot):
    pass


@sopel.module.event('TOPIC')
def rule_on_topic(bot):
    pass


def shutdown():
    pass


def ignored():
    pass

"""


@pytest.fixture
def tmpconfig(configfactory):
    return configfactory('test.cfg', TMP_CONFIG)


@pytest.fixture
def mockbot(tmpconfig, botfactory):
    return botfactory(tmpconfig)


@pytest.fixture
def mockplugin(tmpdir):
    root = tmpdir.mkdir('loader_mods')
    mod_file = root.join('mockplugin.py')
    mod_file.write(MOCK_MODULE_CONTENT)

    return plugins.handlers.PyFilePlugin(mod_file.strpath)


# -----------------------------------------------------------------------------
# sopel.bot.SopelWrapper

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


# -----------------------------------------------------------------------------
# Register/Unregister plugins

def test_register_plugin(tmpconfig, mockplugin):
    sopel = bot.Sopel(tmpconfig)
    assert not sopel.has_plugin('mockplugin')

    mockplugin.load()
    mockplugin.setup(sopel)
    mockplugin.register(sopel)

    assert sopel.has_plugin('mockplugin')
    assert sopel.rules.has_command('do')
    assert sopel.rules.has_command('do', plugin='mockplugin')
    assert sopel.rules.has_nick_command('info')
    assert sopel.rules.has_nick_command('info', plugin='mockplugin')
    assert sopel.rules.has_action_command('tell')
    assert sopel.rules.has_action_command('tell', plugin='mockplugin')
    assert sopel.rules.has_url_callback('example_url')
    assert sopel.rules.has_url_callback('example_url', plugin='mockplugin')


def test_register_unregister_plugin(tmpconfig, mockplugin):
    sopel = bot.Sopel(tmpconfig, daemon=False)

    # register the plugin
    mockplugin.load()
    mockplugin.register(sopel)
    assert sopel.has_plugin('mockplugin'), 'The mockplugin must be registered!'

    # unregister it
    mockplugin.unregister(sopel)
    assert not sopel.has_plugin('mockplugin')
    assert not sopel.rules.has_command('do')
    assert not sopel.rules.has_nick_command('info')
    assert not sopel.rules.has_action_command('tell')


def test_remove_plugin_unknown_plugin(tmpconfig):
    sopel = bot.Sopel(tmpconfig, daemon=False)

    handler = plugins.handlers.PyModulePlugin('admin', 'sopel.modules')
    with pytest.raises(plugins.exceptions.PluginNotRegistered):
        sopel.remove_plugin(handler, [], [], [], [])


def test_remove_plugin_unregistered_plugin(tmpconfig):
    sopel = bot.Sopel(tmpconfig, daemon=False)

    # register the plugin
    handler = plugins.handlers.PyModulePlugin('coretasks', 'sopel')
    handler.load()
    handler.register(sopel)

    # Unregister the plugin
    handler.unregister(sopel)

    # And now it must raise an exception
    with pytest.raises(plugins.exceptions.PluginNotRegistered):
        sopel.remove_plugin(handler, [], [], [], [])


def test_reload_plugin_unregistered_plugin(tmpconfig):
    sopel = bot.Sopel(tmpconfig, daemon=False)

    # register the plugin
    handler = plugins.handlers.PyModulePlugin('coretasks', 'sopel')
    handler.load()
    handler.register(sopel)

    # Unregister the plugin
    handler.unregister(sopel)

    # And now it must raise an exception
    with pytest.raises(plugins.exceptions.PluginNotRegistered):
        sopel.reload_plugin(handler.name)


# -----------------------------------------------------------------------------
# register callables, jobs, shutdown, urls

def test_register_callables(tmpconfig):
    sopel = bot.Sopel(tmpconfig)

    @module.rule(r'(hi|hello|hey|sup)')
    def rule_hello(bot, trigger):
        pass

    @plugin.rule_lazy(lambda *args: [re.compile(r'say what')])
    def rule_say_what(bot, trigger):
        pass

    @plugin.find(r'(hi|hello|hey|sup)')
    def rule_find_hello(bot, trigger):
        pass

    @plugin.find_lazy(lambda *args: [re.compile(r'what')])
    def rule_find_what(bot, trigger):
        pass

    @plugin.search(r'(hi|hello|hey|sup)')
    def rule_search_hello(bot, trigger):
        pass

    @plugin.search_lazy(lambda *args: [re.compile(r'what')])
    def rule_search_what(bot, trigger):
        pass

    @module.commands('do')
    @module.example('.do nothing')
    def command_do(bot, trigger):
        """The do command does nothing."""
        pass

    @module.commands('main sub')
    @module.example('.main sub')
    def command_main_sub(bot, trigger):
        """A command with subcommand sub."""
        pass

    @module.commands('main other')
    @module.example('.main other')
    def command_main_other(bot, trigger):
        """A command with subcommand other."""
        pass

    @module.nickname_commands('info')
    @module.example('$nickname: info about this')
    def nick_command_info(bot, trigger):
        """Ask Sopel to get some info about nothing."""
        pass

    @module.action_commands('tell')
    def action_command_tell(bot, trigger):
        pass

    @module.commands('mixed')
    @module.rule('mixing')
    def mixed_rule_command(bot, trigger):
        pass

    @module.event('JOIN')
    @plugin.label('handle_join_event')
    def on_join(bot, trigger):
        pass

    # prepare callables to be registered
    callables = [
        rule_hello,
        rule_say_what,
        rule_find_hello,
        rule_find_what,
        rule_search_hello,
        rule_search_what,
        command_do,
        command_main_sub,
        command_main_other,
        nick_command_info,
        action_command_tell,
        mixed_rule_command,
        on_join,
    ]

    # clean callables and set plugin name by hand
    # since the loader and plugin handlers are excluded here
    for handler in callables:
        loader.clean_callable(handler, tmpconfig)
        handler.plugin_name = 'testplugin'

    # register callables
    sopel.register_callables(callables)

    # trigger rule "hello"
    line = ':Foo!foo@example.com PRIVMSG #sopel :hello'
    pretrigger = trigger.PreTrigger(sopel.nick, line)

    matches = sopel.rules.get_triggered_rules(sopel, pretrigger)
    assert len(matches) == 3
    assert matches[0][0].get_rule_label() == 'rule_hello'
    assert matches[1][0].get_rule_label() == 'rule_find_hello'
    assert matches[2][0].get_rule_label() == 'rule_search_hello'

    # trigger lazy rule "say what"
    line = ':Foo!foo@example.com PRIVMSG #sopel :say what now?'
    pretrigger = trigger.PreTrigger(sopel.nick, line)

    matches = sopel.rules.get_triggered_rules(sopel, pretrigger)
    assert len(matches) == 3
    assert matches[0][0].get_rule_label() == 'rule_say_what'
    assert matches[1][0].get_rule_label() == 'rule_find_what'
    assert matches[2][0].get_rule_label() == 'rule_search_what'

    # trigger command "do"
    line = ':Foo!foo@example.com PRIVMSG #sopel :.do'
    pretrigger = trigger.PreTrigger(sopel.nick, line)

    matches = sopel.rules.get_triggered_rules(sopel, pretrigger)
    assert len(matches) == 1
    assert matches[0][0].get_rule_label() == 'do'

    # trigger command with subcommand "main-sub"
    line = ':Foo!foo@example.com PRIVMSG #sopel :.main sub'
    pretrigger = trigger.PreTrigger(sopel.nick, line)

    matches = sopel.rules.get_triggered_rules(sopel, pretrigger)
    assert len(matches) == 1
    assert matches[0][0].get_rule_label() == 'main-sub'

    # trigger command with the other subcommand "main-other"
    line = ':Foo!foo@example.com PRIVMSG #sopel :.main other'
    pretrigger = trigger.PreTrigger(sopel.nick, line)

    matches = sopel.rules.get_triggered_rules(sopel, pretrigger)
    assert len(matches) == 1
    assert matches[0][0].get_rule_label() == 'main-other'

    # trigger nick command "info"
    line = ':Foo!foo@example.com PRIVMSG #sopel :TestBot: info'
    pretrigger = trigger.PreTrigger(sopel.nick, line)

    matches = sopel.rules.get_triggered_rules(sopel, pretrigger)
    assert len(matches) == 1
    assert matches[0][0].get_rule_label() == 'info'

    # trigger action command "tell"
    line = ':Foo!foo@example.com PRIVMSG #sopel :\x01ACTION tell\x01'
    pretrigger = trigger.PreTrigger(sopel.nick, line)

    matches = sopel.rules.get_triggered_rules(sopel, pretrigger)
    assert len(matches) == 1
    assert matches[0][0].get_rule_label() == 'tell'

    # trigger rules with event
    line = ':Foo!foo@example.com JOIN #Sopel'
    pretrigger = trigger.PreTrigger(sopel.nick, line)

    matches = sopel.rules.get_triggered_rules(sopel, pretrigger)
    assert len(matches) == 1
    assert matches[0][0].get_rule_label() == 'handle_join_event'

    # trigger command "mixed"
    line = ':Foo!foo@example.com PRIVMSG #sopel :.mixed'
    pretrigger = trigger.PreTrigger(sopel.nick, line)

    matches = sopel.rules.get_triggered_rules(sopel, pretrigger)
    assert len(matches) == 1
    assert matches[0][0].get_rule_label() == 'mixed'

    # trigger rule "mixed_rule_command"
    line = ':Foo!foo@example.com PRIVMSG #sopel :mixing'
    pretrigger = trigger.PreTrigger(sopel.nick, line)

    matches = sopel.rules.get_triggered_rules(sopel, pretrigger)
    assert len(matches) == 1
    assert matches[0][0].get_rule_label() == 'mixed_rule_command'

    # check documentation
    assert sopel.command_groups == {
        'testplugin': ['do', 'info', 'main other', 'main sub', 'mixed'],
    }

    assert sopel.doc == {
        'do': (
            ['The do command does nothing.'],
            ['.do nothing'],
        ),
        'info': (
            ['Ask Sopel to get some info about nothing.'],
            ['TestBot: info about this'],
        ),
        'main sub': (
            ['A command with subcommand sub.'],
            ['.main sub'],
        ),
        'main other': (
            ['A command with subcommand other.'],
            ['.main other'],
        ),
        'mixed': (
            [],
            [],
        )
    }


def test_register_urls(tmpconfig):
    sopel = bot.Sopel(tmpconfig)

    @module.url(r'https://(\S+)/(.+)?')
    @plugin.label('handle_urls_https')
    def url_callback_https(bot, trigger, match):
        pass

    @module.url(r'http://(\S+)/(.+)?')
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

    # trigger URL callback "handle_urls_https"
    line = ':Foo!foo@example.com PRIVMSG #sopel :https://example.com/test'
    pretrigger = trigger.PreTrigger(sopel.nick, line)

    matches = sopel.rules.get_triggered_rules(sopel, pretrigger)
    assert len(matches) == 1
    assert matches[0][0].get_rule_label() == 'handle_urls_https'

    # trigger URL callback "handle_urls_https"
    line = ':Foo!foo@example.com PRIVMSG #sopel :http://example.com/test'
    pretrigger = trigger.PreTrigger(sopel.nick, line)

    matches = sopel.rules.get_triggered_rules(sopel, pretrigger)
    assert len(matches) == 1
    assert matches[0][0].get_rule_label() == 'handle_urls_http'


# -----------------------------------------------------------------------------
# call_rule

def test_call_rule(mockbot):
    # setup
    items = []

    def testrule(bot, trigger):
        bot.say('hi')
        items.append(1)
        return "Return Value"

    rule_hello = rules.Rule(
        [re.compile(r'(hi|hello|hey|sup)')],
        plugin='testplugin',
        label='testrule',
        handler=testrule)

    # trigger
    line = ':Test!test@example.com PRIVMSG #channel :hello'
    pretrigger = trigger.PreTrigger(mockbot.nick, line)

    # match
    matches = list(rule_hello.match(mockbot, pretrigger))
    assert len(matches) == 1
    match = matches[0]

    # trigger and wrapper
    rule_trigger = trigger.Trigger(
        mockbot.settings, pretrigger, match, account=None)
    wrapper = bot.SopelWrapper(mockbot, rule_trigger)

    # call rule
    mockbot.call_rule(rule_hello, wrapper, rule_trigger)

    # assert the rule has been executed
    assert mockbot.backend.message_sent == rawlist(
        'PRIVMSG #channel :hi'
    )
    assert items == [1]

    # assert the rule is not rate limited
    assert not rule_hello.is_rate_limited(Identifier('Test'))
    assert not rule_hello.is_channel_rate_limited('#channel')
    assert not rule_hello.is_global_rate_limited()

    # call rule again
    mockbot.call_rule(rule_hello, wrapper, rule_trigger)

    # assert the rule has been executed twice now
    assert mockbot.backend.message_sent == rawlist(
        'PRIVMSG #channel :hi',
        'PRIVMSG #channel :hi',
    )
    assert items == [1, 1]


def test_call_rule_rate_limited_user(mockbot):
    items = []

    # setup
    def testrule(bot, trigger):
        bot.say('hi')
        items.append(1)
        return "Return Value"

    rule_hello = rules.Rule(
        [re.compile(r'(hi|hello|hey|sup)')],
        plugin='testplugin',
        label='testrule',
        handler=testrule,
        rate_limit=100)

    # trigger
    line = ':Test!test@example.com PRIVMSG #channel :hello'
    pretrigger = trigger.PreTrigger(mockbot.nick, line)

    # match
    matches = list(rule_hello.match(mockbot, pretrigger))
    match = matches[0]

    # trigger and wrapper
    rule_trigger = trigger.Trigger(
        mockbot.settings, pretrigger, match, account=None)
    wrapper = bot.SopelWrapper(mockbot, rule_trigger)

    # call rule
    mockbot.call_rule(rule_hello, wrapper, rule_trigger)

    # assert the rule has been executed
    assert mockbot.backend.message_sent == rawlist(
        'PRIVMSG #channel :hi'
    )
    assert items == [1]

    # assert the rule is now rate limited
    assert rule_hello.is_rate_limited(Identifier('Test'))
    assert not rule_hello.is_channel_rate_limited('#channel')
    assert not rule_hello.is_global_rate_limited()

    # call rule again
    mockbot.call_rule(rule_hello, wrapper, rule_trigger)

    # assert no new message
    assert mockbot.backend.message_sent == rawlist(
        'PRIVMSG #channel :hi'
    ), 'There must not be any new message sent'
    assert items == [1], 'There must not be any new item'


def test_call_rule_rate_limited_channel(mockbot):
    items = []

    # setup
    def testrule(bot, trigger):
        bot.say('hi')
        items.append(1)
        return "Return Value"

    rule_hello = rules.Rule(
        [re.compile(r'(hi|hello|hey|sup)')],
        plugin='testplugin',
        label='testrule',
        handler=testrule,
        channel_rate_limit=100)

    # trigger
    line = ':Test!test@example.com PRIVMSG #channel :hello'
    pretrigger = trigger.PreTrigger(mockbot.nick, line)

    # match
    matches = list(rule_hello.match(mockbot, pretrigger))
    match = matches[0]

    # trigger and wrapper
    rule_trigger = trigger.Trigger(
        mockbot.settings, pretrigger, match, account=None)
    wrapper = bot.SopelWrapper(mockbot, rule_trigger)

    # call rule
    mockbot.call_rule(rule_hello, wrapper, rule_trigger)

    # assert the rule is now rate limited
    assert not rule_hello.is_rate_limited(Identifier('Test'))
    assert rule_hello.is_channel_rate_limited('#channel')
    assert not rule_hello.is_global_rate_limited()

    # call rule again
    mockbot.call_rule(rule_hello, wrapper, rule_trigger)

    # assert no new message
    assert mockbot.backend.message_sent == rawlist(
        'PRIVMSG #channel :hi'
    ), 'There must not be any new message sent'
    assert items == [1], 'There must not be any new item'


def test_call_rule_rate_limited_global(mockbot):
    items = []

    # setup
    def testrule(bot, trigger):
        bot.say('hi')
        items.append(1)
        return "Return Value"

    rule_hello = rules.Rule(
        [re.compile(r'(hi|hello|hey|sup)')],
        plugin='testplugin',
        label='testrule',
        handler=testrule,
        global_rate_limit=100)

    # trigger
    line = ':Test!test@example.com PRIVMSG #channel :hello'
    pretrigger = trigger.PreTrigger(mockbot.nick, line)

    # match
    matches = list(rule_hello.match(mockbot, pretrigger))
    match = matches[0]

    # trigger and wrapper
    rule_trigger = trigger.Trigger(
        mockbot.settings, pretrigger, match, account=None)
    wrapper = bot.SopelWrapper(mockbot, rule_trigger)

    # call rule
    mockbot.call_rule(rule_hello, wrapper, rule_trigger)

    # assert the rule is now rate limited
    assert not rule_hello.is_rate_limited(Identifier('Test'))
    assert not rule_hello.is_channel_rate_limited('#channel')
    assert rule_hello.is_global_rate_limited()

    # call rule again
    mockbot.call_rule(rule_hello, wrapper, rule_trigger)

    # assert no new message
    assert mockbot.backend.message_sent == rawlist(
        'PRIVMSG #channel :hi'
    ), 'There must not be any new message sent'
    assert items == [1], 'There must not be any new item'


# -----------------------------------------------------------------------------
# Channel privileges


def test_has_channel_privilege_no_privilege(ircfactory, botfactory, tmpconfig):
    sopel = botfactory.preloaded(tmpconfig)
    server = ircfactory(sopel)
    name = Identifier('#adminchannel')

    # unknown channel
    with pytest.raises(ValueError):
        sopel.has_channel_privilege('#adminchannel', plugin.VOICE)

    # join channel
    server.channel_joined('#adminchannel')

    # check privileges
    assert not sopel.has_channel_privilege(name, plugin.VOICE)
    assert not sopel.has_channel_privilege('#adminchannel', plugin.VOICE)
    assert not sopel.has_channel_privilege(name, plugin.HALFOP)
    assert not sopel.has_channel_privilege('#adminchannel', plugin.HALFOP)
    assert not sopel.has_channel_privilege(name, plugin.OP)
    assert not sopel.has_channel_privilege('#adminchannel', plugin.OP)
    assert not sopel.has_channel_privilege(name, plugin.ADMIN)
    assert not sopel.has_channel_privilege('#adminchannel', plugin.ADMIN)
    assert not sopel.has_channel_privilege(name, plugin.OWNER)
    assert not sopel.has_channel_privilege('#adminchannel', plugin.OWNER)
    assert not sopel.has_channel_privilege(name, plugin.OPER)
    assert not sopel.has_channel_privilege('#adminchannel', plugin.OPER)

    # unknown channel
    with pytest.raises(ValueError):
        sopel.has_channel_privilege('#anotherchannel', plugin.VOICE)


def test_has_channel_privilege_voice(ircfactory, botfactory, tmpconfig):
    sopel = botfactory.preloaded(tmpconfig)
    server = ircfactory(sopel)
    name = Identifier('#adminchannel')

    # join channel
    server.channel_joined('#adminchannel')
    server.mode_set('#adminchannel', '+v', [sopel.nick])

    assert sopel.has_channel_privilege(name, plugin.VOICE)
    assert sopel.has_channel_privilege('#adminchannel', plugin.VOICE)
    assert not sopel.has_channel_privilege(name, plugin.HALFOP)
    assert not sopel.has_channel_privilege('#adminchannel', plugin.HALFOP)
    assert not sopel.has_channel_privilege(name, plugin.OP)
    assert not sopel.has_channel_privilege('#adminchannel', plugin.OP)
    assert not sopel.has_channel_privilege(name, plugin.ADMIN)
    assert not sopel.has_channel_privilege('#adminchannel', plugin.ADMIN)
    assert not sopel.has_channel_privilege(name, plugin.OWNER)
    assert not sopel.has_channel_privilege('#adminchannel', plugin.OWNER)
    assert not sopel.has_channel_privilege(name, plugin.OPER)
    assert not sopel.has_channel_privilege('#adminchannel', plugin.OPER)


def test_has_channel_privilege_halfop(ircfactory, botfactory, tmpconfig):
    sopel = botfactory.preloaded(tmpconfig)
    server = ircfactory(sopel)
    name = Identifier('#adminchannel')

    # join channel
    server.channel_joined('#adminchannel')
    server.mode_set('#adminchannel', '+h', [sopel.nick])

    assert sopel.has_channel_privilege(name, plugin.VOICE)
    assert sopel.has_channel_privilege('#adminchannel', plugin.VOICE)
    assert sopel.has_channel_privilege(name, plugin.HALFOP)
    assert sopel.has_channel_privilege('#adminchannel', plugin.HALFOP)
    assert not sopel.has_channel_privilege(name, plugin.OP)
    assert not sopel.has_channel_privilege('#adminchannel', plugin.OP)
    assert not sopel.has_channel_privilege(name, plugin.ADMIN)
    assert not sopel.has_channel_privilege('#adminchannel', plugin.ADMIN)
    assert not sopel.has_channel_privilege(name, plugin.OWNER)
    assert not sopel.has_channel_privilege('#adminchannel', plugin.OWNER)
    assert not sopel.has_channel_privilege(name, plugin.OPER)
    assert not sopel.has_channel_privilege('#adminchannel', plugin.OPER)


def test_has_channel_privilege_op(ircfactory, botfactory, tmpconfig):
    sopel = botfactory.preloaded(tmpconfig)
    server = ircfactory(sopel)
    name = Identifier('#adminchannel')

    # join channel
    server.channel_joined('#adminchannel')
    server.mode_set('#adminchannel', '+o', [sopel.nick])

    assert sopel.has_channel_privilege(name, plugin.VOICE)
    assert sopel.has_channel_privilege('#adminchannel', plugin.VOICE)
    assert sopel.has_channel_privilege(name, plugin.HALFOP)
    assert sopel.has_channel_privilege('#adminchannel', plugin.HALFOP)
    assert sopel.has_channel_privilege(name, plugin.OP)
    assert sopel.has_channel_privilege('#adminchannel', plugin.OP)
    assert not sopel.has_channel_privilege(name, plugin.ADMIN)
    assert not sopel.has_channel_privilege('#adminchannel', plugin.ADMIN)
    assert not sopel.has_channel_privilege(name, plugin.OWNER)
    assert not sopel.has_channel_privilege('#adminchannel', plugin.OWNER)
    assert not sopel.has_channel_privilege(name, plugin.OPER)
    assert not sopel.has_channel_privilege('#adminchannel', plugin.OPER)


def test_has_channel_privilege_admin(ircfactory, botfactory, tmpconfig):
    sopel = botfactory.preloaded(tmpconfig)
    server = ircfactory(sopel)
    name = Identifier('#adminchannel')

    # join channel
    server.channel_joined('#adminchannel')
    server.mode_set('#adminchannel', '+a', [sopel.nick])

    assert sopel.has_channel_privilege(name, plugin.VOICE)
    assert sopel.has_channel_privilege('#adminchannel', plugin.VOICE)
    assert sopel.has_channel_privilege(name, plugin.HALFOP)
    assert sopel.has_channel_privilege('#adminchannel', plugin.HALFOP)
    assert sopel.has_channel_privilege(name, plugin.OP)
    assert sopel.has_channel_privilege('#adminchannel', plugin.OP)
    assert sopel.has_channel_privilege(name, plugin.ADMIN)
    assert sopel.has_channel_privilege('#adminchannel', plugin.ADMIN)
    assert not sopel.has_channel_privilege(name, plugin.OWNER)
    assert not sopel.has_channel_privilege('#adminchannel', plugin.OWNER)
    assert not sopel.has_channel_privilege(name, plugin.OPER)
    assert not sopel.has_channel_privilege('#adminchannel', plugin.OPER)


def test_has_channel_privilege_owner(ircfactory, botfactory, tmpconfig):
    sopel = botfactory.preloaded(tmpconfig)
    server = ircfactory(sopel)
    name = Identifier('#adminchannel')

    # join channel
    server.channel_joined('#adminchannel')
    server.mode_set('#adminchannel', '+q', [sopel.nick])

    assert sopel.has_channel_privilege(name, plugin.VOICE)
    assert sopel.has_channel_privilege('#adminchannel', plugin.VOICE)
    assert sopel.has_channel_privilege(name, plugin.HALFOP)
    assert sopel.has_channel_privilege('#adminchannel', plugin.HALFOP)
    assert sopel.has_channel_privilege(name, plugin.OP)
    assert sopel.has_channel_privilege('#adminchannel', plugin.OP)
    assert sopel.has_channel_privilege(name, plugin.ADMIN)
    assert sopel.has_channel_privilege('#adminchannel', plugin.ADMIN)
    assert sopel.has_channel_privilege(name, plugin.OWNER)
    assert sopel.has_channel_privilege('#adminchannel', plugin.OWNER)
    assert not sopel.has_channel_privilege(name, plugin.OPER)
    assert not sopel.has_channel_privilege('#adminchannel', plugin.OPER)


def test_has_channel_privilege_operator(ircfactory, botfactory, tmpconfig):
    sopel = botfactory.preloaded(tmpconfig)
    server = ircfactory(sopel)
    name = Identifier('#adminchannel')

    # join channel
    server.channel_joined('#adminchannel')
    server.mode_set('#adminchannel', '+y', [sopel.nick])

    assert sopel.has_channel_privilege(name, plugin.VOICE)
    assert sopel.has_channel_privilege('#adminchannel', plugin.VOICE)
    assert sopel.has_channel_privilege(name, plugin.HALFOP)
    assert sopel.has_channel_privilege('#adminchannel', plugin.HALFOP)
    assert sopel.has_channel_privilege(name, plugin.OP)
    assert sopel.has_channel_privilege('#adminchannel', plugin.OP)
    assert sopel.has_channel_privilege(name, plugin.ADMIN)
    assert sopel.has_channel_privilege('#adminchannel', plugin.ADMIN)
    assert sopel.has_channel_privilege(name, plugin.OWNER)
    assert sopel.has_channel_privilege('#adminchannel', plugin.OWNER)
    assert sopel.has_channel_privilege(name, plugin.OPER)
    assert sopel.has_channel_privilege('#adminchannel', plugin.OPER)


# -----------------------------------------------------------------------------
# URL Callbacks

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
