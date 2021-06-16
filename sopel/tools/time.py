# coding=utf-8
"""Tools for getting and displaying the time."""
from __future__ import absolute_import, division, print_function, unicode_literals

import datetime

import pytz


# various time units measured in seconds; approximated for months and years
SECONDS = 1
MINUTES = 60 * SECONDS
HOURS = 60 * MINUTES
DAYS = 24 * HOURS
MONTHS = int(30.5 * DAYS)
YEARS = 365 * DAYS


def validate_timezone(zone):
    """Return an IETF timezone from the given IETF zone or common abbreviation.

    :param str zone: in a strict or a human-friendly format
    :return: the valid IETF timezone properly formatted
    :raise ValueError: when ``zone`` is not a valid timezone

    Prior to checking timezones, two transformations are made to make the zone
    names more human-friendly:

    1. the string is split on ``', '``, the pieces reversed, and then joined
       with ``/`` (*"New York, America"* becomes *"America/New York"*)
    2. Remaining spaces are replaced with ``_``

    This means ``new york, america`` becomes ``America/New_York``, and ``utc``
    becomes ``UTC``. In the majority of user-facing interactions, such
    case-insensitivity will be expected.

    If the zone is not valid, ``ValueError`` will be raised.
    """
    if zone is None:
        return None

    zone = '/'.join(reversed(zone.split(', '))).replace(' ', '_')
    try:
        tz = pytz.timezone(zone)
    except pytz.exceptions.UnknownTimeZoneError:
        raise ValueError('Invalid time zone.')
    return tz.zone


def validate_format(tformat):
    """Validate a time format string.

    :param str tformat: the format string to validate
    :return: the format string, if valid
    :raise ValueError: when ``tformat`` is not a valid time format string
    """
    try:
        time = datetime.datetime.utcnow()
        time.strftime(tformat)
    except (ValueError, TypeError):
        raise ValueError('Invalid time format.')
    return tformat


def get_nick_timezone(db, nick):
    """Get a nick's timezone from database.

    :param db: Bot's database handler (usually ``bot.db``)
    :type db: :class:`~sopel.db.SopelDB`
    :param nick: IRC nickname
    :type nick: :class:`~sopel.tools.Identifier`
    :return: the timezone associated with the ``nick``

    If a timezone cannot be found for ``nick``, or if it is invalid, ``None``
    will be returned.
    """
    try:
        return validate_timezone(db.get_nick_value(nick, 'timezone'))
    except ValueError:
        return None


def get_channel_timezone(db, channel):
    """Get a channel's timezone from database.

    :param db: Bot's database handler (usually ``bot.db``)
    :type db: :class:`~sopel.db.SopelDB`
    :param channel: IRC channel name
    :type channel: :class:`~sopel.tools.Identifier`
    :return: the timezone associated with the ``channel``

    If a timezone cannot be found for ``channel``, or if it is invalid,
    ``None`` will be returned.
    """
    try:
        return validate_timezone(db.get_channel_value(channel, 'timezone'))
    except ValueError:
        return None


