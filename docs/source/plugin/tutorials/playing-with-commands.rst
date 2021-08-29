=====================
Playing with commands
=====================

Now that you have started :doc:`your first plugin <first-plugin>`, maybe you
want to write a more interesting command than the basic ``.hello`` one. Not
that there is anything wrong with that command! The emoticons plugin is
composed of commands like this one::

    @plugin.command('shrug')
    @plugin.action_command('shrugs')
    def shrug(bot, trigger):
        bot.say('¯\\_(ツ)_/¯')

Which is one of the maintainers' favorite commands to use. However, let's see
if we can do something a bit more *complex* than that.


Greeting a user by their name
=============================

Have you noticed that a :ref:`plugin callable <Plugin callables>` takes **two
arguments?** The first one is the ``bot``, an instance of Sopel that you can
use to :doc:`interact with the bot </plugin/bot>`.

In the previous tutorial, we used ``bot.reply``, which is convenient when
responding directly to a user, but not always what you want. Maybe you want the
bot to say something more complex::

    <YourNick> .hello
    <Sopel> Hello YourNick, have a nice day!

For that, you need **the second argument**: the ``trigger``. It is an object
with information about the message that triggered your
callable, such as the **message** itself, the **channel**, the type of message,
etc.—and what we need for now is the
:attr:`trigger.nick <sopel.trigger.Trigger.nick>` attribute::

    from sopel import plugin

    @plugin.command('hello')
    def hello(bot, trigger):
        """Say Hello <user>, have a nice day!"""
        bot.say(f'Hello {trigger.nick}, have a nice day!')

.. important::

    If you want to test this with your bot, and your bot is already running,
    restart the bot so it will load the new version of your plugin.

.. seealso::

    You can learn much more about the :class:`trigger <sopel.trigger.Trigger>`
    object by reading its documentation.


Command with arguments
======================

The trigger object can do much more for you: if a user adds arguments to the
command, like ``.hello morning``, you can detect and use that argument::

    from sopel import plugin

    @plugin.command('hello')
    def hello(bot, trigger):
        """Say Hello <user>, have a nice day!"""
        # group 1 is the name of the command that was triggered
        # group 2 is the entire rest of the message
        # groups 3 to 6 are the first, second, third, and fourth command arg
        when = trigger.group(3)
        # select a different greeting depending on when
        greeting = {
            'morning': 'and good morning!',
            'noon': 'are you having lunch?',
            'night': 'I hope it was a good day!',
            'evening': 'good evening to you!'
        }.get(when, 'have a nice day!')  # default to "nice day"
        # say hello
        bot.say(f'Hello {trigger.nick}, {greeting}')

Now the command will be able to react a bit more to your user::

    <YourNick> .hello morning
    <Sopel> Hello YourNick, and good morning!
    <YourNick> .hello noon
    <Sopel> Hello YourNick, are you having lunch?

How does that work? Well, the short version is that Sopel uses regex
(`REGular EXpressions`__) to match a message to a plugin callable, and the
``trigger`` object exposes the match result.

.. seealso::

    You can learn much more about the :class:`~sopel.plugin.command` decorator
    by reading its documentation.

.. note::

    In the case of a command, the regex is entirely managed by Sopel itself,
    while the generic :func:`@plugin.rule <sopel.plugin.rule>` decorator
    allows you to define your own regex.

.. __: https://en.wikipedia.org/wiki/Regular_expression


And... action!
==============

Some users say ``.hello`` out loud, and others will say it with an action. How
do you react to these? Let's go back to the example of the ``shrug`` command::

    @plugin.command('shrug')
    @plugin.action_command('shrugs')
    def shrug(bot, trigger):
        bot.say('¯\\_(ツ)_/¯')

Notice that it also uses a second decorator, ``action_command('shrugs')``,
with a different name. How does that work?

Sopel knows how to register the same plugin callable for different types of
trigger, so both ``.shrug`` and ``/me shrugs`` work. For example, you could do
this for your hello plugin::

    @plugin.command('hello')
    @plugin.action_command('waves')
    def hello(bot, trigger):
        ...

And so, in chat, you will see that::

    <YourNick> .hello
    <Sopel> Hello YourNick, have a nice day!
    * YourNick waves
    <Sopel> Hello YourNick, have a nice day!


Summing it up
=============

In this tutorial, we talked briefly about ``bot.say()`` and ``bot.reply()``,
and explored a few more ways to :doc:`interact with the bot </plugin/bot>`.

We saw that you can use the :class:`trigger <sopel.trigger.Trigger>` argument
of a plugin callable to get more information on the message that triggered the
command. Don't hesitate to read the documentation of that object and discover
all its properties.

We also saw that you have more ways to trigger a callable, and you can read
more in :doc:`the plugin anatomy chapter </plugin/anatomy>` (see
:ref:`how to define rules <plugin-anatomy-rules>`, in particular).

Throughout this tutorial, we also linked to various sections of the
documentation: as we improve the documentation with every release, we invite
you to read it to discover more features of Sopel and what is available to you
as a plugin author.

And if you have come this far, thank you for reading this!
