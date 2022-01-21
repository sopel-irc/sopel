=====================
Interact with the bot
=====================

Once a :term:`Rule` has been triggered, it's time to do whatever the plugin is
supposed to do. Thanks to the ``bot`` parameter, you can make the bot talk:
say something in a channel, reply to someone, send a notice, or join a channel.


Make it talk
============

The most basic way to make the bot talk is to use its
:meth:`~sopel.bot.SopelWrapper.say` method. The wrapper knows the origin of
the trigger (a channel or a private message), and it will use this origin as
the default destination for your message::

    # will send that to trigger.sender
    bot.say('The bot is now talking!')

If you want to send the message to another destination, you can pass it as the
second argument::

    bot.say('The bot is now talking!', '#private-channel')

Instead of a string, you can use an instance of
:class:`~sopel.tools.identifiers.Identifier`.

If you want to reply to a user in a private message, you can use the trigger's
:attr:`~sopel.trigger.Trigger.nick` attribute as destination::

    bot.say('I reply in private message', trigger.nick)

And if you want to send a private message to the bot's owner every time your
rule is triggered, you can use the bot's settings::

    bot.say('Hi owner!', bot.settings.core.owner)

.. note::

    The ``say`` method sends a ``PRIVMSG`` command to the IRC server. To send
    a ``NOTICE`` command instead, you need to use the
    :meth:`~sopel.bot.SopelWrapper.notice` method instead.


Make it reply
=============

Now maybe you want to make sure the user gets notified by the bot's message.
For that, you could use ``trigger.nick`` this way::

    bot.say('%s: ping!' % trigger.nick)

It'll work fine and it's a common usage. So common indeed that Sopel provides a
shortcut for that::

    bot.reply('ping!')

As with the ``say`` method seen above, the :meth:`~sopel.bot.SopelWrapper.reply`
method can send your message to another destination::

    bot.reply('ping!', '#another-channel')

Also, if you want to reply to **someone else**, you can do that too by using
the ``reply_to`` parameter::

    bot.reply('ping!', reply_to=bot.settings.core.owner)

In that example, we send a message on the same channel, with a highlight to the
bot's owner.

.. note::

    By default the ``reply`` method sends its message using a ``PRIVMSG``
    command. You can set ``notice=True`` as argument to make it use a
    ``NOTICE`` command instead::

        bot.reply('ping!', notice=True)


Make it act
===========

Besides talking, the bot can also **act**:

* to :meth:`~sopel.bot.Sopel.join` a channel,
* or to :meth:`~sopel.bot.Sopel.part` from it,
* and even to :meth:`~sopel.bot.Sopel.quit` the server,

Oh, and let's not forget about ``/me does something``, which can be done with
the :meth:`~sopel.bot.SopelWrapper.action` method::

    bot.action('does something')


Do it with style
================

.. Custom role definitions to apply custom style to inline text

.. role:: red
    :class: red

.. role:: boldred
    :class: bold red

.. role:: underline
    :class: underline

.. role:: strike
    :class: strike

.. role:: bolditalic
    :class: bold italic

.. role:: spoiler
    :class: spoiler


When the bot talks, replies, or acts, it can do so with style: colors,
**bold**, *italic*, :underline:`underline`, :strike:`strikethrough`, or
``monospace``. IRC formatting works with control codes, bytes you can use to
tell IRC clients how to display some part of the text.

.. seealso::

    If you want to know more about IRC formatting in general and some of its
    limitations, `the modern IRC documentation`__ may be of interest to you.

    .. __: https://modern.ircdocs.horse/formatting.html

However, dealing with control codes yourself is not the most dev-friendly
approach, hence the :mod:`sopel.formatting` module. It contains various
functions to help you create styled text.

Text styles
-----------

Let's dive into examples, starting with :func:`~sopel.formatting.bold` text::

    from sopel import formatting

    bot.say(formatting.bold('This is some bold text!'))

This will output a line like this:

    <Sopel> **This is some bold text!**

You can use them with Python string formatting::

    emphasis = formatting.bold('important')
    bot.say('And here is the %s part.' % emphasis)

To get that kind of output:

    <Sopel> And here is the **important** part.

