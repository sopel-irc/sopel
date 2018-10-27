# coding=utf-8
"""Tests for command handling"""
from __future__ import unicode_literals, absolute_import, print_function, division

import pytest
import re

from sopel.tools import get_command_regexp, get_nickname_command_regexp


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
    regex = get_command_regexp(prefix, command)
    match = re.match(regex, command_line)
    assert match.group(0) == command_line
    assert match.group(1) == command
    assert match.group(2) == ' '.join(groups.values())
    assert match.group(3) == groups[3]
    assert match.group(4) == groups[4]
    assert match.group(5) == groups[5]
    assert match.group(6) == groups[6]


def test_nickname_command_groups(command, nick, groups, nickname_command_line):
    regex = get_nickname_command_regexp(nick, command, [])
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
    regex = get_nickname_command_regexp(nick, command, alias_nicks)
    match = re.match(regex, aliased_command_line)
    assert match.group(0) == aliased_command_line
    assert match.group(1) == command
    assert match.group(2) == ' '.join(groups.values())
    assert match.group(3) == groups[3]
    assert match.group(4) == groups[4]
    assert match.group(5) == groups[5]
    assert match.group(6) == groups[6]
