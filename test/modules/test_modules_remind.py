"""Tests for Sopel's ``remind`` plugin"""
from __future__ import generator_stop

from datetime import datetime
import os

import pytest
import pytz

from sopel.modules import remind


TMP_CONFIG = """
[core]
owner = Admin
nick = Sopel
enable =
    coretasks
    remind
host = chat.freenode.net
"""


WEIRD_MESSAGE = (
    '( •ᴗ•)ψ( •ᴗ•)ψ( •ᴗ•)ψ( •ᴗ•)ψ( •ᴗ•)ψ'
    '( •ᴗ ^B^]^_ITS CARDBACK TIME!!!!!!!!!!!!!!!!!!!!!!!^B^]^_'
    '( •ᴗ•)ψ( •ᴗ•)ψ( •ᴗ•)ψ( •ᴗ•)ψ( •ᴗ•)ψ( •ᴗ•)ψ'
)

VALID_MATCH_LINES = (
    ('1:20 message',
     remind.TimeReminder(1, 20, 0, 'UTC', None, None, None, 'message')),
    ('01:20 message',
     remind.TimeReminder(1, 20, 0, 'UTC', None, None, None, 'message')),
    ('13:37 message',
     remind.TimeReminder(13, 37, 0, 'UTC', None, None, None, 'message')),
    ('13:37:00 message',
     remind.TimeReminder(13, 37, 0, 'UTC', None, None, None, 'message')),
    # Make sure numbers are not confused with anything else
    ('13:37:00 10 message',
     remind.TimeReminder(13, 37, 0, 'UTC', None, None, None, '10 message')),
    # Date dd-mm-YYYY (with different separators)
    ('13:37:00 03-05-2019 message',
     remind.TimeReminder(13, 37, 0, 'UTC', '03', '05', '2019', 'message')),
    ('13:37:00 03/05/2019 message',
     remind.TimeReminder(13, 37, 0, 'UTC', '03', '05', '2019', 'message')),
    ('13:37:00 03.05.2019 message',
     remind.TimeReminder(13, 37, 0, 'UTC', '03', '05', '2019', 'message')),
    # If separator is wrong, then it won't be parsed as a date
    (
        '13:37:00 03,05,2019 message',
        remind.TimeReminder(
            13, 37, 0, 'UTC', None, None, None, '03,05,2019 message'
        ),
    ),
    (
        '13:37:00 03/05-2019 message',
        remind.TimeReminder(
            13, 37, 0, 'UTC', None, None, None, '03/05-2019 message'
        ),
    ),
    # Weird stuff
    (
        '13:37:00 message\tanother one',
        remind.TimeReminder(
            13, 37, 0, 'UTC', None, None, None, 'message\tanother one'
        ),
    ),
    ('13:37:00 %s' % WEIRD_MESSAGE,
     remind.TimeReminder(13, 37, 0, 'UTC', None, None, None, WEIRD_MESSAGE)),
    # Timezone
    (
        '13:37Europe/Paris message',
        remind.TimeReminder(
            13, 37, 0, 'Europe/Paris', None, None, None, 'message'
        ),
    ),
    (
        '13:37:00Europe/Paris message',
        remind.TimeReminder(
            13, 37, 0, 'Europe/Paris', None, None, None, 'message'
        ),
    ),
    # These should not pass but we are very tolerant a the moment
    ('1:7 message',
     remind.TimeReminder(1, 7, 0, 'UTC', None, None, None, 'message')),
    ('13:7 message',
     remind.TimeReminder(13, 7, 0, 'UTC', None, None, None, 'message')),
    ('0000:20 message',
     remind.TimeReminder(0, 20, 0, 'UTC', None, None, None, 'message')),
    # These are weird but okay-ish at the moment
    # Since the "date" part is optional, the regex thinks it's the message
    ('13:37 2019-10-09',
     remind.TimeReminder(13, 37, 0, 'UTC', None, None, None, '2019-10-09')),
    ('13:37Europe/Paris 2019-10-09',
     remind.TimeReminder(
         13, 37, 0, 'Europe/Paris', None, None, None, '2019-10-09')),
    ('13:37:00Europe/Paris 2019-10-09',
     remind.TimeReminder(
         13, 37, 0, 'Europe/Paris', None, None, None, '2019-10-09')),
)


@pytest.mark.parametrize('line, expected', VALID_MATCH_LINES)
def test_at_parse_regex_match(line, expected):
    result = remind.REGEX_AT.match(line)
    assert result

    reminder = remind.parse_regex_match(result, 'UTC')
    assert reminder == expected
    assert reminder.get_duration() >= 0


