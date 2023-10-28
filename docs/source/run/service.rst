====================
Running as a service
====================

Once you have your bot set up, you will probably want it to run forever in the
background of your system. While there are many ways to do so, there are a few
steps and requirements that remain the same to properly run Sopel as a service.


Requirements to run a service
=============================

Sopel needs the following:

* a non-root user to run as
* read/write access to its configuration file
* a writable pid directory
  (:attr:`~sopel.config.core_section.CoreSection.pid_dir`)
* a writable logs directory
  (:attr:`~sopel.config.core_section.CoreSection.logdir`)
* a writable data directory
  (:attr:`~sopel.config.core_section.CoreSection.homedir`)

.. important::

    Do **not** run Sopel as the **root** user. And avoid if possible to run
    with a privileged user.


Running with systemd
====================

`systemd`__ is a service manager used by Ubuntu and most Debian-derived
Linux distributions. Here is an example of a service unit file to run Sopel as
a service, placed at ``/etc/systemd/system/sopel.service``:

.. code-block:: systemd

    [Unit]
    Description=Sopel IRC bot
    Documentation=https://sopel.chat/
    After=network-online.target

    [Service]
    Type=simple
    User=sopel
    RuntimeDirectory=sopel
    StateDirectory=sopel
    LogsDirectory=sopel
    PIDFile=/run/sopel/sopel.pid
    ExecStart=/home/sopel/.local/bin/sopel start
    Restart=on-failure
    RestartPreventExitStatus=2
    RestartSec=30
    Environment=LC_ALL=en_US.UTF-8 SOPEL_CONFIG_DIR=/etc/sopel

    [Install]
    WantedBy=multi-user.target

.. __: https://systemd.io/

For this service to work you will need the following:

* to create a ``sopel`` user
* to install ``sopel`` with that user (or to change the path in the
  ``ExecStart``)
* to place your Sopel configuration file into ``/etc/sopel/default.cfg``, and
  to setup its access rights so that the ``sopel`` user can read and write it
* and to edit the ``[core]`` section of this configuration file to set the
  appropriate paths:

  .. code-block:: ini

      [core]
      homedir = /var/lib/sopel
      pid_dir = /run/sopel
      logdir = /var/log/sopel

These paths are required for Sopel to know where to put its files (data, cache,
PID file, logs, etc.).

And with that, you will be able to start/stop your bot with:

* ``systemctl start sopel`` to start the service
* ``systemctl stop sopel`` to stop the service

Once you are sure it works, you can enable the service with
``systemctl enable sopel`` so that the service will start automatically at
boot.

.. seealso::

    There is more to say about systemd, its service unit files, and the
    ``systemctl`` command. Be sure to read `systemd.unit's documentation`__ for
    more information.

.. __: https://www.freedesktop.org/software/systemd/man/latest/systemd.unit.html


Example of configuration for Libera Chat
========================================

To put everything together, let's say you want to run a bot for your channel
on the `libera.chat network`__. For that, here is a configuration file you will
need to put at ``/etc/sopel/default.cfg``:

.. code-block:: ini

    [core]
    nick = <Your Bot Nick>
    host = irc.libera.chat
    port = 6697
    use_ssl = yes
    verify_ssl = yes
    owner = <Your Nick>
    channels =
        "#yourchannel"
    homedir = /var/lib/sopel
    pid_dir = /run/sopel
    logdir = /var/log/sopel

Make sure to replace ``<Your Bot Nick>`` with your bot's nick, as "Sopel" is
already taken; and set your own nick as the owner instead of ``<Your Nick>``.

.. __: https://libera.chat/


Multiple instances
==================

You can create a ``sopel@.service`` file that is a multi-instance systemd
template. It follows the same general structure as the single instance from
above, and uses the same user running all instances.

The following file should be placed at ``/etc/systemd/system/sopel@.service``:

.. code-block:: systemd

    [Unit]
    Description=Sopel IRC bot
    Documentation=https://sopel.chat/
    After=network-online.target
    DefaultInstance=sopel

    [Service]
    Type=simple
    User=sopel
    RuntimeDirectory=sopel
    StateDirectory=sopel
    LogsDirectory=sopel
    PIDFile=/run/sopel/sopel-%I.pid
    ExecStart=/home/sopel/.local/bin/sopel start -c %I.cfg
    Restart=on-failure
    RestartPreventExitStatus=2
    RestartSec=30
    Environment=LC_ALL=en_US.UTF-8 SOPEL_CONFIG_DIR=/etc/sopel

    [Install]
    WantedBy=multi-user.target

To start a service, you need to place the name of the configuration file you
want to use in the command, e.g. to run with the ``libera`` configuration:

* ``systemctl start sopel@libera.service`` to start the bot
* ``systemctl stop sopel@libera.service`` to stop the bot

Notice the ``@libera`` in each command line: it means the configuration file
will be ``/etc/sopel/libera.cfg``, and the PID file will be set at
``/run/sopel/sopel-libera.pid``.

.. note::

    The default instance name is ``sopel``, for the ``/etc/sopel/sopel.cfg``
    configuration file, and not ``/etc/sopel/default.cfg``.
