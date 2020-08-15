=====================
Interact with the bot
=====================

Once a :term:`Rule` has been triggered, it's time to do whatever the plugin is
supposed to do. Thanks to the ``bot`` parameter, you can make the bot talk:
say something in a channel, reply to someone, send a notice, or join a channel.

.. contents::
   :local:
   :depth: 2


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

    bot.say('The bot is now talking!, '#private-channel')

Instead of a string, you can use a instance of :class:`sopel.tools.Identifier`.

If you want to reply to a user in a private message, you can use the trigger's
:attr:`~sopel.trigger.Trigger.nick` attribute as destination::

    bot.say('I reply in private message', trigger.nick)

And if you want to send a private message to the bot's owner every time your
rule is triggered, you can use the bot's settings::

    bot.say('Hi owner!', bot.settings.core.owner)

.. note::

    The ``say`` methods sends a ``PRIVMSG`` command to the IRC server. To send
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

As for the ``say`` method seen above, the :meth:`~sopel.bot.SopelWrapper.reply`
method can send your message to another destination::

    bot.reply('ping!', '#another-channel')

Also, if you want to reply to **someone else**, you can do that too by using
the ``reply_to`` parameter::

    bot.reply('ping!', reply_to=bot.settings.core.owner)

In that example, we send a message on the same channel, with a highlight to the
bot's owner.

.. note::

    By default the ``reply`` method sends its message using a ``PRIVMSG``
    command. You can set ``notice=True`` as argument to make it uses a
    ``NOTICE`` command instead::

        bot.reply('ping!', notice=True)


Make it act
===========

Beside talking, the bot can also **act**:

* to :meth:`~sopel.bot.Sopel.join` a channel,
* or to :meth:`~sopel.bot.Sopel.part` from it,
* and even to :meth:`~sopel.bot.Sopel.quit` the server,

Oh, and let's not forget about ``/me something something``, which can be done
with the :meth:`~sopel.bot.SopelWrapper.action` method::

    bot.action('something something')


Channels & users
================

Knowing how to talk is good for a bot, but you may be wondering what the bot
knows about the channels and their users. For that, you can use the bot's
:attr:`~sopel.bot.Sopel.channels` attribute. For example, to list all channels
the bot is in::

    for name, channel in bot.channels.items():
        # do something with the name and the channel

With the ``trigger`` object, you can also access the channel object directly
(granted the message comes from a channel, which you should check first)::

    channel = bot.channels[trigger.sender]

The ``channel`` object is an instance of :class:`sopel.tools.target.Channel`,
which provides the following information:

* its :attr:`~sopel.tools.target.Channel.name`
* its :attr:`~sopel.tools.target.Channel.topic`
* its :attr:`~sopel.tools.target.Channel.users`
* and its users' :attr:`~sopel.tools.target.Channel.privileges`

Using ``trigger.nick``, you can get the nick's profile and privileges in a
channel like this::

    user_privileges = channel.privileges[trigger.nick]
    user = channels.users[trigger.nick]

Then you can check if the user is voiced (mode +v) or not::

    from sopel import plugin

    if user_privileges & plugin.VOICED:
        # user is voiced
    elif user_privileges >= plugin.VOICED:
        # not voiced, but higher privileges
        # like plugin.HALFOP or plugin.OP
    else:
        # no privilege