VALID_MATCH_INVALID_DATE_LINES = (
    # invalid seconds
    ('13:37:71 message',
     remind.TimeReminder(13, 37, 71, 'UTC', None, None, None, 'message')),
    ('13:37:60 message',
     remind.TimeReminder(13, 37, 60, 'UTC', None, None, None, 'message')),
    # invalid minutes
    ('13:71:59 message',
     remind.TimeReminder(13, 71, 59, 'UTC', None, None, None, 'message')),
    ('13:60:59 message',
     remind.TimeReminder(13, 60, 59, 'UTC', None, None, None, 'message')),
    # invalid hours
    ('24:30:15 message',
     remind.TimeReminder(24, 30, 15, 'UTC', None, None, None, 'message')),
    ('71:30:15 message',
     remind.TimeReminder(71, 30, 15, 'UTC', None, None, None, 'message')),
    # invalid date
    ('13:37:25 2019-12-32 message',
     remind.TimeReminder(13, 37, 25, 'UTC', '2019', '12', '32', 'message')),
    ('13:37:25 2019-11-31 message',
     remind.TimeReminder(13, 37, 25, 'UTC', '2019', '11', '31', 'message')),
    ('13:37:25 2019-13-01 message',
     remind.TimeReminder(13, 37, 25, 'UTC', '2019', '13', '01', 'message')),
    # invalid date: using 00 or 0000
    ('13:37:25 0000-12-32 message',
     remind.TimeReminder(13, 37, 25, 'UTC', '0000', '12', '32', 'message')),
    ('13:37:25 2019-00-32 message',
     remind.TimeReminder(13, 37, 25, 'UTC', '2019', '00', '32', 'message')),
    ('13:37:25 2019-12-00 message',
     remind.TimeReminder(13, 37, 25, 'UTC', '2019', '12', '00', 'message')),
)


@pytest.mark.parametrize('line, expected', VALID_MATCH_INVALID_DATE_LINES)
def test_at_parse_regex_match_invalid_duration(line, expected):
    result = remind.REGEX_AT.match(line)
    assert result

    reminder = remind.parse_regex_match(result, 'UTC')
    assert reminder == expected

    with pytest.raises(ValueError):
        reminder.get_duration()


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


SECONDS = 1
ONE_MINUTE = MINUTES = 60 * SECONDS
TWO_MINUTES = 2 * MINUTES
HOURS = 60 * MINUTES
ONE_DAY = DAYS = 24 * HOURS


TEST_DATE_123 = (
    # reminder is the same day
    (None, None, None, TWO_MINUTES, ONE_DAY - ONE_MINUTE),
    # reminder is the same day, with YYYY-mm-dd
    ('2019', '05', '04', TWO_MINUTES, ONE_DAY - ONE_MINUTE),
    ('2019', '5', '4', TWO_MINUTES, ONE_DAY - ONE_MINUTE),
    # reminder is the same day, with dd-mm-YYYY or dd-mm-YY
    ('04', '05', '2019', TWO_MINUTES, ONE_DAY - ONE_MINUTE),
    ('4', '5', '2019', TWO_MINUTES, ONE_DAY - ONE_MINUTE),
    ('04', '05', '19', TWO_MINUTES, ONE_DAY - ONE_MINUTE),
    ('4', '5', '19', TWO_MINUTES, ONE_DAY - ONE_MINUTE),
    # reminder is the same day, with YYYY-mm or mm-YYYY
    ('2019', '05', None, TWO_MINUTES, ONE_DAY - ONE_MINUTE),
    ('2019', '5', None, TWO_MINUTES, ONE_DAY - ONE_MINUTE),
    ('05', '2019', None, TWO_MINUTES, ONE_DAY - ONE_MINUTE),
    ('5', '2019', None, TWO_MINUTES, ONE_DAY - ONE_MINUTE),
    # reminder is the same day, with dd/mm (or dd-mm for the fool)
    ('04', '05', None, TWO_MINUTES, ONE_DAY - ONE_MINUTE),
    ('04', '5', None, TWO_MINUTES, ONE_DAY - ONE_MINUTE),
    ('4', '05', None, TWO_MINUTES, ONE_DAY - ONE_MINUTE),
    ('4', '5', None, TWO_MINUTES, ONE_DAY - ONE_MINUTE),
    # reminder is yesterday, with YYYY-mm-dd
    ('2019', '05', '03', TWO_MINUTES, ONE_DAY - ONE_MINUTE),
    ('2019', '5', '3', TWO_MINUTES, ONE_DAY - ONE_MINUTE),
    # reminder is yesterday, with dd-mm-YYYY or dd-mm-YY
    ('03', '05', '2019', TWO_MINUTES, ONE_DAY - ONE_MINUTE),
    ('3', '5', '2019', TWO_MINUTES, ONE_DAY - ONE_MINUTE),
    ('03', '05', '19', TWO_MINUTES, ONE_DAY - ONE_MINUTE),
    ('3', '5', '19', TWO_MINUTES, ONE_DAY - ONE_MINUTE),
    # reminder is tomorrow
    ('2019', '05', '05',
     # compared to 2019-05-04 at 13:35:00,
     # may 5th at 13:37:00 is tomorrow plus 2 minute
     ONE_DAY + TWO_MINUTES,
     # compared to 2019-05-04 at 13:38:00,
     # may 5th at 13:37:00 is tomorrow, 1 minute sooner than today
     ONE_DAY - ONE_MINUTE),
    ('2019', '5', '5', ONE_DAY + TWO_MINUTES, ONE_DAY - ONE_MINUTE),
    ('05', '05', '2019', ONE_DAY + TWO_MINUTES, ONE_DAY - ONE_MINUTE),
    ('5', '5', '2019', ONE_DAY + TWO_MINUTES, ONE_DAY - ONE_MINUTE),
)


