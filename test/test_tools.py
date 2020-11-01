# coding=utf-8
"""Tests sopel.tools"""
from __future__ import absolute_import, division, print_function, unicode_literals

import re

import pytest

from sopel import tools


TMP_CONFIG = """
[core]
owner = testnick
nick = TestBot
enable = coretasks
"""


@pytest.fixture
def nick():
    return 'Sopel'


@pytest.fixture
def alias_nicks():
    return ['Soap', 'Pie']


@pytest.fixture
def prefix():
    return '.'


@pytest.fixture
def prefix_regex():
    re.escape(prefix())


@pytest.fixture
def command():
    return 'testcmd'


@pytest.fixture
def groups(command):
    return {
        3: "three",
        4: "four",
        5: "five",
        6: "six",
    }


@pytest.fixture
def command_line(prefix, command, groups):
    return "{}{} {}".format(prefix, command, ' '.join(groups.values()))


@pytest.fixture
def nickname_command_line(nick, command, groups):
    return "{}: {} {}".format(nick, command, ' '.join(groups.values()))


@pytest.fixture
def action_command_line(command, groups):
    return "{} {}".format(command, ' '.join(groups.values()))


def test_command_groups(prefix, command, groups, command_line):
    regex = tools.get_command_regexp(prefix, command)
    match = re.match(regex, command_line)
    assert match.group(0) == command_line
    assert match.group(1) == command
    assert match.group(2) == ' '.join(groups.values())
    assert match.group(3) == groups[3]
    assert match.group(4) == groups[4]
    assert match.group(5) == groups[5]
    assert match.group(6) == groups[6]


def test_nickname_command_groups(command, nick, groups, nickname_command_line):
    regex = tools.get_nickname_command_regexp(nick, command, [])
    match = re.match(regex, nickname_command_line)
    assert match.group(0) == nickname_command_line
    assert match.group(1) == command
    assert match.group(2) == ' '.join(groups.values())
    assert match.group(3) == groups[3]
    assert match.group(4) == groups[4]
    assert match.group(5) == groups[5]
    assert match.group(6) == groups[6]


def test_nickname_command_aliased(command, nick, alias_nicks, groups, nickname_command_line):
    aliased_command_line = nickname_command_line.replace(nick, alias_nicks[0])
    regex = tools.get_nickname_command_regexp(nick, command, alias_nicks)
    match = re.match(regex, aliased_command_line)
    assert match.group(0) == aliased_command_line
    assert match.group(1) == command
    assert match.group(2) == ' '.join(groups.values())
    assert match.group(3) == groups[3]
    assert match.group(4) == groups[4]
    assert match.group(5) == groups[5]
    assert match.group(6) == groups[6]


def test_action_command_groups(command, groups, action_command_line):
    regex = tools.get_action_command_regexp(command)
    match = re.match(regex, action_command_line)
    assert match.group(0) == action_command_line
    assert match.group(1) == command
    assert match.group(2) == ' '.join(groups.values())
    assert match.group(3) == groups[3]
    assert match.group(4) == groups[4]
    assert match.group(5) == groups[5]
    assert match.group(6) == groups[6]


def test_get_sendable_message_default():
    initial = 'aaaa'
    text, excess = tools.get_sendable_message(initial)

    assert text == initial
    assert excess == ''


def test_get_sendable_message_limit():
    initial = 'a' * 400
    text, excess = tools.get_sendable_message(initial)

    assert text == initial
    assert excess == ''


def test_get_sendable_message_excess():
    initial = 'a' * 401
    text, excess = tools.get_sendable_message(initial)

    assert text == 'a' * 400
    assert excess == 'a'


def test_get_sendable_message_excess_space():
    # aaa...aaa bbb...bbb
    initial = ' '.join(['a' * 200, 'b' * 200])
    text, excess = tools.get_sendable_message(initial)

    assert text == 'a' * 200
    assert excess == 'b' * 200


def test_get_sendable_message_excess_space_limit():
    # aaa...aaa bbb...bbb
    initial = ' '.join(['a' * 400, 'b' * 200])
    text, excess = tools.get_sendable_message(initial)

    assert text == 'a' * 400
    assert excess == 'b' * 200


def test_get_sendable_message_excess_bigger():
    # aaa...aaa bbb...bbb
    initial = ' '.join(['a' * 401, 'b' * 1000])
    text, excess = tools.get_sendable_message(initial)

    assert text == 'a' * 400
    assert excess == 'a ' + 'b' * 1000


def test_get_sendable_message_optional():
    text, excess = tools.get_sendable_message('aaaa', 3)
    assert text == 'aaa'
    assert excess == 'a'

    text, excess = tools.get_sendable_message('aaa bbb', 3)
    assert text == 'aaa'
    assert excess == 'bbb'

    text, excess = tools.get_sendable_message('aa bb cc', 3)
    assert text == 'aa'
    assert excess == 'bb cc'


def test_get_sendable_message_two_bytes():
    text, excess = tools.get_sendable_message('αααα', 4)
    assert text == 'αα'
    assert excess == 'αα'

    text, excess = tools.get_sendable_message('αααα', 5)
    assert text == 'αα'
    assert excess == 'αα'

    text, excess = tools.get_sendable_message('α ααα', 4)
    assert text == 'α'
    assert excess == 'ααα'

    text, excess = tools.get_sendable_message('αα αα', 4)
    assert text == 'αα'
    assert excess == 'αα'

    text, excess = tools.get_sendable_message('ααα α', 4)
    assert text == 'αα'
    assert excess == 'α α'


def test_chain_loaders(configfactory):
    re_numeric = re.compile(r'\d+')
    re_text = re.compile(r'\w+')
    settings = configfactory('test.cfg', TMP_CONFIG)

    def loader_numeric(settings):
        return [re_numeric]

    def loader_text(settings):
        return [re_text]

    loader = tools.chain_loaders(loader_numeric, loader_text)

    assert callable(loader)
    results = loader(settings)

    assert results == [re_numeric, re_text]


def test_sopel_identifier_memory_str():
    user = tools.Identifier('Exirel')
    memory = tools.SopelIdentifierMemory()
    test_value = 'king'

    memory['Exirel'] = test_value
    assert user in memory
    assert 'Exirel' in memory
    assert 'exirel' in memory
    assert 'exi' not in memory
    assert '#channel' not in memory

    assert memory[user] == test_value
    assert memory['Exirel'] == test_value
    assert memory['exirel'] == test_value


def test_sopel_identifier_memory_id():
    user = tools.Identifier('Exirel')
    memory = tools.SopelIdentifierMemory()
    test_value = 'king'

    memory[user] = test_value
    assert user in memory
    assert 'Exirel' in memory
    assert 'exirel' in memory
    assert 'exi' not in memory
    assert '#channel' not in memory

    assert memory[user] == test_value
    assert memory['Exirel'] == test_value
    assert memory['exirel'] == test_value


def test_sopel_identifier_memory_channel_str():
    channel = tools.Identifier('#adminchannel')
    memory = tools.SopelIdentifierMemory()
    test_value = 'perfect'

    memory['#adminchannel'] = test_value
    assert channel in memory
    assert '#adminchannel' in memory
    assert '#AdminChannel' in memory
    assert 'adminchannel' not in memory
    assert 'Exirel' not in memory

    assert memory[channel] == test_value
    assert memory['#adminchannel'] == test_value
    assert memory['#AdminChannel'] == test_value
