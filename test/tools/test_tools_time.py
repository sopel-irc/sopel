# coding=utf-8
"""Tools for getting and displaying the time."""
from __future__ import absolute_import, division, print_function, unicode_literals

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


def test_time_timedelta_formatter():
    payload = 10000
    assert time.seconds_to_human(payload) == '2 hours, 46 minutes ago'

    payload = -2938124
    assert time.seconds_to_human(payload) == 'in 1 month, 3 days'

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
