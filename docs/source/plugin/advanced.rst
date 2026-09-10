.. _plugin-advanced:

======================
Advanced Tips & Tricks
======================

Now that you know the basics about plugins, you may have more questions, or
you might have a specific need but can't quite grasp how to implement it.
After all, this documentation alone can't cover every possible case!

In this chapter, we'll try to share the many tips and tricks both core
developers and plugin authors have found over time.

If something is not in here, feel free to ask about it on our IRC channel, or
maybe open an issue with the solution if you devise one yourself.


Running a function on a schedule
================================

Sopel provides the :func:`@plugin.interval <sopel.plugin.interval>` decorator
to run plugin callables periodically, but plugin developers semi-frequently ask
how to run a function at the same time every day/week.

Integrating this kind of feature into Sopel's plugin API is trickier than one
might think, and it's actually simpler to have plugins just use a library like
`schedule`__ directly::

    import schedule

    from sopel import plugin


    def scheduled_message(bot):
        bot.say("This is the scheduled message.", "#channelname")


    def setup(bot):
        # schedule the message at midnight every day
        schedule.every().day.at('00:00').do(scheduled_message, bot=bot)


    @plugin.interval(60)
    def run_schedule(bot):
        schedule.run_pending()

As long as the ``bot`` is passed as an argument, the scheduled function can
access config settings or any other attributes/properties it needs.

Multiple plugins all setting up their own checks with ``interval`` naturally
creates *some* overhead, but it shouldn't be significant compared to all the
other things happening inside a Sopel bot with numerous plugins.

.. __: https://pypi.org/project/schedule/


Restricting commands to certain channels
========================================

Allowing games, for example, to be run only in specific channels is a
relatively common request, but a difficult feature to support directly in
Sopel's plugin API. Fortunately it is fairly trivial to build a custom
decorator function that handles this in a configurable way.

Here is a sample plugin that defines such a custom decorator, plus the
scaffolding needed :ref:`for the plugin to pull its list of channels from the
bot's settings <plugin-anatomy-config>`::

    import functools

    from sopel import plugin
    from sopel.config import types


    class MyPluginSection(types.StaticSection):
        allowed_channels = types.ListAttribute('allowed_channels', default=['#botspam'])


    def setup(bot):
        bot.settings.define_section('myplugin', MyPluginSection)


    def my_plugin_require_channel(func):
        @functools.wraps(func)
        def decorated(bot, trigger):
            if trigger.sender not in bot.settings.myplugin.allowed_channels:
                return
            return func(bot, trigger)
        return decorated


    @plugin.command('command_name')
    @plugin.require_chanmsg
    @my_plugin_require_channel
    def my_command(bot, trigger):
        bot.say('This is the good channel.')

.. important::

    When using this example in your own plugin code, remember to change
    ``myplugin`` to a section name appropriate for your plugin. It is also a
    good idea to rename the ``MyPluginSection`` class accordingly.

.. note::

    The example here services the most common situations we have seen users
    ask for help with on IRC. This kind of decorator could be written in many
    different ways. Implementation of more complex approaches is left as an
    exercise for the reader.


Tracking events before/after the bot did
========================================

When a user joins a channel, or quits the server, Sopel will automatically
update the information about said user and channel. For example, when they
join a channel, that information is recorded in
:attr:`bot.channels <sopel.bot.Sopel.channels>` by adding a new
:class:`User <sopel.tools.target.User>` object to the correct
:attr:`channel.users <sopel.tools.target.Channel.users>` dict.

That's all good until you want to do something before or after the change has
been recorded by Sopel: you need to be careful how you declare your rules.

Before event
------------

To handle an event before Sopel records any change, you should use these
decorators together::

    @plugin.event('event-name')             # replace by your event
    @plugin.priority(plugin.Priority.HIGH)  # ensure execution before Sopel
    @plugin.thread(False)                   # ensure sequential execution
    @plugin.unblockable                     # optional
    def before_event_name(bot, trigger):
        # the bot is not updated yet

Requesting high priority and sequential (unthreaded) execution together ensures
that anything you do in your callable will be done **before** Sopel updates its
state: users won't be added or removed yet on JOIN/QUIT.

After event
-----------

To handle an event after Sopel recorded any change, you should use these
decorators together::

    @plugin.event('event-name')             # replace by your event
    @plugin.priority(plugin.Priority.LOW)   # ensure execution after Sopel
    @plugin.thread(False)                   # optional
    @plugin.unblockable                     # optional
    def after_event_name(bot, trigger):
        # the bot has been updated already

The low priority is enough to ensure that anything you do in your callable will
be done **after** Sopel updated its state: users won't exist anymore after
a QUIT/PART event, and they will be available after a JOIN event.

Note that you don't specifically need to use ``@plugin.thread(False)``, but
it is still recommended to prevent any race condition.


Re-using commands from other plugins
====================================

