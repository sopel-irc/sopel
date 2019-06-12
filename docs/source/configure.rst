.. py:module:: sopel.config.core_section

================================
The [core] configuration section
================================

A typical configuration file looks like this::

    [core]
    nick = Sopel
    host = irc.freenode.org
    use_ssl = false
    port = 6667
    owner = dgw
    channels = #sopel

which tells the bot what is its name and its owner, and which server to
connect to and which channels to join.

Everything else is pretty much optional

The :class:`sopel.config.core_section.CoreSection` represents the ``[core]``
section of the configuration file. See each of its attributes for its full
description.

This file can be generated from a :doc:`console wizard<cli>` using
``sopel configure``.

.. contents::
    :local:


Identity & Admins
=================

For the bot:

* :attr:`~CoreSection.nick`
* :attr:`~CoreSection.name`
* :attr:`~CoreSection.user`

For its owners and admins:

* :attr:`~CoreSection.owner`
* :attr:`~CoreSection.owner_account`
* :attr:`~CoreSection.admins`
* :attr:`~CoreSection.admin_accounts`


IRC Server
==========

These directives are used to configure how the bot connect to an IRC server.

For the socket configuration:

* :attr:`~CoreSection.host`
* :attr:`~CoreSection.port`
* :attr:`~CoreSection.bind_host`

For SSL connection:

* :attr:`~CoreSection.use_ssl`
* :attr:`~CoreSection.verify_ssl`
* :attr:`~CoreSection.ca_certs`

For IRC connection:

* :attr:`~CoreSection.channels`
* :attr:`~CoreSection.throttle_join`
* :attr:`~CoreSection.timeout`
* :attr:`~CoreSection.modes`


Authentification
================

To authenticate the bot to the IRC server, the :attr:`~CoreSection.auth_method`
option must be defined, then these options will be used accordingly:

* :attr:`~CoreSection.auth_username`
* :attr:`~CoreSection.auth_password`
* :attr:`~CoreSection.auth_target`


Database
========

* :attr:`~CoreSection.db_type`
* :attr:`~CoreSection.db_driver`
* :attr:`~CoreSection.db_filename`
* :attr:`~CoreSection.db_host`
* :attr:`~CoreSection.db_port`
* :attr:`~CoreSection.db_name`
* :attr:`~CoreSection.db_user`
* :attr:`~CoreSection.db_pass`


Commands & Plugins
==================

To configure commands & triggers options:

* :attr:`~CoreSection.prefix`
* :attr:`~CoreSection.help_prefix`
* :attr:`~CoreSection.alias_nicks`
* :attr:`~CoreSection.auto_url_schemes`

To configure loaded plugins:

* :attr:`~CoreSection.enable`
* :attr:`~CoreSection.exclude`
* :attr:`~CoreSection.extra`

To ignore hosts & nicks:

* :attr:`~CoreSection.host_blocks`
* :attr:`~CoreSection.nick_blocks`

Logging
=======

Sopel's outputs are redirected to a file named ``stdio.log``, located in the
**log directory**, which is configured by :attr:`~CoreSection.logdir`.

It uses the built-in :func:`logging.basicConfig` function to configure its
logs with the following arguments:

* ``format``: set to :attr:`~CoreSection.logging_format` if configured
* ``datefmt``: set to :attr:`~CoreSection.logging_datefmt` if configured
* ``level``: set to :attr:`~CoreSection.logging_level`, default to ``WARNING``
  (see the Python documentation for available `logging level`__)

.. __: https://docs.python.org/3/library/logging.html#logging-levels

Example of configuration for logging:

.. code-block:: ini

   [core]
   logging_level = INFO
   logging_format = [%(asctime)s] %(levelname)s - %(message)s
   logging_datefmt = %Y-%m-%d %H:%M:%S


Log to a channel
----------------

It is possible to send logs to an IRC channel, by configuring
:attr:`~CoreSection.logging_channel`. By default, its uses the same log level,
format, and date-format parameters as console logs. This can be overridden
with these:

* ``format`` with :attr:`~CoreSection.logging_channel_format`
* ``datefmt`` with :attr:`~CoreSection.logging_channel_datefmt`
* ``level`` with :attr:`~CoreSection.logging_level`

Example of configuration to log errors only in the ``##bot_logs`` channel:

.. code-block:: ini

   [core]
   logging_level = INFO
   logging_format = [%(asctime)s] %(levelname)s - %(message)s
   logging_datefmt = %Y-%m-%d %H:%M:%S
   logging_channel = ##bot_logs
   logging_channel_level = ERROR
   logging_channel_format = %(message)s


Raw Logs
--------

It is possible to store raw logs of what Sopel receives and sends by setting
the flag :attr:`~CoreSection.log_raw` to true.

In that case, IRC messages received and sent are stored into a file named
``raw.log``, located in the log directory.


Misc
====

* :attr:`~CoreSection.homedir`
* :attr:`~CoreSection.default_time_format`
* :attr:`~CoreSection.default_timezone`
* :attr:`~CoreSection.not_configured`
* :attr:`~CoreSection.reply_errors`
* :attr:`~CoreSection.pid_dir`
