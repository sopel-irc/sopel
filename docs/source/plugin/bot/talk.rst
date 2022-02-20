
============
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
:class:`sopel.tools.identifiers.Identifier` that can represent a channel or a
user::

    from sopel.tools.identifiers import Identifier

    channel = Identifier('#channel')
    nick = Identifier('Nickname')
    bot.say('Hello channel!', channel)
    bot.say('Hello user!', nick)

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

As with the ``say`` method seen above, the
:meth:`~sopel.bot.SopelWrapper.reply` method can send your message to another
destination::

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
