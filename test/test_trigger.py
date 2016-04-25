# coding=utf-8
"""Tests for message parsing"""
from __future__ import unicode_literals, absolute_import, print_function, division

import re
import pytest
import datetime

from sopel.test_tools import MockConfig
from sopel.trigger import PreTrigger, Trigger
from sopel.tools import Identifier


@pytest.fixture
def nick():
    return Identifier('Sopel')


def test_basic_pretrigger(nick):
    line = ':Foo!foo@example.com PRIVMSG #Sopel :Hello, world'
    pretrigger = PreTrigger(nick, line)
    assert pretrigger.tags == {}
    assert pretrigger.hostmask == 'Foo!foo@example.com'
    assert pretrigger.line == line
    assert pretrigger.args == ['#Sopel', 'Hello, world']
    assert pretrigger.event == 'PRIVMSG'
    assert pretrigger.nick == Identifier('Foo')
    assert pretrigger.user == 'foo'
    assert pretrigger.host == 'example.com'
    assert pretrigger.sender == '#Sopel'


def test_pm_pretrigger(nick):
    line = ':Foo!foo@example.com PRIVMSG Sopel :Hello, world'
    pretrigger = PreTrigger(nick, line)
    assert pretrigger.tags == {}
    assert pretrigger.hostmask == 'Foo!foo@example.com'
    assert pretrigger.line == line
    assert pretrigger.args == ['Sopel', 'Hello, world']
    assert pretrigger.event == 'PRIVMSG'
    assert pretrigger.nick == Identifier('Foo')
    assert pretrigger.user == 'foo'
    assert pretrigger.host == 'example.com'
    assert pretrigger.sender == Identifier('Foo')


def test_quit_pretrigger(nick):
    line = ':Foo!foo@example.com QUIT :quit message text'
    pretrigger = PreTrigger(nick, line)
    assert pretrigger.tags == {}
    assert pretrigger.hostmask == 'Foo!foo@example.com'
    assert pretrigger.line == line
    assert pretrigger.args == ['quit message text']
    assert pretrigger.event == 'QUIT'
    assert pretrigger.nick == Identifier('Foo')
    assert pretrigger.user == 'foo'
    assert pretrigger.host == 'example.com'
    assert pretrigger.sender is None


def test_join_pretrigger(nick):
    line = ':Foo!foo@example.com JOIN #Sopel'
    pretrigger = PreTrigger(nick, line)
    assert pretrigger.tags == {}
    assert pretrigger.hostmask == 'Foo!foo@example.com'
    assert pretrigger.line == line
    assert pretrigger.args == ['#Sopel']
    assert pretrigger.event == 'JOIN'
    assert pretrigger.nick == Identifier('Foo')
    assert pretrigger.user == 'foo'
    assert pretrigger.host == 'example.com'
    assert pretrigger.sender == Identifier('#Sopel')


def test_tags_pretrigger(nick):
    line = '@foo=bar;baz;sopel.chat/special=value :Foo!foo@example.com PRIVMSG #Sopel :Hello, world'
    pretrigger = PreTrigger(nick, line)
    assert pretrigger.tags == {'baz': None,
                               'foo': 'bar',
                               'sopel.chat/special': 'value'}
    assert pretrigger.hostmask == 'Foo!foo@example.com'
    assert pretrigger.line == line
    assert pretrigger.args == ['#Sopel', 'Hello, world']
    assert pretrigger.event == 'PRIVMSG'
    assert pretrigger.nick == Identifier('Foo')
    assert pretrigger.user == 'foo'
    assert pretrigger.host == 'example.com'
    assert pretrigger.sender == '#Sopel'


def test_intents_pretrigger(nick):
    line = '@intent=ACTION :Foo!foo@example.com PRIVMSG #Sopel :Hello, world'
    pretrigger = PreTrigger(nick, line)
    assert pretrigger.tags == {'intent': 'ACTION'}
    assert pretrigger.hostmask == 'Foo!foo@example.com'
    assert pretrigger.line == line
    assert pretrigger.args == ['#Sopel', 'Hello, world']
    assert pretrigger.event == 'PRIVMSG'
    assert pretrigger.nick == Identifier('Foo')
    assert pretrigger.user == 'foo'
    assert pretrigger.host == 'example.com'
    assert pretrigger.sender == '#Sopel'


def test_unusual_pretrigger(nick):
    line = 'PING'
    pretrigger = PreTrigger(nick, line)
    assert pretrigger.tags == {}
    assert pretrigger.hostmask is None
    assert pretrigger.line == line
    assert pretrigger.args == []
    assert pretrigger.event == 'PING'


def test_ctcp_intent_pretrigger(nick):
    line = ':Foo!foo@example.com PRIVMSG Sopel :\x01VERSION\x01'
    pretrigger = PreTrigger(nick, line)
    assert pretrigger.tags == {'intent': 'VERSION'}
    assert pretrigger.hostmask == 'Foo!foo@example.com'
    assert pretrigger.line == line
    assert pretrigger.args == ['Sopel', '']
    assert pretrigger.event == 'PRIVMSG'
    assert pretrigger.nick == Identifier('Foo')
    assert pretrigger.user == 'foo'
    assert pretrigger.host == 'example.com'
    assert pretrigger.sender == Identifier('Foo')


