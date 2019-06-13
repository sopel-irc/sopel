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

Flood prevention
----------------

In order to prevent Sopel from flooding the server, a flood prevention
mechanism has been implemented. It can be controlled with several directives:

* :attr:`~CoreSection.flood_burst_lines`: it defines the number of message
  that can be sent before triggering the throttle mechanism.
* :attr:`~CoreSection.flood_empty_wait`: time to wait once burst limit has been
  reach before sending a new message.
* :attr:`~CoreSection.flood_refill_rate`: how much time (in second) must be
  spent before recovering flood limit.

For example this configuration:

.. code-block:: ini

   [core]
   flood_burst_lines = 10
   flood_empty_wait = 0.5
   flood_refill_rate = 2

will allow 10 messages at once before triggering the throttle mechanism, then
it'll wait 0.5s before sending a new message, and refill the burst limit every
2 seconds.

The default configuration works fine with most tested network, but bot's owners
are invited to tweak as necessary to respect their network's flood policy.


Authentication
==============

Sopel provide two ways to authenticate: a simple method, and a multi-methods
authentication. If only one authentication method is available, then it's best
to stick to the simple method, using :attr:`~CoreSection.auth_method`.

Simple method
-------------

This is the most common use case: the bot will authenticate itself using one
and only one method, being a server-based  or nick-based authentication.

To configure the authentication method, :attr:`~CoreSection.auth_method` must
be configured. For **server-based** methods:

* ``sasl``,
* ``server``

And for **nick-based** methods:

* ``nickserv``,
* ``authserv``,
* ``Q``,
* ``userserv``

These additionals options can be used to configure the authentication method
and the required credentials:

* :attr:`~CoreSection.auth_username`: account's username, if required
* :attr:`~CoreSection.auth_password`: account's password
* :attr:`~CoreSection.auth_target`: authentication method's target, if required
  by the ``auth_method``; when used for ``sasl``, it is the SASL mechanism,
  with a default to ``PLAIN``; when used for ``nickserv`` and ``userserv``,
  it's the service's nickname to send credentials to (respectively ``NickServ``
  and ``UserServ`` by default)

Multi-methods
-------------

In some case, an IRC bot needs to use both methods: server-based and
nick-based.

* :attr:`~CoreSection.server_auth_method`: define the server-based
  authentication method to use (``sasl`` or ``server``)
* :attr:`~CoreSection.nick_auth_method`: define the nick-based authentication
  method to use ( ``nickserv``, ``authserv``, ``Q``, or ``userserv``)

.. important::

   If ``auth_method`` is defined then ``nick_auth_method`` (and its options)
   will be ignored.


Server-based
............

When :attr:`~CoreSection.server_auth_method` is defined, the configuration
used are:

* :attr:`~CoreSection.server_auth_username`: account's username
* :attr:`~CoreSection.server_auth_password`: account's password
* :attr:`~CoreSection.server_auth_sasl_mech`: the SASL mechanism to use
  (defaults to ``PLAIN``)

Nick-based
..........

When :attr:`~CoreSection.nick_auth_method` is defined, the configuration
used are:

* :attr:`~CoreSection.nick_auth_username`: account's username; may be
  optional for some authentication method; defaults to the bot's nick
* :attr:`~CoreSection.nick_auth_password`: account's password
* :attr:`~CoreSection.nick_auth_target`: the target used to send authentication
  credentials; may be optional for some authentication method; defaults to
  ``NickServ`` for ``nickserv``, and to ``UserServ`` for ``userserv``.


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
