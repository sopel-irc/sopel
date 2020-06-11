================
Plugin structure
================

.. contents::
   :local:
   :depth: 1

Anatomy of a plugin
===================

A Sopel plugin consists of a Python module containing one or more
``callable``\s. It may optionally also contain ``configure``, ``setup``, and
``shutdown`` hooks.

.. py:function:: callable(bot, trigger)

    :param bot: the bot's instance
    :type bot: :class:`sopel.bot.SopelWrapper`
    :param trigger: the object that triggered the call
    :type trigger: :class:`sopel.trigger.Trigger`

    A callable is any function which takes as its arguments a
    :class:`sopel.bot.SopelWrapper` object and a :class:`sopel.trigger.Trigger`
    object, and is wrapped with appropriate decorators from
    :mod:`sopel.module`. The ``bot`` provides the ability to send messages to
    the network and check the state of the bot. The ``trigger`` provides
    information about the line which triggered this function to be called.

    The return value of these function is ignored, unless it is
    :const:`sopel.module.NOLIMIT`, in which case rate limiting will not be
    applied for that call.

    Note that the name can, and should, be anything - it doesn't need to be
    called "callable"::

        from sopel import module

        @module.commands('hello')
        def say_hello(bot, trigger):
            """Reply hello to you."""
            bot.reply('Hello!')


.. py:function:: setup(bot)

    :param bot: the bot's instance
    :type bot: :class:`sopel.bot.Sopel`

    This is an optional function of a plugin, which will be called while the
    module is being loaded. The purpose of this function is to perform whatever
    actions are needed to allow a module to function properly (e.g, ensuring
    that the appropriate configuration variables exist and are set). Note that
    this normally occurs prior to connection to the server, so the behavior of
    the messaging functions on the :class:`sopel.bot.Sopel` object it's passed
    is undefined.

    Throwing an exception from this function (such as a
    :exc:`sopel.config.ConfigurationError`) will prevent any callables in the
    module from being registered, and provide an error message to the user.
    This is useful when requiring the presence of configuration values or
    making other environmental requirements.

    The bot will not continue loading modules or connecting during the
    execution of this function. As such, an infinite loop (such as an
    unthreaded polling loop) will cause the bot to hang.

.. py:function:: shutdown(bot)

    :param bot: the bot's instance
    :type bot: :class:`sopel.bot.Sopel`

    This is an optional function of a module, which will be called while the
    bot is quitting. Note that this normally occurs after closing connection
    to the server, so the behavior of the messaging functions on the
    :class:`sopel.bot.Sopel` object it's passed is undefined. The purpose of
    this function is to perform whatever actions are needed to allow a module
    to properly clean up (e.g, ensuring that any temporary cache files are
    deleted).

    The bot will not continue notifying other modules or continue quitting
    during the execution of this function. As such, an infinite loop (such as
    an unthreaded polling loop) will cause the bot to hang.

    .. versionadded:: 4.1

.. py:function:: configure(config)

    :param bot: the bot's configuration object
    :type bot: :class:`sopel.config.Config`

    This is an optional function of a module, which will be called during the
    user's setup of the bot. It's intended purpose is to use the methods of the
    passed :class:`sopel.config.Config` object in order to create the
    configuration variables it needs to function properly.

    .. versionadded:: 3.0


Callable decorators
===================

.. automodule:: sopel.module
   :members:


Internal machinery
==================

.. important::

   This section contains modules and classes used by Sopel internally. They are
   subject to rapid changes between versions. They are documented here for
   completeness, and for the aid of Sopel’s core development.

.. contents::
   :local:


sopel.plugins
-------------
.. automodule:: sopel.plugins
   :members:

sopel.plugins.handlers
----------------------
.. automodule:: sopel.plugins.handlers
   :members:

sopel.plugins.exceptions
------------------------
.. automodule:: sopel.plugins.exceptions
   :members:

sopel.plugins.rules
-------------------
.. automodule:: sopel.plugins.rules
   :members:
   :show-inheritance:

   .. autoclass:: AbstractRule
      :members:
      :undoc-members:

   .. autoclass:: NamedRuleMixin
      :members:
      :undoc-members:

sopel.loader
------------
.. automodule:: sopel.loader
   :members:
