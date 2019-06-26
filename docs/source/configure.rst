.. py:module:: sopel.config.core_section

================================
The [core] configuration section
================================

A typical configuration file looks like this::

    [core]
    nick = Sopel
    host = chat.freenode.net
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
    :depth: 2


Identity & Admins
=================

Your bot's identity is configured by the following options:

* :attr:`~CoreSection.nick`: this is your bot's nick, as it will appear to
  other users on the server
* :attr:`~CoreSection.name` (optional)
* :attr:`~CoreSection.user` (optional)

User Modes
----------

To configure User modes, the :attr:`~CoreSection.modes` can be used:

.. code-block:: ini

   [core]
   mode = BpR

In this example, upon connection to the IRC server, Sopel will send this::

   MODE Sopel +BpR

Which means: this is a Bot (B), don't show channels it is in (p), and only
registered users (R) can send it messages. The list of supported modes depends
on the IRC server the bot connects to.

Owner & Admins
--------------

A Sopel instance must have exactly one owner. This is configured either by
:attr:`~CoreSection.owner_account` if the IRC server support IRC v3 Account; or
by :attr:`~CoreSection.owner`. If ``owner_account`` is set, ``owner`` will be
ignored.

The same instance can have multiple admins. The same way, it can be configured
by :attr:`~CoreSection.admin_accounts` or by :attr:`~CoreSection.admins`. If
``admin_accounts`` is set, ``admins`` will be ignored.

Both ``owner_account`` and ``admin_accounts`` are safer to use than a
nick-based management.


IRC Server
==========

To connect to a server, your bot needs these directives:

* :attr:`~CoreSection.host`: the server's hostname. Can be a domain name
  (like ``chat.freenode.net``) or an IP address.
* :attr:`~CoreSection.port`: optional, the port to connect to. Usually 6697,
  this is the default value the bot will use to connet to the server.

.. code-block:: ini

   [core]
   host = chat.freenode.net
   port = 6667

You can also configure the host the bot will connect from with
:attr:`~CoreSection.bind_host`.

Ping timeout
------------

By default, if Sopel doesn't get a Ping from the server every 120s, it will
consider that the connection has timed out. This amount of time can be modified
with the :attr:`~CoreSection.timeout` directive.

SSL Connection
--------------

It is possible to connect to an IRC server with an SSL connection. For that,
you need to set :attr:`~CoreSection.use_ssl` to true:

.. code-block:: ini

   [core]
   use_ssl = yes
   verify_ssl = yes
   ca_certs = path/to/sopel/ca_certs.pem

In that case:

* default port to connect to IRC will be 6697
* certificate will be verified if :attr:`~CoreSection.verify_ssl` is set to
  true, and its location can be configured with :attr:`~CoreSection.ca_certs`.

.. seealso::

   Sopel uses the built-in :func:`ssl.wrap_socket` function to wrap the socket
   used for the IRC connection.

   Certificate is required if and only if :attr:`~CoreSection.verify_ssl` is
   set to true.

Channels
--------

By default, Sopel won't connect to any channels. The list of channels to
connect to is configured by :attr:`~CoreSection.channels`:

.. code-block:: ini

   [core]
   channels = #sopel, #sopelunkers

It is possible to slow down the initial join of channels using
:attr:`~CoreSection.throttle_join`.

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

.. versionadded:: 7.0

   Flood prevention has been modified in Sopel 7.0 and these configuration
   options have been added: ``flood_burst_lines``, ``flood_empty_wait``, and
   ``flood_refill_rate``.


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

.. versionadded:: 7.0

   The multi-methods authentication has been added in Sopel 7.0 with its
   configuration options.

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

Sopel uses SQLAlchemy to connect and query its database. To configure the type
of database, set :attr:`~CoreSection.db_type` to one of these values:

* ``sqlite`` (default)
* ``mysql``
* ``postgres``
* ``mssql``
* ``oracle``
* ``firebird``
* ``sybase``

SQLite
------

There is only one options for SQLite, :attr:`~CoreSection.db_filename`, which
configures the path to the SQLite database file. Other options are ignored
when ``db_type`` is set to ``sqlite``.

