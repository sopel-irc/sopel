==============================
Configuration and plugin setup
==============================

Maybe you :doc:`played with commands <playing-with-commands>` for your
plugin and now you want to make your plugin configurable. If you run an
instance of Sopel yourself, you probably had to open and edit its
:doc:`configuration</run/configuration>` file.

Usually located in the ``.sopel/`` folder under your home directory, the
configuration file is an INI file with sections defined by Sopel's core and by
plugins. In this tutorial, let's see how to declare and use a configuration
section dedicated to your plugin.


Declaring your configuration
============================

To declare a configuration section, you must first create a subclass of
:class:`~sopel.config.types.StaticSection`, and define attributes::

    from sopel.config import types

    class MyPluginSection(types.StaticSection):
        fruits = types.ListAttribute('fruits')


Telling Sopel about it
======================

Now, having a class in your plugin doesn't achieve much: you need to tell the
bot about it by using the :meth:`~sopel.config.Config.define_section` method.
The best place to do so is in the :func:`setup` function hook of your plugin::

    def setup(bot):
        bot.settings.define_section('myplugin', MyPluginSection)

This way, you tell Sopel that the ``[myplugin]`` section in the **configuration
file** is used by your plugin, and to parse this section Sopel must use your
class, i.e. ``MyPluginSection``.


Using your section
==================

Now that you have told Sopel about your custom section, you can add the
following lines in your configuration file:

.. code-block:: ini

    [myplugin]
    fruits =
        banana
        apple
        peach
        strawberry

And Sopel will expose that for you through ``bot.settings.myplugin``. For
example, you can write this command::

    import random

    @plugin.command('fruits')
    def fruits(bot, trigger):
        fruit = random.choice(bot.settings.myplugin.fruits)
        bot.say(f'I want a {fruit}!')

And whenever someone triggers this command, the bot will say that it wants one
of the configured fruits. If you want to list 50 fruits or only 2 is up to you,
and to the bot owners who will install your plugin.


Putting everything together
===========================

We can combine all of this into one plugin file, located at the same place as
before (``~/.sopel/plugins/myplugin.py``, assuming the default location)::

    import random
    from sopel.config import types


    class MyPluginSection(types.StaticSection):
        """Declaration of your plugin's configuration."""
        fruits = types.ListAttribute('fruits')


    def setup(bot):
        """Telling the bot about the plugin's configuration."""
        bot.settings.define_section('myplugin', MyPluginSection)


    @plugin.command('fruits')
    def fruits(bot, trigger):
        """Using the plugin's configuration in our command."""
        fruit = random.choice(bot.settings.myplugin.fruits)
        bot.say(f'I want a {fruit}!')

As you can see, there are **several steps** when it comes to configuration:

* creating a class to represent your configuration section
* telling Sopel about it in a ``setup`` function
* using your plugin's configuration in your plugin

Sopel tries to make it as straightforward and flexible as possible for you to
declare and to setup your plugin configuration, and you can read more about
:ref:`plugin configuration <plugin-anatomy-config>`,
which includes a section about the configuration wizard as well. You can also
see Sopel's own configuration in
:doc:`the configuration chapter </run/configuration>`.

Once you are familiar with the concept, you can also read deeper into the
reference documentation for the :mod:`sopel.config` module.
