# coding=utf-8
"""Tests sopel.tools"""
from __future__ import absolute_import, division, print_function, unicode_literals

from datetime import timedelta
import re

import pytest

from sopel import tools
from sopel.tools.time import seconds_to_human


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


def test_time_timedelta_formatter():
    payload = 10000
    assert seconds_to_human(payload) == '2 hours, 46 minutes ago'

    payload = -2938124
    assert seconds_to_human(payload) == 'in 1 month, 3 days'

    payload = timedelta(hours=4)
    assert seconds_to_human(payload) == '4 hours ago'

    payload = timedelta(hours=-4)
    assert seconds_to_human(payload) == 'in 4 hours'
