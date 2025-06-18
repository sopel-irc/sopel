"""Tools for getting and displaying the time."""
from __future__ import annotations

import datetime
from typing import TYPE_CHECKING

import pytest
import pytz

from sopel.db import SopelDB
from sopel.tools import time

if TYPE_CHECKING:
    from sopel.config import Config


TMP_CONFIG = """
[core]
owner = Pepperpots
db_filename = {db_filename}
"""


@pytest.fixture
def tmpconfig(configfactory, tmpdir):
    content = TMP_CONFIG.format(db_filename=tmpdir.join('test.sqlite'))
    return configfactory('default.cfg', content)


@pytest.fixture
def db(tmpconfig):
    db = SopelDB(tmpconfig)
    return db


def test_validate_timezone():
    assert time.validate_timezone('Europe/Paris') == 'Europe/Paris'
    assert time.validate_timezone('America/New York') == 'America/New_York'
    assert time.validate_timezone('Paris, Europe') == 'Europe/Paris'
    assert time.validate_timezone('New York, America') == 'America/New_York'
    assert time.validate_timezone('Israel') == 'Israel'


def test_validate_timezone_invalid():
    with pytest.raises(ValueError):
        time.validate_timezone(None)

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


def test_get_nick_timezone(db: SopelDB):
    nick = 'IronMan'
    assert time.get_nick_timezone(db, nick) is None

    db.set_nick_value(nick, 'timezone', 'Europe/Paris')
    assert time.get_nick_timezone(db, nick) == 'Europe/Paris'

    db.set_nick_value(nick, 'timezone', 'Invalid_TZ')
    assert time.get_nick_timezone(db, nick) is None


def test_get_channel_timezone(db: SopelDB):
    channel = '#test'
    assert time.get_channel_timezone(db, channel) is None

    db.set_channel_value(channel, 'timezone', 'Europe/Paris')
    assert time.get_channel_timezone(db, channel) == 'Europe/Paris'

    db.set_channel_value(channel, 'timezone', 'Invalid_TZ')
    assert time.get_channel_timezone(db, channel) is None


def test_get_timezone_config_only(db: SopelDB, tmpconfig: Config):
    zone = 'Europe/Paris'

    assert time.get_timezone(db) is None
    assert time.get_timezone(db, tmpconfig) == 'UTC', (
        'Must use default timezone from config'
    )
    assert time.get_timezone(db, tmpconfig, zone) == zone


def test_get_timezone_only_nick_data(db: SopelDB, tmpconfig: Config):
    zone_nick = 'America/New_York'
    nick = 'IronMan'
    channel = '#test'

    db.set_nick_value(nick, 'timezone', zone_nick)

    assert time.get_timezone(db, tmpconfig, None, nick, channel) == zone_nick


def test_get_timezone_only_channel_data(db: SopelDB, tmpconfig: Config):
    zone_channel = 'Asia/Tokyo'
    nick = 'IronMan'
    channel = '#test'

    db.set_channel_value(channel, 'timezone', zone_channel)

    assert time.get_timezone(
        db, tmpconfig, None, nick, channel
    ) == zone_channel
    assert time.get_timezone(
        db, tmpconfig, 'Invalid/Tz', nick, channel
    ) == zone_channel, 'Expected channel timezone'


def test_get_timezone_nick_and_channel_data(db: SopelDB, tmpconfig: Config):
    zone_nick = 'America/New_York'
    zone_channel = 'Asia/Tokyo'
    nick = 'IronMan'
    channel = '#test'

    db.set_nick_value(nick, 'timezone', zone_nick)
    db.set_channel_value(channel, 'timezone', zone_channel)

    assert time.get_timezone(db, tmpconfig, None, nick, channel) == zone_nick, (
        'Nick timezone must take priority'
    )


def test_get_timezone_zone_nick_or_channel(db: SopelDB, tmpconfig):
    zone_nick = 'America/New_York'
    zone_channel = 'Asia/Tokyo'
    nick = 'IronMan'
    channel = '#test'

    db.set_nick_value(nick, 'timezone', zone_nick)
    db.set_channel_value(channel, 'timezone', zone_channel)

    # when zone is actually a nick
    assert time.get_timezone(db, tmpconfig, zone=nick) == zone_nick
    assert time.get_timezone(
        db, tmpconfig, zone=nick, channel=channel
    ) == zone_nick, 'zone argument must have priority over channel arguments'
    assert time.get_timezone(
        db, tmpconfig, zone=nick, nick=nick, channel=channel
    ) == zone_nick, 'zone argument must have priority over other arguments'

    # when zone is actually a channel
    assert time.get_timezone(db, tmpconfig, zone=channel) == zone_channel
    assert time.get_timezone(
        db, tmpconfig, zone=channel, nick=nick
    ) == zone_channel, 'zone argument must have priority over nick argument'
    assert time.get_timezone(
        db, tmpconfig, zone=channel, nick=nick, channel=channel
    ) == zone_channel, 'zone argument must have priority over other arguments'


