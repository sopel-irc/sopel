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