@pytest.mark.parametrize('tz_name', ['UTC', 'Europe/Paris', 'America/Chicago'])
@pytest.mark.parametrize('date1, date2, date3, expected1, expected2', TEST_DATE_123)
def test_timereminder_get_duration(tz_name,
                                   date1, date2, date3,
                                   expected1,
                                   expected2):
    """Assert result of ``get_duration`` from reminder

    :param str tz_name: the timezone used to generate aware today & reminder
    :param str date1: numeric value given for date1 of reminder
    :param str date2: numeric value given for date2 of reminder
    :param str date3: numeric value given for date3 of reminder
    :param expected1: expected duration, in seconds, for reminder compared to
                      ``2019-05-04 13:35:00`` (same timezone)
    :param expected2: duration, in seconds, for reminder compared to
                      ``2019-05-04 13:38:00`` (same timezone)

    The reminder will be created at a fixed time point of ``13:37:00`` local
    to the given timezone (from ``tz_name``), and the date will be provided by
    the parameters ``date1``, ``date2``, and ``date3``.
    """
    reminder = remind.TimeReminder(
        13, 37, 0, tz_name, date1, date2, date3, message='Hello')

    timezone = pytz.timezone(tz_name)
    test_today = timezone.localize(datetime(2019, 5, 4, 13, 35, 0))
    assert reminder.get_duration(test_today) == expected1

    test_today = timezone.localize(datetime(2019, 5, 4, 13, 38, 0))
    assert reminder.get_duration(test_today) == expected2


def test_timereminder_get_duration_different_timezone():
    reminder = remind.TimeReminder(
        13, 37, 0, 'Europe/Paris', None, None, None, message='Hello')

    test_today = pytz.utc.localize(datetime(2019, 5, 4, 11, 35, 0))
    assert reminder.get_duration(test_today) == 120

    # 1 minute in the past is timedelta(-1, 86340)
    # ie. yesterday + 86340 seconds
    # ie. today one minute ago
    test_today = pytz.utc.localize(datetime(2019, 5, 4, 11, 38, 0))
    assert reminder.get_duration(test_today) == 86340


TEST_INVALID_DATE_123 = (
    # empty value
    ('0000', '00', '00'),
    ('00', '00', '0000'),
    ('00', '00', '00'),
    # year full but day and/or month empty
    ('2019', '00', '00'),
    ('2019', '00', '05'),
    ('2019', '03', '00'),
    ('00', '00', '2019'),
    ('00', '05', '2019'),
    ('03', '00', '2019'),
    # no year provided but day and/or month empty
    ('00', '00', None),
    ('03', '00', None),
    ('00', '03', None),
    # month above 12
    ('01', '13', None),
    ('01', '13', '2019'),
    ('01', '13', '19'),
    ('2019', '13', '01'),
    # day above 31
    ('32', '12', None),
    ('32', '12', '2019'),
    ('32', '12', '19'),
    ('2019', '12', '32'),
)


@pytest.mark.parametrize('date1, date2, date3', TEST_INVALID_DATE_123)
def test_timereminder_get_duration_error(date1, date2, date3):
    test_today = pytz.utc.localize(datetime(2019, 5, 4, 11, 35, 0))
    reminder = remind.TimeReminder(
        13, 37, 0, 'Europe/Paris', date1, date2, date3, message='Hello')

    with pytest.raises(ValueError):
        reminder.get_duration(test_today)


