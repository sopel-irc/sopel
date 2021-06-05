"""Tools for getting and displaying the time."""
from __future__ import generator_stop

import datetime

import pytest

from sopel.tools import time


def test_validate_timezone():
    assert time.validate_timezone('Europe/Paris') == 'Europe/Paris'
    assert time.validate_timezone('America/New York') == 'America/New_York'
    assert time.validate_timezone('Paris, Europe') == 'Europe/Paris'
    assert time.validate_timezone('New York, America') == 'America/New_York'
    assert time.validate_timezone('Israel') == 'Israel'


def test_validate_timezone_none():
    assert time.validate_timezone(None) is None


def test_validate_timezone_invalid():
    with pytest.raises(ValueError):
        time.validate_timezone('Invalid/Timezone')

    with pytest.raises(ValueError):
        time.validate_timezone('Europe Paris')

    with pytest.raises(ValueError):
        time.validate_timezone('Paris/Europe')

    with pytest.raises(ValueError):
        time.validate_timezone('Paris,Europe')


def test_validate_format():
    assert time.validate_format('%Y') == '%Y'
    assert time.validate_format('%Y%m%d') == '%Y%m%d'
    assert time.validate_format('%b %d %Y %H:%M:%S') == '%b %d %Y %H:%M:%S'
    assert time.validate_format('some text') == 'some text'


def test_validate_format_none():
    with pytest.raises(ValueError):
        time.validate_format(None)


def test_seconds_to_human():
    payload = 0
    assert time.seconds_to_human(payload) == '0 seconds ago'

    payload = 10000
    assert time.seconds_to_human(payload) == '2 hours, 46 minutes ago'

    payload = -2938124
    assert time.seconds_to_human(payload) == 'in 1 month, 3 days'


def test_seconds_to_human_timedelta():
    payload = datetime.timedelta(hours=4)
    assert time.seconds_to_human(payload) == '4 hours ago'

    payload = datetime.timedelta(hours=-4)
    assert time.seconds_to_human(payload) == 'in 4 hours'

    payload = datetime.timedelta(days=4)
    assert time.seconds_to_human(payload) == '4 days ago'

    payload = datetime.timedelta(days=4, hours=26)
    assert time.seconds_to_human(payload) == '5 days, 2 hours ago'

    payload = datetime.timedelta(days=4, hours=2, seconds=123)
    assert time.seconds_to_human(payload) == '4 days, 2 hours ago'

    payload = datetime.timedelta(days=4, seconds=123)
    assert time.seconds_to_human(payload) == '4 days, 2 minutes ago'

    payload = datetime.timedelta(days=365, seconds=5)
    assert time.seconds_to_human(payload) == '1 year, 5 seconds ago'


def test_seconds_to_human_granularity():
    assert time.seconds_to_human(3672) == '1 hour, 1 minute ago'
    assert time.seconds_to_human(3672, 3) == '1 hour, 1 minute, 12 seconds ago'
    assert time.seconds_to_human(3672, 1) == '1 hour ago'

    assert time.seconds_to_human(-3672) == 'in 1 hour, 1 minute'
    assert time.seconds_to_human(-3672, 3) == 'in 1 hour, 1 minute, 12 seconds'
    assert time.seconds_to_human(-3672, 1) == 'in 1 hour'


def test_seconds_to_split():
    assert time.seconds_to_split(364465915) == (11, 6, 20, 8, 31, 55)
    assert time.seconds_to_split(15) == (0, 0, 0, 0, 0, 15)
    assert time.seconds_to_split(120) == (0, 0, 0, 0, 2, 0)
    assert time.seconds_to_split(7800) == (0, 0, 0, 2, 10, 0)
    assert time.seconds_to_split(143659) == (0, 0, 1, 15, 54, 19)
    assert time.seconds_to_split(128000) == (0, 0, 1, 11, 33, 20)
    assert time.seconds_to_split(3000000) == (0, 1, 4, 5, 20, 0)


def test_get_time_unit():
    assert time.get_time_unit(days=1, hours=15, minutes=54, seconds=19) == (
        (0, 'years'),
        (0, 'months'),
        (1, 'day'),
        (15, 'hours'),
        (54, 'minutes'),
        (19, 'seconds'),
    )
    assert time.get_time_unit(years=1) == (
        (1, 'year'),
        (0, 'months'),
        (0, 'days'),
        (0, 'hours'),
        (0, 'minutes'),
        (0, 'seconds'),
    )
    assert time.get_time_unit(
        years=1,
        months=1,
        days=1,
        hours=1,
        minutes=1,
        seconds=1
    ) == (
        (1, 'year'),
        (1, 'month'),
        (1, 'day'),
        (1, 'hour'),
        (1, 'minute'),
        (1, 'second'),
    )
    assert time.get_time_unit(
        years=10,
        months=10,
        days=10,
        hours=10,
        minutes=10,
        seconds=10
    ) == (
        (10, 'years'),
        (10, 'months'),
        (10, 'days'),
        (10, 'hours'),
        (10, 'minutes'),
        (10, 'seconds'),
    )
