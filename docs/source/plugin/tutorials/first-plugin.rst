=================
Your first plugin
=================

Sopel's most interesting features come from its plugins, either published by
Sopel's developers or by third-party developers, and you can write your own
plugins. But where do you start?

Here is a very short example of code for your first plugin that contains one
and only one command::

    from sopel import plugin

    @plugin.command('hello')
    def hello(bot, trigger):
        """Reply with Hello!"""
        bot.reply('Hello!')

You can put this code in a Python file, placed into your Sopel plugin
directory, such as ``~/.sopel/plugins/myplugin.py``. Once this is done, you can
check if the bot can see the plugin, by using the ``sopel-plugins`` command
line tool::

    $ sopel-plugins show myplugin
    Plugin: myplugin
    Status: enabled
    Type: python-file
    Source: /path/to/home/.sopel/plugins/myplugin.py
    Label: myplugin plugin
    Loaded successfully
    Setup: no
    Shutdown: no
    Configure: no

Notice how the filename (without the extension) is also the name of the plugin:
if you were to name your file ``hello.py``, it would be the ``hello`` plugin.

If ``status`` is not ``enabled``, you can enable your plugin with
``sopel-plugins enable hello``.

Then, you can start your bot and trigger the command like this::

    <YourNick> .hello
    <Sopel> YourNick: Hello!

And voilà! This is your first plugin. Sure, it doesn't do much, and yet it uses
the key elements that you'll need to understand to write your own plugins.

.. seealso::

    To interact with the list of plugins installed, read the documentation
    of :ref:`sopel-plugins`.
