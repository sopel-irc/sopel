================
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
===============================

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
==========================

To get a list of users in a **channel**, you can use its
:attr:`~sopel.tools.target.Channel.users` attribute: this is a map of users you
can iterate over to get all the users::

    for nick, user in channel.users.items():
        # do something with the nick and the user

You can access one user in a channel with its nick::

    user = channel.users['Nickname']

With the ``trigger`` object, you can also access the user object directly::

    user = channel.users[trigger.nick]
