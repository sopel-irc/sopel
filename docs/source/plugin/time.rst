==========
About time
==========

Your plugin may want to display dates and times in messages. For that, you can
always count on the :mod:`datetime` built-in module. However, what if you would
like to respect the date-format for a given user or a given channel? Functions
of :mod:`sopel.tools.time` can help you with that:

* :func:`~sopel.tools.time.get_timezone` will fetch the right timezone for you
* :func:`~sopel.tools.time.format_time` will format your aware datetime for you

Here is a full example of that, adapted from the built-in ``.t`` command::

    import datetime

    import pytz

    from sopel import plugin
    from sopel.tools.time import format_time, get_timezone


    @plugin.command('.t')
    @plugin.require_chanmsg
    def my_command(bot, trigger):
        """Give time in a channel."""
        time = pytz.UTC.localize(datetime.datetime.utcnow())
        timezone = get_timezone(
            bot.db,
            bot.settings,
            nick=trigger.nick,
            channel=trigger.sender,
        )
        formatted_time = format_time(
            bot.db,
            bot.settings,
            timezone,
            trigger.nick,
            trigger.sender,
            time,
        )
        bot.say(formatted_time)

Getting the time
================

As mentioned earlier, Sopel relies on a Python built-in module:
:mod:`datetime`. This module allows you to get the current time like this::

    >>> import datetime
    >>> datetime.datetime.now()
    datetime.datetime(2021, 7, 26, 18, 7, 13, 491786)
    >>> datetime.datetime.utcnow()
    datetime.datetime(2021, 7, 26, 16, 7, 16, 496404)

As you can see at the moment of writing this documentation, there was a 2h
offset between the local time and UTC. To properly manage timezones and UTC
offsets, it is best to rely on ``pytz``, and work with UTC only::

    >>> import pytz
    >>> pytz.UTC.localize(datetime.datetime.utcnow())
    datetime.datetime(2021, 7, 26, 16, 7, 19, 321828, tzinfo=<UTC>)

This way, you'll always have an aware datetime to work with (store, compare,
manipulate, etc.) that doesn't depend on your local time, and you'll only
convert it to the proper timezone when you need to.

.. note::

    You should **always** work with aware datetime objects. It's also easier to
    always work with UTC+0 datetime as input and in storage, then convert to
    another timezone when displaying time to a user.

Getting the timezone
====================

Sopel uses ``pytz`` to handle timezones to manipulate aware datetimes, i.e.
datetimes with timezone-related information such as the UTC Offset and DST
(`Daylight Saving Time`__) status. When using this library, getting a timezone
is straightforward (as long as you know the `IANA name of said timezone`__)::

    >>> paris = pytz.timezone('Europe/Paris')

Then you can get a UTC datetime::

    >>> now = pytz.UTC.localize(datetime.datetime.utcnow())

Which you can convert to your timezone, or to another timezone::

    >>> now.astimezone(paris)  # convert to timezone
    datetime.datetime(
        2021, 7, 26, 18, 7, 49, 27970,
        tzinfo=<DstTzInfo 'Europe/Paris' CEST+2:00:00 DST>)
    >>> chicago = pytz.timezone('America/Chicago')
    >>> now.astimezone(chicago)  # convert to a different timezone
    datetime.datetime(
        2021, 7, 26, 11, 7, 58, 610998,
        tzinfo=<DstTzInfo 'America/Chicago' CDT-1 day, 19:00:00 DST>

.. __: https://en.wikipedia.org/wiki/Daylight_saving_time
.. __: https://en.wikipedia.org/wiki/List_of_tz_database_time_zones

To get the IANA timezone for a given user or channel, you should use the
:func:`~sopel.tools.time.get_timezone` function::

    >>> from sopel.tools.time import get_timezone
    >>> # assuming bot is an instance of sopel.bot.Sopel
    >>> custom_tz = get_timezone(
    ...     bot.db, bot.settings,
    ...     zone=None, nick='Nick', channel='#sopel',
    ... )  # should be something like "Europe/Paris"
    >>> local_now = now.astimezone(pytz.timezone(custom_tz))

This function does all the heavy lifting of looking for the right timezone, as
configured for a user, a channel, or the bot itself.

.. seealso::

    The `pytz library`__ is used by Sopel to manipulate timezone for aware
    datetimes. You can always assume it is available for your plugin since
    Sopel depends on this library.

.. __: https://pypi.org/project/pytz/

Format time
===========

So far, you have:

* an aware datetime in UTC+0
* the user (or channel) timezone

And you want to:

* display the time properly formatted for a user/channel

Then you have arrived at the last step of your journey, thanks to the
:func:`~sopel.tools.time.format_time` function::

    >>> from sopel.tools.time import format_time
    >>> format_time(
    ...  bot.db, bot.settings,
    ...  zone=custom_tz, nick='Nick', channel='#sopel', time=now,
    ... )
    '2021-07-26 - 18:07:49 (Europe/Paris)'

And voilà! You now have a string formatted aware datetime that uses the format
defined for a user/channel/the bot, and can now rest and enjoy your own time.

Best practices
==============

So far, you have learned how to get a time formatted with the preferred timezone
and format of a user: this is perfect for a command like ``.time`` that
displays the time for a specific user in mind. However, other commands, like
URL previews, are not related to users, and they should use a different
strategy to figure out the right timezone and format.

User specific time
------------------

A user specific time is when the time is displayed for a specific user: a
direct message, a reminder, the user's time, etc.

In that case, the recommended order to select the appropriate timezone and time
format is:

* user's preferred ones
* channel's preferred ones
* bot's timezone and format (from configuration)
* default timezone and format

This can be done with :func:`~sopel.tools.time.get_timezone` and
:func:`~sopel.tools.time.format_time`::

    >>> custom_tz = get_timezone(
    ...     bot.db, bot.settings, zone=None,
    ...     nick=nick_name, channel=channel_name,
    ... )
    >>> display_time = format_time(
    ...     bot.db, bot.settings, zone=custom_tz,
    ...     nick=nick_name, channel=channel_name, time=user_time,
    ... )

Other times
-----------

When displaying a time that is not for a specific user, it doesn't make sense
to display time with the user's preferred format. For example, a URL preview
plugin is not displaying a user specific time.

In that case, the recommended order to select the appropriate timezone and time
format is:

* channel's preferred ones
* bot's timezone and format (from configuration)
* default timezone and format

This can be done with :func:`~sopel.tools.time.get_timezone` and
:func:`~sopel.tools.time.format_time`::

    >>> custom_tz = get_timezone(
    ...     bot.db, bot.settings, zone=None,
    ...     channel=channel_name,
    ... )
    >>> display_time = plugin_defined_format or format_time(
    ...     bot.db, bot.settings, zone=custom_tz,
    ...     channel=channel_name, time=plugin_time,
    ... )

Note the absence of the ``nick`` parameter in that snippet.