def test_ctcp_data_pretrigger(nick):
    line = ':Foo!foo@example.com PRIVMSG Sopel :\x01PING 1123321\x01'
    pretrigger = PreTrigger(nick, line)
    assert pretrigger.tags == {'intent': 'PING'}
    assert pretrigger.hostmask == 'Foo!foo@example.com'
    assert pretrigger.line == line
    assert pretrigger.args == ['Sopel', '1123321']
    assert pretrigger.event == 'PRIVMSG'
    assert pretrigger.nick == Identifier('Foo')
    assert pretrigger.user == 'foo'
    assert pretrigger.host == 'example.com'
    assert pretrigger.sender == Identifier('Foo')


def test_ircv3_extended_join_pretrigger(nick):
    line = ':Foo!foo@example.com JOIN #Sopel bar :Real Name'
    pretrigger = PreTrigger(nick, line)
    assert pretrigger.tags == {'account': 'bar'}
    assert pretrigger.hostmask == 'Foo!foo@example.com'
    assert pretrigger.line == line
    assert pretrigger.args == ['#Sopel', 'bar', 'Real Name']
    assert pretrigger.event == 'JOIN'
    assert pretrigger.nick == Identifier('Foo')
    assert pretrigger.user == 'foo'
    assert pretrigger.host == 'example.com'
    assert pretrigger.sender == Identifier('#Sopel')


def test_ircv3_extended_join_trigger(nick):
    line = ':Foo!foo@example.com JOIN #Sopel bar :Real Name'
    pretrigger = PreTrigger(nick, line)

    config = MockConfig()
    config.core.owner_account = 'bar'

    fakematch = re.match('.*', line)

    trigger = Trigger(config, pretrigger, fakematch)
    assert trigger.sender == '#Sopel'
    assert trigger.raw == line
    assert trigger.is_privmsg is False
    assert trigger.hostmask == 'Foo!foo@example.com'
    assert trigger.user == 'foo'
    assert trigger.nick == Identifier('Foo')
    assert trigger.host == 'example.com'
    assert trigger.event == 'JOIN'
    assert trigger.match == fakematch
    assert trigger.group == fakematch.group
    assert trigger.groups == fakematch.groups
    assert trigger.args == ['#Sopel', 'bar', 'Real Name']
    assert trigger.account == 'bar'
    assert trigger.tags == {'account': 'bar'}
    assert trigger.owner is True
    assert trigger.admin is True


def test_ircv3_intents_trigger(nick):
    line = '@intent=ACTION :Foo!foo@example.com PRIVMSG #Sopel :Hello, world'
    pretrigger = PreTrigger(nick, line)

    config = MockConfig()
    config.core.owner = 'Foo'
    config.core.admins = ['Bar']

    fakematch = re.match('.*', line)

    trigger = Trigger(config, pretrigger, fakematch)
    assert trigger.sender == '#Sopel'
    assert trigger.raw == line
    assert trigger.is_privmsg is False
    assert trigger.hostmask == 'Foo!foo@example.com'
    assert trigger.user == 'foo'
    assert trigger.nick == Identifier('Foo')
    assert trigger.host == 'example.com'
    assert trigger.event == 'PRIVMSG'
    assert trigger.match == fakematch
    assert trigger.group == fakematch.group
    assert trigger.groups == fakematch.groups
    assert trigger.groupdict == fakematch.groupdict
    assert trigger.args == ['#Sopel', 'Hello, world']
    assert trigger.tags == {'intent': 'ACTION'}
    assert trigger.admin is True
    assert trigger.owner is True


def test_ircv3_account_tag_trigger(nick):
    line = '@account=Foo :Nick_Is_Not_Foo!foo@example.com PRIVMSG #Sopel :Hello, world'
    pretrigger = PreTrigger(nick, line)

    config = MockConfig()
    config.core.owner_account = 'Foo'
    config.core.admins = ['Bar']

    fakematch = re.match('.*', line)

    trigger = Trigger(config, pretrigger, fakematch)
    assert trigger.admin is True
    assert trigger.owner is True


def test_ircv3_server_time_trigger(nick):
    line = '@time=2016-01-09T03:15:42.000Z :Foo!foo@example.com PRIVMSG #Sopel :Hello, world'
    pretrigger = PreTrigger(nick, line)

    config = MockConfig()
    config.core.owner = 'Foo'
    config.core.admins = ['Bar']

    fakematch = re.match('.*', line)

    trigger = Trigger(config, pretrigger, fakematch)
    assert trigger.time == datetime.datetime(2016, 1, 9, 3, 15, 42, 0)

    # Spec-breaking string
    line = '@time=2016-01-09T04:20 :Foo!foo@example.com PRIVMSG #Sopel :Hello, world'
    pretrigger = PreTrigger(nick, line)
    assert pretrigger.time is not None
