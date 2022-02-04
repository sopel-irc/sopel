.. _plugin-anatomy:

===================
Anatomy of a plugin
===================

A Sopel plugin consists of a Python module containing one or more
``callable``\s. It may optionally also contain ``configure``, ``setup``, and
``shutdown`` hooks.


.. _plugin-anatomy-rules:

Defining rules
==============

The main goal of a Sopel plugin is to react to IRC messages. For that, Sopel
uses a :term:`Rule system`: plugins define rules, which Sopel loads, and then
Sopel triggers any matching rules for each message it receives.

Sopel identifies a callable as a rule when it has been decorated with any of
these decorators from :mod:`sopel.plugin`:

* :term:`Generic rule`: :func:`~sopel.plugin.rule`,
  :func:`~sopel.plugin.find`, and :func:`~sopel.plugin.search` (and their lazy
  versions: :func:`~sopel.plugin.rule_lazy`, :func:`~sopel.plugin.find_lazy`,
  and :func:`~sopel.plugin.search_lazy`)
* :term:`Named rule`: :func:`~sopel.plugin.command`,
  :func:`~sopel.plugin.action_command`, and
  :func:`~sopel.plugin.nickname_command`
* :term:`URL callback`: :func:`~sopel.plugin.url` (and its lazy version,
  :func:`~sopel.plugin.url_lazy`)

Additionally, Sopel identifies a callable as a generic rule when these
decorators are used alone:

* event based rule: :func:`~sopel.plugin.event`
* CTCP based rule: :func:`~sopel.plugin.ctcp`

In that case, it will use a match-all regex (``r'.*'``)::

   from sopel import plugin

   @plugin.event('JOIN')
   def on_join(bot, trigger):
      pass

   # the above is equivalent to this:
   @plugin.rule(r'.*')
   @plugin.event('JOIN')
   def on_join(bot, trigger):
      pass

Channel vs. private messages
----------------------------

By default, :term:`rules <Rule>` can be triggered from a channel or a private
message. It is possible to limit that to either one of these options:

* channel only: :func:`sopel.plugin.require_chanmsg`
* private message only: :func:`sopel.plugin.require_privmsg`

Access right requirements
-------------------------

By default anyone can trigger a :term:`rule <Rule>`, and for some it might be
better to limit who can trigger them. There are decorators for that:

* :func:`sopel.plugin.require_account`: requires services/NickServ
  authentication; works only if the server implements modern IRC authentication
  (see also :attr:`Trigger.account <sopel.trigger.Trigger.account>` and
  the `account-tag`__ specification for more information)
* :func:`sopel.plugin.require_privilege`: requires a specific level of
  privileges in the channel; works only for channel messages, not private
  messages, and you probably want to use it with
  :func:`~sopel.plugin.require_chanmsg`
* :func:`sopel.plugin.require_admin`: only the bot's owner and its admins can
  trigger the rule
* :func:`sopel.plugin.require_owner`: only the bot's owner can trigger the rule

Sometimes it's not the channel privilege level of the user who triggers a
command that matters, but the **bot's** privilege level. For that, there are
two options:

* :func:`sopel.plugin.require_bot_privilege`: this decorator is similar to
  the ``require_privilege`` decorator, but it checks the bot's privilege level
  instead of the user's; works only for channel messages, not private messages;
  and you probably want to use it with the ``require_chanmsg`` decorator.
* :meth:`bot.has_channel_privilege() <sopel.bot.Sopel.has_channel_privilege>`
  is a method that can be used to check the bot's privilege level in a channel,
  which can be used in any callable.

.. __: https://ircv3.net/specs/extensions/account-tag-3.2

.. seealso::

   Read the :doc:`privileges` chapter for more information on how to manage
   privileges and access management in a plugin.

Rate limiting
-------------

All :term:`rules <Rule>` can have rate limiting with the
:func:`sopel.plugin.rate` decorator. Rate limiting means how often a rule can
be triggered. This is different from the flood protection logic, which is how
often Sopel can send messages to the network. By default, a rule doesn't have
any rate limiting.

There are three types of rate limiting:

* per-user: how often a rule triggers for each user
* per-channel: how often a rule triggers for a given channel
* globally: how often a rule triggers accross the whole network

Example::

   from sopel import plugin

   @plugin.rule(r'Ah[!?.]?')
   @plugin.rate(user=2)
   def you_said_ah(bot, trigger):
      bot.reply('Ha AH!')