And you can use multiple style functions together, for example with the
:func:`~sopel.formatting.italic` function::

    word = formatting.italic('very')
    emphasis = formatting.bold('%s important' % word)
    bot.say('And here is the %s part.' % emphasis)

To get a result that looks like this:

    <Sopel> And here is the :bolditalic:`very` **important** part.

Colored styles
--------------

Colorized text is a bit more complicated, and Sopel tries to provide helpful
functions and constants for that: the :func:`~sopel.formatting.color` function
and the :class:`~sopel.formatting.colors` class.

The ``color`` function takes a line of text and a foreground color. It also
accepts an optional background color that uses the same color codes. The color
codes are listed by the ``colors`` class, and can be used like this::

    bot.say(formatting.color('Red text.', formatting.colors.RED))

The above example should produce this output:

    <Sopel> :red:`Red text.`

You can combine colors and styles, like this::

    big = formatting.color(
        formatting.bold('WARNING'), formatting.colors.RED)
    small = formatting.italic('warning')
    bot.say('[%s] This is a %s.' % (big, small))

So you get a similar result as:

    <Sopel> [:boldred:`WARNING`] This is a *warning*.

If you want to prevent spoilers, you could be tempted to take advantage of
the background color::

    spoiler = formatting.color(
        'He was the killer.',
        formatting.colors.BLACK,
        formatting.colors.BLACK,
    )
    bot.say(spoiler)

And expect this (you need to select the text to read it):

    <Sopel> :spoiler:`He was the killer.`

Note that not all combinations of foreground and background colors are happy
ones, and you should be mindful of using too many unnecessary colors.


Channels & users
================

Knowing how to talk is good for a bot, but you may be wondering what the bot
knows about the channels and their users. For that, you can use the bot's
:attr:`~sopel.bot.Sopel.channels` attribute.

For example, to list all channels the bot is in::

    for name, channel in bot.channels.items():
        # do something with the name and the channel

.. note::

    Sopel doesn't know about channels it didn't join first, and it forgets
    everything about a channel when it leaves.

Getting a channel's information
-------------------------------

To get a channel's information, you need to know its name, with its channel
prefix (usually ``#``), such as this::

    channel = bot.channels['#channel_name']

With the ``trigger`` object, you can also access the channel object directly
(assuming the message comes from a channel, which you should check first)::

    channel = bot.channels[trigger.sender]

The ``channel`` object is an instance of :class:`~sopel.tools.target.Channel`,
which provides the following information:

* its :attr:`~sopel.tools.target.Channel.name`
* its :attr:`~sopel.tools.target.Channel.topic`
* its :attr:`~sopel.tools.target.Channel.users`
* and its users' :attr:`~sopel.tools.target.Channel.privileges`

.. note::

    To check if a message comes from a channel, you have two options:

    1. use the :func:`~sopel.plugin.require_chanmsg` decorator on your plugin
       callable
    2. use an ``if`` block in your function to check
       :attr:`trigger.sender <sopel.trigger.Trigger.sender>`::

           if not trigger.sender.is_nick():
               # this trigger is from a channel

       See :meth:`Identifier.is_nick() <sopel.tools.identifiers.Identifier.is_nick>`
       for more information.

Getting users in a channel
--------------------------

To get a list of users in a **channel**, you can use its
:attr:`~sopel.tools.target.Channel.users` attribute: this is a map of users you
can iterate over to get all the users::

    for nick, user in channel.users.items():
        # do something with the nick and the user

You can access one user in a channel with its nick::

    user = channel.users['Nickname']

With the ``trigger`` object, you can also access the user object directly::

    user = channel.users[trigger.nick]

About time
==========

Your plugin may want to display dates and times in messages. For that, you can
always count on the :mod:`datetime` built-in module. However, what if you would
like to respect the date-format for a given user or a given channel? Various
functions of :mod:`Sopel<sopel.tools.time>` can help you with that:

* :func:`~sopel.tools.time.get_timezone` will fetch the right timezone for you
* :func:`~sopel.tools.time.format_time` will format your aware datetime for you

Here is a full example of that::

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
----------------

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
--------------------

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
-----------

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