def test_get_timezone_zone_has_priority(db: SopelDB, tmpconfig: Config):
    zone = 'Europe/Paris'
    nick = 'IronMan'
    channel = '#test'

    db.set_nick_value(nick, 'timezone', 'America/New_York')
    db.set_channel_value(channel, 'timezone', 'Asia/Tokyo')
    assert time.get_timezone(db, tmpconfig, zone, nick, channel) == zone, (
        'zone argument must have priority over other arguments'
    )


UTC = pytz.timezone('UTC')
PARIS = pytz.timezone('Europe/Paris')

TIME_FORMAT_PAIRS = [
    (
        # Naïve
        datetime.datetime(
            2021, 7, 4, 17, 7, 6,
            tzinfo=None,
        ),
        '2021-07-04 - 17:07:06 +0000',
    ),
    (
        # Aware, UTC
        datetime.datetime(
            2021, 7, 4, 17, 7, 6,
            tzinfo=UTC,
        ),
        '2021-07-04 - 17:07:06 +0000',
    ),
    (
        # Aware, non-UTC
        datetime.datetime(
            2021, 7, 4, 17, 7, 6,
            tzinfo=UTC,
        ).astimezone(PARIS),
        '2021-07-04 - 17:07:06 +0000',
    ),
]


@pytest.mark.parametrize('time_arg, result', TIME_FORMAT_PAIRS)
def test_format_time(time_arg: datetime.datetime, result: str):
    assert time.format_time(time=time_arg) == result


def test_format_time_config_default_format(tmpconfig: Config):
    time_arg = datetime.datetime(2023, 4, 22, 19, 38, 26)
    tmpconfig.core.default_time_format = '%Y-%m-%d at %H:%M'
    assert time.format_time(
        config=tmpconfig, time=time_arg
    ) == '2023-04-22 at 19:38'

    # with timezone
    assert time.format_time(
        config=tmpconfig, time=time_arg, zone='Europe/Paris',
    ) == '2023-04-22 at 21:38'


def test_format_time_nick_format(tmpconfig: Config, db: SopelDB):
    nick = 'IronMan'
    time_arg = datetime.datetime(2023, 4, 22, 19, 38, 26)
    tmpconfig.core.default_time_format = '%Y-%m-%d at %H:%M'
    db.set_nick_value(nick, 'time_format', '%H:%M on %h %d of %Y')
    assert time.format_time(
        db, config=tmpconfig, nick=nick, time=time_arg
    ) == '19:38 on Apr 22 of 2023'

    # with timezone
    assert time.format_time(
        db, config=tmpconfig, nick=nick, time=time_arg, zone='Europe/Paris',
    ) == '21:38 on Apr 22 of 2023'


def test_format_time_channel_format(tmpconfig: Config, db: SopelDB):
    nick = 'IronMan'
    channel = '#test'
    time_arg = datetime.datetime(2023, 4, 22, 19, 38, 26)
    tmpconfig.core.default_time_format = '%Y-%m-%d at %H:%M'
    db.set_channel_value(channel, 'time_format', '%H:%M on %h %d of %Y')
    assert time.format_time(
        db, config=tmpconfig, channel=channel, time=time_arg
    ) == '19:38 on Apr 22 of 2023'

    # with timezone
    assert time.format_time(
        db, config=tmpconfig,
        channel=channel,
        time=time_arg,
        zone='Europe/Paris',
    ) == '21:38 on Apr 22 of 2023'

    # nick has priority
    db.set_nick_value(nick, 'time_format', '%h %d of %Y at %H:%M')
    assert time.format_time(
        db, config=tmpconfig, nick=nick, channel=channel, time=time_arg
    ) == 'Apr 22 of 2023 at 19:38'


def test_format_time_utcnow():
    result = time.format_time()
    parsed = datetime.datetime.strptime(result, '%Y-%m-%d - %H:%M:%S +0000')
    assert result == time.format_time(time=parsed)


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
    assert time.seconds_to_split(0) == (0, 0, 0, 0, 0, 0)


def test_seconds_to_split_duration():
    duration = time.seconds_to_split(364465915)
    assert duration.years == 11
    assert duration.months == 6
    assert duration.days == 20
    assert duration.hours == 8
    assert duration.minutes == 31
    assert duration.seconds == 55


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
