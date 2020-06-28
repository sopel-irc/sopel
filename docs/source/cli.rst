=======================
Command Line Interfaces
=======================

Once installed, you can configure and start a Sopel IRC Bot instance::

   $ sopel configure
   # ... configuration wizard ...
   $ sopel start

The ``configure`` subcommand will run a brief configuration wizard to set up
the basic options: the bot's nick, its admin's nick, the IRC server to connect
to, and channels to join. By default, it creates the file
``~/.sopel/default.cfg`` (creating the homedir directory if necessary.)

Once this is done, the ``start`` subcommand runs the bot, using this
configuration file unless one is provided using the ``-c``/``--config`` option.

Certain command-line options can be passed via environment variables. Also see
the :ref:`section on environment variables <Supported environment variables>`
for more possibilities.

.. contents::
    :local:
    :depth: 1


The ``sopel`` command
=====================

.. autoprogram:: sopel.cli.run:build_parser()
    :prog: sopel
    :maxdepth: 1

.. autoprogram:: sopel.cli.run:build_parser()
    :prog: sopel
    :start_command: start

.. autoprogram:: sopel.cli.run:build_parser()
    :prog: sopel
    :start_command: stop

.. autoprogram:: sopel.cli.run:build_parser()
    :prog: sopel
    :start_command: restart

.. autoprogram:: sopel.cli.run:build_parser()
    :prog: sopel
    :start_command: configure


The ``sopel-config`` command
============================

.. versionadded:: 7.0

   The command ``sopel-config`` and its subcommands have been added in
   Sopel 7.0.

.. autoprogram:: sopel.cli.config:build_parser()
    :prog: sopel-config


The ``sopel-plugins`` command
=============================

.. versionadded:: 7.0

   The command ``sopel-plugins`` and its subcommands have been added in
   Sopel 7.0.

.. autoprogram:: sopel.cli.plugins:build_parser()
    :prog: sopel-plugins


Supported environment variables
===============================


``SOPEL_CONFIG``
----------------

This environment variable replaces the built-in default config name (which is,
confusingly, also "default") if set. It's interpreted in the same way as the
``-c``/``--config`` option accepted by most CLI commands described above.

.. versionadded:: 7.0


``SOPEL_CONFIG_DIR``
--------------------

This environment variable replaces the default directory in which Sopel
searches for config files. It's interpreted in the same way as the
``--config-dir`` option accepted by most CLI commands described above.

.. versionadded:: 7.1


Overriding individual settings
------------------------------

Whenever a setting is accessed, Sopel looks for a matching environment
variable. If found, the environment variable's value (even if it's empty)
overrides the value from Sopel's config file.

The variable name Sopel looks for is structured as follows:

  * ``SOPEL_`` prefix (to prevent collisions with other programs)
  * The section name in UPPERCASE, e.g. ``CORE`` or ``PLUGIN_NAME``
  * ``_`` as separator
  * The setting name in UPPERCASE, e.g. ``NICK`` or ``API_KEY``

For example, take this stripped-down config file:

.. code-block:: ini

    [core]
    nick = ConfigFileNick
    host = chat.freenode.net

    [plugin_name]
    api_key = abad1dea

Sopel would take the nickname ``ConfigFileNick`` when connecting to IRC at
``chat.freenode.net``, and the ``plugin_name`` plugin would use the API key
``abad1dea`` when communicating with its remote service.

However, by setting the environment variables:

.. code-block:: shell

    SOPEL_CORE_NICK=EnvVarNick
    SOPEL_PLUGIN_NAME_API_KEY=1337c0ffee9001

Sopel would take the nickname ``EnvVarNick`` when connecting to IRC (still at
``chat.freenode.net``; that value isn't overridden or lost), and the
``plugin_name`` plugin would use the API key ``1337c0ffee9001``, instead.

.. versionadded:: 7.0

.. note::

   Any ``_`` character in the section or setting name also appears in the
   environment variable name. It's therefore *theoretically* possible for two
   plugins to have section and setting name pairs that both resolve to the same
   environment variable name, but in practice this is highly unlikely.

   However, should such a collision occur, please notify the main Sopel project
   *and* both plugin authors via any relevant communication channel(s).