def test_get_filename(configfactory, botfactory):
    tmpconfig = configfactory('default.ini', TMP_CONFIG)
    mockbot = botfactory(tmpconfig)

    filename = remind.get_filename(mockbot)
    assert filename == os.path.join(
        mockbot.config.core.homedir,
        'default.reminders.db')


def test_load_database_empty(tmpdir):
    tmpfile = tmpdir.join('remind.db')
    assert remind.load_database(tmpfile.strpath) == {}


def test_load_database(tmpdir):
    tmpfile = tmpdir.join('remind.db')
    tmpfile.write(
        '523549810.0\t#sopel\tAdmin\tmessage\n'
        '839169010.0\t#sopel\tAdmin\tanother message\n')
    result = remind.load_database(tmpfile.strpath)
    assert len(result.keys()) == 2, (
        'There should be only two keys: 523549810, 839169010; found %s'
        % (', '.join(result.keys())))

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
    assert len(result.keys()) == 2, (
        'There should be only two keys: 523549810, 839169010; found %s'
        % (', '.join(result.keys())))
    # first timestamp
    assert 523549810 in result
    assert len(result[523549810]) == 1
    assert ('#sopel', 'Admin', 'message') in result[523549810]

    # second timestamp
    assert 839169010 in result
    assert len(result[839169010]) == 1
    assert ('#sopel', 'Admin', 'message\textra') in result[839169010]


def test_load_database_weirdo(tmpdir):
    tmpfile = tmpdir.join('remind.db')
    weird_message = (
        '( •ᴗ•)ψ( •ᴗ•)ψ( •ᴗ•)ψ( •ᴗ•)ψ( •ᴗ•)ψ'
        '( •ᴗ ^B^]^_ITS CARDBACK TIME!!!!!!!!!!!!!!!!!!!!!!!^B^]^_'
        '( •ᴗ•)ψ( •ᴗ•)ψ( •ᴗ•)ψ( •ᴗ•)ψ( •ᴗ•)ψ( •ᴗ•)ψ')
    tmpfile.write_text(
        '523549810.0\t#sopel\tAdmin\t%s\n' % weird_message,
        encoding='utf-8')

    result = remind.load_database(tmpfile.strpath)
    assert len(result.keys()) == 1, (
        'There should be only one key: 523549810; found %s'
        % (', '.join(result.keys())))
    # first timestamp
    assert 523549810 in result
    assert len(result[523549810]) == 1
    assert ('#sopel', 'Admin', weird_message) in result[523549810]


def test_load_database_irc_formatting(tmpdir):
    tmpfile = tmpdir.join('remind.db')
    formatted_message = (
        'This message has \x0301,04colored text\x03, \x0400ff00hex-colored '
        'text\x04, \x02bold\x02, \x1ditalics\x1d, \x1funderline\x1f, '
        '\x11monospace\x11, \x16reverse\x16, \x1estrikethrough or\x0f '
        'strikethrough and normal text.')
    tmpfile.write_text(
        '523549810.0\t#sopel\tAdmin\t%s\n' % formatted_message,
        encoding='utf-8')

    result = remind.load_database(tmpfile.strpath)
    assert len(result.keys()) == 1, (
        'There should be only one key: 523549810; found %s'
        % (', '.join(result.keys())))
    # first timestamp
    assert 523549810 in result
    assert len(result[523549810]) == 1
    assert ('#sopel', 'Admin', formatted_message) in result[523549810]


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
    weird_message = (
        '( •ᴗ•)ψ( •ᴗ•)ψ( •ᴗ•)ψ( •ᴗ•)ψ( •ᴗ•)ψ'
        '( •ᴗ ^B^]^_ITS CARDBACK TIME!!!!!!!!!!!!!!!!!!!!!!!^B^]^_'
        '( •ᴗ•)ψ( •ᴗ•)ψ( •ᴗ•)ψ( •ᴗ•)ψ( •ᴗ•)ψ( •ᴗ•)ψ')
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
        666169010: [
            ('#sopel', 'Admin', weird_message),
        ]
    }
    remind.dump_database(tmpfile.strpath, test_data)

    content = tmpfile.read_text(encoding='utf-8')
    assert content.endswith('\n')
    lines = content.strip().split('\n')
    assert len(lines) == 5, 'There should be 5 lines, found %d' % len(lines)
    assert '523549810\t#sopel\tAdmin\tmessage' in lines
    assert '523549810\t#sopel\tAdmin\tanother message' in lines
    assert '839169010\t#sopel\tAdmin\tthe last message' in lines
    assert '555169010\t#sopel\tAdmin\toops\tanother\tmessage' in lines

    weird_line = '666169010\t#sopel\tAdmin\t%s' % weird_message
    assert weird_line in lines
