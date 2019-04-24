Command Line Interfaces
=======================

Once installed, you can configure and start a Sopel IRC Bot instance::

   $ sopel configure
   # ... configuration wizard ...
   $ sopel start

The ``configure`` sub-command will run a brief configuration wizard to set up
the basic options: the bot's nick, its admin's nick, the server and channels
to join. By default, it creates the file ``~/.sopel/default.cfg``; creating
the homedir directory if necessary.

Once this is done, the ``start`` sub-command run the bot, using this
configuration file unless one is provided using the ``-c/--config`` options.


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