A rule with rate-limiting can return :const:`sopel.plugin.NOLIMIT` to let the
user try again after a failed command, e.g. if a required argument is missing.

Bypassing restrictions
----------------------

By default, a :term:`Rule` will not trigger on messages from Sopel itself,
other users that are flagged as bots, or users who are
:ref:`ignored <Ignore User>` or :ref:`rate-limited <Rate limiting>`. In
certain cases, it might be desirable to bypass these defaults using one or
more of these decorators:

* :func:`sopel.plugin.allow_bots`: the rule will accept events from other
  users who are flagged as bots (like Sopel itself)
* :func:`sopel.plugin.echo`: the rule will accept Sopel's own output (e.g.
  from calls to :func:`bot.say() <sopel.bot.Sopel.say>`)
* :func:`sopel.plugin.unblockable`: the rule will ignore rate-limiting or
  nick/host blocks and always process the event

For example, Sopel itself uses the :func:`sopel.plugin.unblockable` decorator
to track joins/parts from everyone, always, so plugins can *always* access
data about any user in any channel.

.. important::

   The :func:`sopel.plugin.echo` decorator will send *anything* Sopel says
   (that matches the rule) to the decorated callable, *including output from
   the decorated callable*. Be careful not to create a feedback loop.

Rule labels
-----------

A rule has a label: it will be used for logging, documentation, and internal
manipulation. There are two cases to consider:

* :term:`Generic rules <Generic rule>` and :term:`URL callbacks <URL callback>`
  use their :term:`callable <Plugin callable>`'s name by default (i.e. the
  function's ``__name__``). This can be overridden with the
  :func:`sopel.plugin.label` decorator.
* A :term:`Named rule` is already named (by definition), so it uses its name
  directly as rule label. This can't be overridden by a decorator.

This label is particularly useful for bot owners who want to disable a rule in
a specific channel. In the following example, the ``say_hello`` rule from the
``hello`` plugin is disabled in the ``#rude`` channel:

.. code-block:: ini

   [#rude]
   disable_commands = {'hello': ['say_hello']}

The rule in question is defined by the ``hello`` plugin like so::

   @plugin.rule(r'hello!?', r'hi!?', r'hey!?')
   @plugin.label('say_hello')
   def handler_hello(bot, trigger):
      bot.reply('Ha AH!')


.. _plugin-anatomy-callables:

Plugin callables
================

When a message from the IRC server matches a :term:`Rule`, Sopel will execute
its attached :term:`callable <Plugin callable>`. All plugin callables follow
the same interface:

.. py:function:: plugin_callable(bot, trigger)

   :param bot: wrapped bot instance
   :type bot: :class:`sopel.bot.SopelWrapper`
   :param trigger: the object that triggered the call
   :type trigger: :class:`sopel.trigger.Trigger`

A callable must accept two positional arguments: a
:class:`bot <sopel.bot.SopelWrapper>` object, and a
:class:`trigger <sopel.trigger.Trigger>` object. Both are tied to the specific
message that matches the rule.

The ``bot`` provides the ability to send messages to the network (to say
something or to send a specific command such as ``JOIN``), and to check the
state of the bot such as its settings, memory, or database. It is a context
aware wrapper around the running :class:`~sopel.bot.Sopel` instance.

The ``trigger`` provides information about the line which triggered the rule
and this callable to be executed.

The return value of a callable is ignored unless it is
:const:`sopel.plugin.NOLIMIT`, in which case
:term:`rate limiting <Rate limiting>` will not be applied for that call.
(See :func:`sopel.plugin.rate`.)

.. note::

   Note that the name can, and should, be anything, and it doesn't have to be
   called ``plugin_callable``. At least, it should not be called ``callable``,
   since that is a :func:`Python built-in function <callable>`::

      from sopel import plugin

      @plugin.command('hello')
      def say_hello(bot, trigger):
         """Reply hello to you."""
         bot.reply('Hello!')


.. _plugin-anatomy-jobs:

Plugin jobs
===========

Another feature available to plugins is the ability to define
:term:`jobs <Plugin job>`. A job is a Python callable decorated with
:func:`sopel.plugin.interval`, which executes the callable
periodically on a schedule.

A job follows this interface:

.. py:function:: plugin_job(bot)

   :param bot: the bot instance
   :type bot: :class:`sopel.bot.Sopel`

.. note::

   Note that the name can be anything, and it doesn't have to be called
   ``plugin_job``::

      from sopel import plugin

      @plugin.interval(5)
      def spam_every_5s(bot):
          if "#here" in bot.channels:
              bot.say("It has been five seconds!", "#here")


.. important::

   A job may execute while the ``bot`` is **not** connected, and it must not
   assume any network access.



.. _plugin-anatomy-setup-shutdown:

Plugin setup & shutdown
=======================

When loading and unloading plugins, a plugin can perform setup and shutdown
actions. For that purpose, a plugin can define optional functions named
``setup`` and ``shutdown``. There can be one and only one function with each
name for a plugin.

Setup
-----

The ``setup`` function must follow this interface:

.. py:function:: setup(bot)

   :param bot: the bot instance
   :type bot: :class:`sopel.bot.Sopel`

This function is optional. If it exists, it will be called while the plugin is
being loaded. The purpose of this function is to perform whatever actions are
needed to allow a plugin to do its work properly (e.g, ensuring that the
appropriate configuration variables exist and are set). Note that this normally
occurs prior to connection to the server, so the behavior of the messaging
functions on the :class:`sopel.bot.Sopel` object it's passed is undefined and
they are likely to fail.

Throwing an exception from this function will stop Sopel from loading the
plugin, and none of its :term:`rules <Rule>` or :term:`jobs <Plugin job>` will
be registered. The exception will be caught, an error message logged, and Sopel
will try to load the next plugin.

This is useful when requiring the presence of configuration values (by raising
a :exc:`~sopel.config.ConfigurationError` error) or making other environmental
requirements (dependencies, file/folder access rights, and so on).

The bot will not continue loading plugins or connecting during the execution of
this function. As such, an infinite loop (such as an unthreaded polling loop)
will cause the bot to hang.

Shutdown
--------

The ``shutdown`` function must follow this interface:

.. py:function:: shutdown(bot)

   :param bot: the bot instance
   :type bot: :class:`sopel.bot.Sopel`

This function is optional. If it exists, it will be called while the bot
is shutting down. Note that this normally occurs after closing connection
to the server, so the behavior of the messaging functions on the
:class:`bot <sopel.bot.Sopel>` object it's passed is undefined and they are
likely to fail.

The purpose of this function is to perform whatever actions are needed to allow
a plugin to properly clean up after itself (e.g. ensuring that any temporary
cache files are deleted).

The bot will not continue notifying other plugins or continue quitting during
the execution of this function. As such, an infinite loop (such as an
unthreaded polling loop) will cause the bot to hang.

.. versionadded:: 4.1


.. _plugin-anatomy-config:

Plugin configuration
====================

A plugin can define and use a configuration section. By subclassing
:class:`sopel.config.types.StaticSection`, it can define the options it uses
and may require. Then, it should add this section to the bot's settings::

   from sopel.config import types

   class FooSection(types.StaticSection):
       bar = types.ListAttribute('bar')
       fizz = types.ValidatedAttribute('fizz', bool, default=False)

   def setup(bot):
      bot.settings.define_section('foo', FooSection)

This will allow the bot to properly load this part of the configuration file:

.. code-block:: ini

   [foo]
   bar =
      spam
      eggs
      bacon
   fizz = yes

.. seealso::

   The :meth:`~sopel.config.Config.define_section` method to define a new
   section so the bot can parse it properly.

Configuration wizard
--------------------

When the owner sets up the bot, Sopel provides a configuration wizard. When a
plugin defines a ``configure`` function, the user will be asked if they want
to configure said plugin, and if yes, this function will execute.

The ``configure`` function must follow this interface:

.. py:function:: configure(settings)

   :param settings: the bot's configuration object
   :type settings: :class:`sopel.config.Config`

Its intended purpose is to use the methods of the passed
:class:`sopel.config.Config` object in order to create the configuration
variables it needs to work properly.

.. versionadded:: 3.0

Example::

   def configure(config):
      config.define_section('foo', FooSection)
      config.foo.configure_setting('bar', 'What do you want?')
      config.foo.configure_setting('fizz', 'Do you fizz?')

.. note::

   The ``configure`` function is called only from the command line, and
   network access must not be assumed.

   This process doesn't call the bot's ``setup`` or ``shutdown`` functions, so
   this function **must** define the configuration section it wants to use.

.. seealso::

   The :meth:`~sopel.config.Config.define_section` method to define a new
   section, and the :meth:`~sopel.config.types.StaticSection.configure_setting`
   method to prompt the user to set an option.
