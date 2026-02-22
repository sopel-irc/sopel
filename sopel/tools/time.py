"""Tools for getting and displaying the time.

.. versionadded:: 5.3
.. versionchanged:: 6.0

    Moved from ``willie`` namespace to ``sopel`` namespace for project rename.

"""
from __future__ import annotations

import datetime
from typing import cast, NamedTuple, TYPE_CHECKING, Union

import pytz


if TYPE_CHECKING:
    from sopel.config import Config
    from sopel.db import SopelDB


# various time units measured in seconds; approximated for months and years
SECONDS = 1
MINUTES = 60 * SECONDS
HOURS = 60 * MINUTES
DAYS = 24 * HOURS
MONTHS = int(30.5 * DAYS)
YEARS = 365 * DAYS


class Duration(NamedTuple):
    """Named tuple representation of a duration.

    This can be used as a tuple as well as an object::

        >>> d = Duration(minutes=12, seconds=34)
        >>> d.minutes
        12
        >>> d.seconds
        34
        >>> years, months, days, hours, minutes, seconds = d
        >>> (years, months, days, hours, minutes, seconds)
        (0, 0, 0, 0, 12, 34)

    """
    years: int = 0
    """Years spent."""
    months: int = 0
    """Months spent."""
    days: int = 0
    """Days spent."""
    hours: int = 0
    """Hours spent."""
    minutes: int = 0
    """Minutes spent."""
    seconds: int = 0
    """Seconds spent."""


def validate_timezone(zone: str | None) -> str:
    """Normalize and validate an IANA timezone name.

    :param zone: in a strict or a human-friendly format
    :return: the valid IANA timezone properly formatted
    :raise ValueError: when ``zone`` is not a valid timezone
                       (including empty string and ``None`` value)

    Prior to checking timezones, two transformations are made to make the zone
    names more human-friendly:

    1. the string is split on ``', '``, the pieces reversed, and then joined
       with ``/`` (*"New York, America"* becomes *"America/New York"*)
    2. Remaining spaces are replaced with ``_``

    This means ``new york, america`` becomes ``America/New_York``, and ``utc``
    becomes ``UTC``. In the majority of user-facing interactions, such
    case-insensitivity will be expected.

    If the zone is not valid, :exc:`ValueError` will be raised.

    .. versionadded:: 6.0

    .. versionchanged:: 8.0

        If ``zone`` is ``None``, raises a :exc:`ValueError` as if it was an
        empty string or an invalid timezone instead of returning ``None``.

    """
    if zone is None:
        raise ValueError('Invalid time zone.')

    zone = '/'.join(reversed(zone.split(', '))).replace(' ', '_')
    try:
        tz = pytz.timezone(zone)
    except pytz.exceptions.UnknownTimeZoneError:
        raise ValueError('Invalid time zone.')

    return cast('str', tz.zone)


def validate_format(tformat: str) -> str:
    """Validate a time format string.

    :param tformat: the format string to validate
    :return: the format string, if valid
    :raise ValueError: when ``tformat`` is not a valid time format string

    .. versionadded:: 6.0
    """
    try:
        time = datetime.datetime.now(datetime.timezone.utc)
        time.strftime(tformat)
    except (ValueError, TypeError):
        raise ValueError('Invalid time format.')
    return tformat


def get_nick_timezone(db: SopelDB, nick: str) -> str | None:
    """Get a nick's timezone from database.

    :param db: Bot's database handler (usually ``bot.db``)
    :param nick: IRC nickname
    :return: the timezone associated with the ``nick``

    If a timezone cannot be found for ``nick``, or if it is invalid, ``None``
    will be returned.

    .. versionadded:: 7.0
    """
    try:
        return validate_timezone(db.get_nick_value(nick, 'timezone'))
    except ValueError:
        return None


def get_channel_timezone(db: SopelDB, channel: str) -> str | None:
    """Get a channel's timezone from database.

    :param db: Bot's database handler (usually ``bot.db``)
    :param channel: IRC channel name
    :return: the timezone associated with the ``channel``

    If a timezone cannot be found for ``channel``, or if it is invalid,
    ``None`` will be returned.

    .. versionadded:: 7.0
    """
    try:
        return validate_timezone(db.get_channel_value(channel, 'timezone'))
    except ValueError:
        return None