Other Database
--------------

When ``db_type`` is one of the other type of database, the following options
are available:

* :attr:`~CoreSection.db_host`
* :attr:`~CoreSection.db_user`
* :attr:`~CoreSection.db_pass`
* :attr:`~CoreSection.db_port` (optional)
* :attr:`~CoreSection.db_name` (optional)
* :attr:`~CoreSection.db_driver` (optional)

Both ``db_port`` and ``db_name`` are optional, depending on your setup and the
type of your database.

In all cases, Sopel uses a database driver specific to each type. This driver
can be configured manually with the ``db_driver`` options. See the SQLAlchemy
documentation for more information about `database drivers`__, and how to
install them.

.. __: https://docs.sqlalchemy.org/en/latest/dialects/

.. versionadded:: 7.0

   SQLAlchemy for Database has been added in Sopel 7.0, which support multiple
   type of databases. The configuration options required for these new types
   has been added at the same time.


Commands & Plugins
==================

Users can interact with Sopel throught its commands, from Sopel's core or
from Sopel's plugins. A command is a prefix with a name. The prefix can be
configured with :attr:`~CoreSection.prefix`.

.. code-block:: ini

   [core]
   prefix = \.

.. note::

   This directive expect a **regex** pattern, so special regex characters must
   be escaped, as shown is the example above.

Other directives include:

* :attr:`~CoreSection.help_prefix`: the prefix used in help messages
* :attr:`~CoreSection.alias_nicks`: variable name for nick substitution,
  used by nick-based commands
* :attr:`~CoreSection.auto_url_schemes`: URL scheme (like ``http`` or ``ftp``)
  used to trigger the detection of URLs in messages.

Plugins
-------

By default, Sopel will load all available plugins. To exclude a plugins, you
can put its name in the :attr:`~CoreSection.exclude` directive. Here, the
``reload`` and ``meetbot`` plugins are disabled:

.. code-block:: ini

   [core]
   exclude = reload, meetbot

Alternatively, you can define a list of allowed plugins with
:attr:`~CoreSection.enable`: plugins not in this list will be ignored. In this
example, only the ``bugzilla`` and ``remind`` plugins are enabled (because
the ``meetbot`` is still excluded):

.. code-block:: ini

   [core]
   enable = bugzilla, remind, meetbot
   exclude = reload, meetbot

To load plugins from extra directories, use the :attr:`~CoreSection.extra`
option.

Ignore User
-----------

To ignore users based on their hosts and/or nicks, you can use these options:

* :attr:`~CoreSection.host_blocks`
* :attr:`~CoreSection.nick_blocks`


Logging
=======

Sopel's outputs are redirected to a file named ``<base>.stdio.log``, located in
the **log directory**, which is configured by :attr:`~CoreSection.logdir`; and
where ``<base>`` is the configuration's basename (usually ``default``).

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

.. versionadded:: 7.0

   Configuration options ``logging_format`` and ``logging_datefmt`` has been
   added to extend logging configuration.

.. versionchanged:: 7.0

   The log filename has been renamed from ``stdio.log`` to ``<base>.stdio.log``
   to prevent conflict when running more than one instance of Sopel.

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

.. versionadded:: 7.0

   Configuration options ``logging_channel_level``, ``logging_channel_format``
   and ``logging_channel_datefmt`` has been added to extend logging
   configuration.

Raw Logs
--------

It is possible to store raw logs of what Sopel receives and sends by setting
the flag :attr:`~CoreSection.log_raw` to true.

In that case, IRC messages received and sent are stored into a file named
``<base>.raw.log``, located in the log directory.

.. versionchanged:: 7.0

   The log filename has been renamed from ``raw.log`` to ``<base>.raw.log``
   to prevent conflict when running more than one instance of Sopel.


Misc
====

* :attr:`~CoreSection.homedir`
* :attr:`~CoreSection.default_time_format`
* :attr:`~CoreSection.default_timezone`
* :attr:`~CoreSection.not_configured`
* :attr:`~CoreSection.reply_errors`
* :attr:`~CoreSection.pid_dir`
