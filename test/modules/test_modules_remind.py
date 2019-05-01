# coding=utf-8
"""Tests for Sopel's ``remind`` plugin"""
from __future__ import unicode_literals, absolute_import, print_function, division

from collections import namedtuple
import os

import pytest

from sopel import test_tools
from sopel.modules import remind


@pytest.fixture
def sopel():
    bot = test_tools.MockSopel('Sopel')
    bot.config.core.owner = 'Admin'
    bot.config.core.host = 'chat.freenode.net'
    return bot


TimeReminder = namedtuple(
    'TimeReminder', ['hour', 'minute', 'second', 'tz', 'message'])

VALID_MATCH_LINES = (
    ('1:20 message', TimeReminder('1', '20', None, None, 'message')),
    ('01:20 message', TimeReminder('01', '20', None, None, 'message')),
    ('13:37 message', TimeReminder('13', '37', None, None, 'message')),
    ('13:37:00 message', TimeReminder('13', '37', '00', None, 'message')),
    # Make sure numbers are not confused with anything else
    ('13:37:00 10 message',
     TimeReminder('13', '37', '00', None, '10 message')),
    # Weird stuff
    ('13:37:00 message\tanother one',
     TimeReminder('13', '37', '00', None, 'message\tanother one')),
    ('13:37:00 ( •ᴗ•)ψ( •ᴗ•)ψ( •ᴗ•)ψ( •ᴗ•)ψ( •ᴗ•)ψ'
     '( •ᴗ ^B^]^_ITS CARDBACK TIME!!!!!!!!!!!!!!!!!!!!!!!^B^]^_'
     '( •ᴗ•)ψ( •ᴗ•)ψ( •ᴗ•)ψ( •ᴗ•)ψ( •ᴗ•)ψ( •ᴗ•)ψ',
     TimeReminder('13', '37', '00', None,
        '( •ᴗ•)ψ( •ᴗ•)ψ( •ᴗ•)ψ( •ᴗ•)ψ( •ᴗ•)ψ'
        '( •ᴗ ^B^]^_ITS CARDBACK TIME!!!!!!!!!!!!!!!!!!!!!!!^B^]^_'
        '( •ᴗ•)ψ( •ᴗ•)ψ( •ᴗ•)ψ( •ᴗ•)ψ( •ᴗ•)ψ( •ᴗ•)ψ')),
    # Timezone
    ('13:37Europe/Paris message',
     TimeReminder('13', '37', None, 'Europe/Paris', 'message')),
    ('13:37:00Europe/Paris message',
     TimeReminder('13', '37', '00', 'Europe/Paris', 'message')),
    # these should not pass, but they do at the moment
    ('13:7 message', TimeReminder('13', '7', None, None, 'message')),
    ('0000:20 message', TimeReminder('0000', '20', None, None, 'message')),
    ('13:37:71 message', TimeReminder('13', '37', '71', None, 'message')),
)


@pytest.mark.parametrize('line, expected', VALID_MATCH_LINES)
def test_at_regex_matches(line, expected):
    result = remind.REGEX_AT.match(line)
    assert result

    reminder = TimeReminder(*result.groups())
    assert reminder == expected


INVALID_MATCH_LINES = (
    '',
    '1 message',
    '01 message',
    '13h message',
    '13h37 message',
    '1337 message',
    ':20 message',
    # no message
    '13:37',
    '13:37Europe/Paris',
    '13:37:00Europe/Paris',
)


@pytest.mark.parametrize('line', INVALID_MATCH_LINES)
def test_at_regex_dont_match(line):
    result = remind.REGEX_AT.match(line)
    assert result is None, (
        'Result found for invalid line "%s": %s' % (line, result.groups()))


def test_get_filename(sopel):
    filename = remind.get_filename(sopel)
    assert filename == os.path.join(
        sopel.config.core.homedir,
        'Sopel-chat.freenode.net.reminders.db')