def get_timezone(
    db: SopelDB | None = None,
    config: Config | None = None,
    zone: str | None = None,
    nick: str | None = None,
    channel: str | None = None,
) -> str | None:
    """Find, and return, the appropriate timezone.

    :param db: bot database object (optional)
    :param config: bot config object (optional)
    :param zone: preferred timezone name (optional)
    :param nick: nick whose timezone to use, if set (optional)
    :param channel: channel whose timezone to use, if set (optional)

    Timezone is pulled in the following priority:

    1. ``zone``, if it is valid
    2. The timezone for the channel or nick ``zone`` in ``db`` if one is set
       and valid.
    3. The timezone for the nick ``nick`` in ``db``, if one is set and valid.
    4. The timezone for the channel ``channel`` in ``db``, if one is set and
       valid.
    5. The default timezone in ``config``, if one is set and valid.

    If ``db`` is not given, or given but not set up, steps 2 and 3 will be
    skipped. If ``config`` is not given, step 4 will be skipped. If no step
    yields a valid timezone, ``None`` is returned.

    Valid timezones are those present in the IANA Time Zone Database.

    .. seealso::

       The :func:`validate_timezone` function handles the validation and
       formatting of the timezone.

    """
    def _check(zone: str | None) -> str | None:
        try:
            return validate_timezone(zone)
        except ValueError:
            return None

    tz: str | None = None

    if zone:
        tz = _check(zone)
        # zone might be a nick or a channel
        if not tz and db is not None:
            tz = _check(db.get_nick_or_channel_value(zone, 'timezone'))

    # get nick's timezone, and if none, get channel's timezone instead
    if not tz and db is not None:
        if nick:
            tz = _check(db.get_nick_value(nick, 'timezone'))
        if not tz and channel:
            tz = _check(db.get_channel_value(channel, 'timezone'))

    # if still not found, default to core configuration
    if not tz and config is not None and config.core.default_timezone:
        tz = _check(config.core.default_timezone)

    return tz


def format_time(
    db: SopelDB | None = None,
    config: Config | None = None,
    zone: str | None = None,
    nick: str | None = None,
    channel: str | None = None,
    time: datetime.datetime | None = None,
) -> str:
    """Return a formatted string of the given time in the given zone.

    :param db: bot database object (optional)
    :param config: bot config object (optional)
    :param zone: name of timezone to use for output (optional)
    :param nick: nick whose time format to use, if set (optional)
    :param channel: channel whose time format to use, if set (optional)
    :param time: the time value to format (optional)

    ``time``, if given, should be a ``~datetime.datetime`` object, and will be
    treated as being in the UTC timezone if it is :ref:`naïve
    <datetime-naive-aware>`. If ``time`` is not given, the current time will
    be used.

    If ``zone`` is given it must be present in the IANA Time Zone Database;
    ``get_timezone`` can be helpful for this. If ``zone`` is not given, UTC
    will be assumed.

    The format for the string is chosen in the following order:

    1. The format for the nick ``nick`` in ``db``, if one is set and valid.
    2. The format for the channel ``channel`` in ``db``, if one is set and
       valid.
    3. The default format in ``config``, if one is set and valid.
    4. ISO-8601

    If ``db`` is not given or is not set up, steps 1 and 2 are skipped. If
    ``config`` is not given, step 3 will be skipped.
    """
    target_tz: datetime.tzinfo = pytz.utc
    tformat: str | None = None

    # get an aware datetime
    if not time:
        time = datetime.datetime.now(datetime.timezone.utc)
    elif not time.tzinfo:
        time = pytz.utc.localize(time)

    # get target timezone
    if zone:
        target_tz = pytz.timezone(zone)

    # get format for nick or channel
    if db:
        if nick:
            tformat = db.get_nick_value(nick, 'time_format')
        if not tformat and channel:
            tformat = db.get_channel_value(channel, 'time_format')

    # get format from configuration
    if not tformat and config and config.core.default_time_format:
        tformat = config.core.default_time_format

    # or default to hard-coded format
    if not tformat:
        tformat = '%Y-%m-%d - %T %z'

    # format local time with format
    return time.astimezone(target_tz).strftime(tformat)