Because plugins are just Python modules it is possible to import functionality
from other plugins, including commands. For example, this can be used to add
an alias for an existing command::

    from sopel import plugin

    import sopel_someplugin as sp

    @plugin.command("new_command")
    @plugin.output_prefix(sp.PLUGIN_OUTPUT_PREFIX)
    def someplugin_alias(bot, trigger):
        sp.plugin_command(bot, trigger)

.. warning::

    Any callables imported from other plugins will be treated as if they were
    exposed in the current plugin. This can lead to duplication of plugin
    rules. For the most predictable results, import the other plugin as a
    module rather than unpacking its callables using a ``from`` import.

.. warning::

    Some plugins may not be as easy to import as the example shown here.
    For example, a :term:`Single file plugin` may not be available on
    ``sys.path`` without extra handling not shown here.


Managing Capability negotiation
===============================

`Capability negotiation`__ is a feature of IRCv3 that allows a server to
advertise a list of optional capabilities, and allows its clients to request
such capabilities. You can see that as feature flags, activated by the client.

Capability negotiation takes place after:

* connecting to the IRC server
* client's identification (``USER`` and ``NICK``)

And before:

* the ``RPL_WELCOME`` event (001)
* ``ISUPPORT`` messages
* client's authentication (except for SASL, which occurs in the capability
  negotiation phase)

.. warning::

    This is a very advanced feature, and plugin authors should understand how
    capability negotiation works before using it. Even if Sopel tries to make
    it as simple as possible, plugin authors should be aware of the known
    limitations and possible caveats.

.. __: https://ircv3.net/specs/extensions/capability-negotiation

Declaring requests: the ``capability`` decorator
------------------------------------------------

In :mod:`sopel.plugin` there is an advanced :func:`~sopel.plugin.capability`
decorator. This decorator returns an instance of
:class:`~sopel.plugins.callables.Capability` that declares a capability request
and an optional handler to run after the capability is acknowledged or denied
by the server::

    """Sample plugin file"""

    from sopel import plugin

    # this will register a capability request
    CAP_ACCOUNT_TAG = plugin.capability('account-tag')

    # this will work as well
    @plugin.capability('message-prefix')
    def cap_message_prefix(cap_req, bot, acknowledged):
        # do something if message-prefix is ACK or NAK
        ...

.. autofunction:: sopel.plugin.capability

Working with capabilities
-------------------------

A plugin that requires capabilities, or that can enhance its features with
capabilities, should rely on
:attr:`bot.capabilities <sopel.irc.AbstractBot.capabilities>`'s methods'::

    @plugin.command('mycommand')
    def mycommand_handler(bot, trigger):
        if bot.capabilities.is_enabled('cap1'):
            # be fancy with enhanced capabilities
        else:
            # stick to the basics

The :meth:`~sopel.irc.capabilities.Capabilities.is_enabled` method in
particular is the most interesting, as it allows a plugin to always know if a
capability is available or not.

.. note::

   Capability negotiation happens after the bot has loaded its plugins and
   after the socket connection. As a result, it is not possible to know the
   supported and enabled capabilities in the ``setup`` plugin hook.


Ending negotiations
-------------------

Sopel automatically sends a ``CAP END`` message when all requests are handled.
However in some cases, a plugin author may need to delay the end of CAP
negotiation to perform an action that must be done first. In that case, a
plugin must return
:attr:`~sopel.plugins.callables.CapabilityNegotiation.CONTINUE` in its callback.

This is the case for SASL authentication, as seen in the ``coretasks``
internal plugin that manages that:

.. code-block:: python
    :emphasize-lines: 8

    @plugin.capability('sasl')
    def cap_sasl_handler(cap_req, bot, acknowledged):
        # ... <skip for readability> ...
        bot.write(('AUTHENTICATE', mech))

        # If we want to do SASL, we have to wait before we can send CAP END.
        # So if we are, wait on 903 (SASL successful) to send it.
        return plugin.CapabilityNegotiation.CONTINUE

Later on, the plugin uses the
:meth:`~sopel.bot.Sopel.resume_capability_negotiation` method to tell the bot
that the request is complete, and the bot will send the ``CAP END``
automatically:

.. code-block:: python
    :emphasize-lines: 8

    @plugin.event(events.RPL_SASLSUCCESS)
    @plugin.thread(False)
    @plugin.unblockable
    @plugin.priority(plugin.Priority.MEDIUM)
    def sasl_success(bot: SopelWrapper, trigger: Trigger):
        """Resume capability negotiation on successful SASL auth."""
        LOGGER.info("Successful SASL Auth.")
        bot.resume_capability_negotiation(
            cap_sasl_handler.cap_req,
            'coretasks'
        )

.. important::

    Plugin callables that modify the bot's capability negotiation state should
    always use ``@plugin.thread(False)`` and ``@plugin.unblockable`` to prevent
    unwanted race conditions.
