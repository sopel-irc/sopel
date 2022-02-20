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

Manage channels
===============

Like any IRC client, Sopel uses IRC messages to join or leave channels, to kick
users or to set channel modes. It provides methods you can use to send those
commands:

* :meth:`bot.join() <sopel.irc.AbstractBot.join>`: to join a channel
* :meth:`bot.part() <sopel.irc.AbstractBot.part>`: to leave a channel
* :meth:`bot.kick() <sopel.irc.AbstractBot.kick>`: to kick a user from a
  channel (this may require some extra privileges)
* :meth:`bot.write() <sopel.irc.AbstractBot.write>`: to send any message to IRC

Join & Part
-----------

If you want the bot to join or leave a channel, the solution is
straightforward::

    bot.join('#channel_name')
    bot.part('#channel_name')

For example, you can recreate the ``.tmpjoin`` command like so::

    @plugin.commands('tmpjoin')
    @plugin.require_admin()
    def my_custom_join(bot, trigger):
        channel, key = trigger.group(3), trigger.group(4)
        if not channel:
            bot.reply('I need a channel to join.')
        else:
            bot.join(channel, password=key)

To use that command:

.. code-block:: irc

    <Admin> .tmpjoin #channel

And then the bot will send the following message:

.. code-block:: irc

    JOIN #channel

When the server replies to that message, Sopel will automatically update its
list of known channels and may send other IRC commands to know more about its
users. The ``part`` method works exactly like the ``join`` method, but the bot
will leave the channel instead of joining it.

.. note::

    Both ``join`` and ``part`` methods send an IRC command to the server, but they
    don't update the bot's configuration file: when the bot restarts, unless
    :attr:`bot.settings.core.channels <sopel.config.core_section.CoreSection.channels>`
    has been updated manually, the bot won't remember the channels joined or
    left from these methods alone.

.. warning::

    You should always consider security when allowing the bot to join or leave
    a channel: in this example, only admins are allowed to use the ``.tmpjoin``
    command thanks to the :func:`~sopel.plugin.require_admin` decorator.

Kick users
----------

Sometimes you don't want a user in your channel. The IRC message would be:

.. code-block:: irc

    KICK #channel xnaas :You know why!

You can use :meth:`bot.kick() <sopel.irc.AbstractBot.kick>` to achieve the same
result::

    bot.kick('xnaas', '#channel', text='You know why!')

.. warning::

    Be responsible: you should ensure that your plugin limits the potential for abuse as much as
    possible. For example, consider limiting who can trigger a kick by checking
    :doc:`privileges </plugin/privileges>`, and/or limiting kicks to an
    explicit set of reasons.