def seconds_to_split(seconds: int) -> Duration:
    """Split an amount of ``seconds`` into years, months, days, etc.

    :param seconds: amount of time in seconds
    :return: the time split into a named tuple of years, months, days, hours,
             minutes, and seconds

    Examples::

        >>> seconds_to_split(7800)
        Duration(years=0, months=0, days=0, hours=2, minutes=10, seconds=0)
        >>> seconds_to_split(143659)
        Duration(years=0, months=0, days=1, hours=15, minutes=54, seconds=19)

    .. versionadded:: 7.1

    .. versionchanged:: 8.0

        This function returns a :class:`Duration` named tuple.

    """
    years, seconds_left = divmod(int(seconds), YEARS)
    months, seconds_left = divmod(seconds_left, MONTHS)
    days, seconds_left = divmod(seconds_left, DAYS)
    hours, seconds_left = divmod(seconds_left, HOURS)
    minutes, seconds_left = divmod(seconds_left, MINUTES)

    return Duration(years, months, days, hours, minutes, seconds_left)


def get_time_unit(
    years: int = 0,
    months: int = 0,
    days: int = 0,
    hours: int = 0,
    minutes: int = 0,
    seconds: int = 0,
) -> tuple[
    tuple[int, str],
    tuple[int, str],
    tuple[int, str],
    tuple[int, str],
    tuple[int, str],
    tuple[int, str],
]:
    """Map a time in (y, m, d, h, min, s) to its labels.

    :param years: number of years
    :param months: number of months
    :param days: number of days
    :param hours: number of hours
    :param minutes: number of minutes
    :param seconds: number of seconds
    :return: a tuple of 2-value tuples, each for a time amount and its label

    This helper function takes a time split into years, months, days, hours,
    minutes, and seconds to return a tuple with the correct label for each
    unit. The label is pluralized according to whether the value is zero, one,
    or more than one::

        >>> get_time_unit(days=1, hours=15, minutes=54, seconds=19)
        (
            (0, 'years'),
            (0, 'months'),
            (1, 'day'),
            (15, 'hours'),
            (54, 'minutes'),
            (19, 'seconds'),
        )

    This function can be used with :func:`seconds_to_split`::

        >>> get_time_unit(*seconds_to_split(143659))
        # ... same result as the example above

    .. versionadded:: 7.1

    .. note::

        This function always returns a tuple with **all** time units, even when
        their amount is 0 (which is their default value).

    """
    years_text = "year{}".format("s" if years != 1 else "")
    months_text = "month{}".format("s" if months != 1 else "")
    days_text = "day{}".format("s" if days != 1 else "")
    hours_text = "hour{}".format("s" if hours != 1 else "")
    minutes_text = "minute{}".format("s" if minutes != 1 else "")
    seconds_text = "second{}".format("s" if seconds != 1 else "")

    return (
        (years, years_text),
        (months, months_text),
        (days, days_text),
        (hours, hours_text),
        (minutes, minutes_text),
        (seconds, seconds_text),
    )


def seconds_to_human(
    secs: Union[datetime.timedelta, float, int],
    granularity: int = 2,
) -> str:
    """Format :class:`~datetime.timedelta` as a human-readable relative time.

    :param secs: time difference to format
    :param granularity: number of time units to return (default to 2)

    Inspiration for function structure from:
    https://gist.github.com/Highstaker/280a09591df4a5fb1363b0bbaf858f0d

    Examples::

        >>> seconds_to_human(65707200)
        '2 years, 1 month ago'
        >>> seconds_to_human(-17100)  # negative amount
        'in 4 hours, 45 minutes'
        >>> seconds_to_human(-709200)
        'in 8 days, 5 hours'
        >>> seconds_to_human(39441600, 1)  # 1 year + 3 months
        '1 year ago'

    This function can be used with a :class:`~datetime.timedelta`::

        >>> from datetime import timedelta
        >>> seconds_to_human(timedelta(days=42, seconds=278))
        '1 month, 11 days ago'

    The ``granularity`` argument controls how detailed the result is::

        >>> seconds_to_human(3672)  # 2 by default
        '1 hour, 1 minute ago'
        >>> seconds_to_human(3672, granularity=3)
        '1 hour, 1 minute, 12 seconds ago'
        >>> seconds_to_human(3672, granularity=1)
        '1 hour ago'

    .. versionadded:: 7.0
    """
    if isinstance(secs, datetime.timedelta):
        secs = secs.total_seconds()

    future = False
    if secs < 0:
        future = True

    secs = int(secs)
    secs = abs(secs)

    if secs == 0:
        # zero is a special case that the algorithm below won't handle correctly (#1841)
        result = "0 seconds"
    else:
        result = ", ".join([
            "%s %s" % (value, unit)
            for value, unit in get_time_unit(*seconds_to_split(secs))
            if value
        ][:granularity])

    if future is False:
        result += " ago"
    else:
        result = "in " + result

    return result