def test_load_database_empty(tmpdir):
    tmpfile = tmpdir.join('remind.db')
    assert remind.load_database(tmpfile.strpath) == {}


def test_load_database(tmpdir):
    tmpfile = tmpdir.join('remind.db')
    tmpfile.write(
        '523549810.0\t#sopel\tAdmin\tmessage\n'
        '839169010.0\t#sopel\tAdmin\tanother message\n')
    result = remind.load_database(tmpfile.strpath)
    assert len(result.keys()) == 2

    # first timestamp
    assert 523549810 in result
    assert len(result[523549810]) == 1
    assert ('#sopel', 'Admin', 'message') in result[523549810]

    # second timestamp
    assert 839169010 in result
    assert len(result[839169010]) == 1
    assert ('#sopel', 'Admin', 'another message') in result[839169010]


def test_load_database_tabs(tmpdir):
    tmpfile = tmpdir.join('remind.db')
    tmpfile.write(
        '523549810.0\t#sopel\tAdmin\tmessage\n'
        '839169010.0\t#sopel\tAdmin\tmessage\textra\n')
    result = remind.load_database(tmpfile.strpath)
    assert len(result.keys()) == 2
    # first timestamp
    assert 523549810 in result
    assert len(result[523549810]) == 1
    assert ('#sopel', 'Admin', 'message') in result[523549810]

    # second timestamp
    assert 839169010 in result
    assert len(result[839169010]) == 1
    assert ('#sopel', 'Admin', 'message\textra') in result[839169010]


def test_load_multiple_reminders_same_timestamp(tmpdir):
    tmpfile = tmpdir.join('remind.db')
    tmpfile.write(
        '523549810.0\t#sopel\tAdmin\tmessage\n'
        '523549810.0\t#sopel\tAdmin\tanother message\n')
    result = remind.load_database(tmpfile.strpath)
    assert len(result.keys()) == 1, (
        'There should be only one key: 523549810; found %s'
        % (', '.join(result.keys())))
    assert 523549810 in result
    assert len(result[523549810]) == 2
    assert ('#sopel', 'Admin', 'message') in result[523549810]
    assert ('#sopel', 'Admin', 'another message') in result[523549810]


def test_load_multiple_reminders_same_timestamp_microseconds_ignored(tmpdir):
    tmpfile = tmpdir.join('remind.db')
    tmpfile.write(
        '523549810.210\t#sopel\tAdmin\tmessage\n'
        '523549810.420\t#sopel\tAdmin\tanother message\n')
    result = remind.load_database(tmpfile.strpath)
    assert len(result.keys()) == 1, (
        'There should be only one key: 523549810; found %s'
        % (', '.join(result.keys())))
    assert 523549810 in result
    assert len(result[523549810]) == 2
    assert ('#sopel', 'Admin', 'message') in result[523549810]
    assert ('#sopel', 'Admin', 'another message') in result[523549810]


def test_dump_database(tmpdir):
    tmpfile = tmpdir.join('remind.db')
    test_data = {
        523549810: [
            ('#sopel', 'Admin', 'message'),
            ('#sopel', 'Admin', 'another message'),
        ],
        839169010: [
            ('#sopel', 'Admin', 'the last message'),
        ],
        555169010: [
            ('#sopel', 'Admin', 'oops\tanother\tmessage'),
        ],
    }
    remind.dump_database(tmpfile.strpath, test_data)

    content = tmpfile.read()
    assert content.endswith('\n')
    lines = content.strip().split('\n')
    assert len(lines) == 4, 'There should be 4 lines, found %d' % len(lines)
    assert '523549810\t#sopel\tAdmin\tmessage' in lines
    assert '523549810\t#sopel\tAdmin\tanother message' in lines
    assert '839169010\t#sopel\tAdmin\tthe last message' in lines
    assert '555169010\t#sopel\tAdmin\toops\tanother\tmessage' in lines