def get_timezone(db=None, config=None, zone=None, nick=None, channel=None):
    """Find, and return, the appropriate timezone.

    :param db: bot database object (optional)
    :type db: :class:`~.db.SopelDB`
    :param config: bot config object (optional)
    :type config: :class:`~.config.Config`
    :param str zone: preferred timezone name (optional)
    :param str nick: nick whose timezone to use, if set (optional)
    :param str channel: channel whose timezone to use, if set (optional)

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
    def _check(zone):
        try:
            return validate_timezone(zone)
        except ValueError:
            return None

    tz = None

    if zone:
        tz = _check(zone)
        if not tz:
            tz = _check(
                db.get_nick_or_channel_value(zone, 'timezone'))
    if not tz and nick:
        tz = _check(db.get_nick_value(nick, 'timezone'))
    if not tz and channel:
        tz = _check(db.get_channel_value(channel, 'timezone'))
    if not tz and config and config.core.default_timezone:
        tz = _check(config.core.default_timezone)
    return tz


def format_time(db=None, config=None, zone=None, nick=None, channel=None,
                time=None):
    """Return a formatted string of the given time in the given zone.

    :param db: bot database object (optional)
    :type db: :class:`~.db.SopelDB`
    :param config: bot config object (optional)
    :type config: :class:`~.config.Config`
    :param str zone: name of timezone to use (optional)
    :param str nick: nick whose time format to use, if set (optional)
    :param str channel: channel whose time format to use, if set (optional)
    :param time: the time value to format (optional)
    :type time: :class:`~datetime.datetime`

    ``time``, if given, should be a naive ``datetime.datetime`` object and will
    be treated as being in the UTC timezone. If it is not given, the current
    time will be used. If ``zone`` is given it must be present in the IANA Time
    Zone Database; ``get_timezone`` can be helpful for this. If ``zone`` is not
    given, UTC will be assumed.

    The format for the string is chosen in the following order:

    1. The format for the nick ``nick`` in ``db``, if one is set and valid.
    2. The format for the channel ``channel`` in ``db``, if one is set and
       valid.
    3. The default format in ``config``, if one is set and valid.
    4. ISO-8601

    If ``db`` is not given or is not set up, steps 1 and 2 are skipped. If
    ``config`` is not given, step 3 will be skipped.
    """
    tformat = None
    if db:
        if nick:
            tformat = db.get_nick_value(nick, 'time_format')
        if not tformat and channel:
            tformat = db.get_channel_value(channel, 'time_format')
    if not tformat and config and config.core.default_time_format:
        tformat = config.core.default_time_format
    if not tformat:
        tformat = '%Y-%m-%d - %T%Z'

    if not time:
        time = datetime.datetime.utcnow()

    if not zone:
        return time.strftime(tformat)
    else:
        if not time.tzinfo:
            utc = pytz.timezone('UTC')
            time = utc.localize(time)
        zone = pytz.timezone(zone)
        return time.astimezone(zone).strftime(tformat)


def seconds_to_split(seconds):
    """Split an amount of ``seconds`` into years, months, days, etc.

    :param int seconds: amount of time in seconds
    :return: the time split into a tuple of years, months, days, hours,
             minutes, and seconds
    :rtype: :class:`tuple`

    Examples::

        >>> seconds_to_split(7800)
        (0, 0, 0, 2, 10, 0)
        >>> seconds_to_split(143659)
        (0, 0, 1, 15, 54, 19)

    """
    years, seconds_left = divmod(int(seconds), YEARS)
    months, seconds_left = divmod(seconds_left, MONTHS)
    days, seconds_left = divmod(seconds_left, DAYS)
    hours, seconds_left = divmod(seconds_left, HOURS)
    minutes, seconds_left = divmod(seconds_left, MINUTES)

    return years, months, days, hours, minutes, seconds_left


def get_time_unit(years=0, months=0, days=0, hours=0, minutes=0, seconds=0):
    """Map a time in (y, m, d, h, min, s) to its labels.

    :param int years: number of years
    :param int months: number of months
    :param int days: number of days
    :param int hours: number of hours
    :param int minutes: number of minutes
    :param int seconds: number of seconds
    :return: a tuple of 2-value tuples, each for a time amount and its label
    :rtype: :class:`tuple`

    This helper function get a time split in years, months, days, hours,
    minutes, and seconds to return a tuple with the correct label for each
    unit. The label is pluralized and account for zéro, one, and more than one
    value per unit::

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


def seconds_to_human(secs, granularity=2):
    """Format :class:`~datetime.timedelta` as a human-readable relative time.

    :param secs: time difference to format
    :type secs: :class:`~datetime.timedelta` or integer
    :param int granularity: number of time units to return (default to 2)

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
