.. py:currentmodule:: sopel.config.core_section

================================
The [core] configuration section
================================

.. highlight:: ini

A typical configuration file looks like this::

    [core]
    nick = Sopel
    host = irc.libera.chat
    use_ssl = true
    port = 6697
    owner = dgw
    channels =
        "#sopel"

which tells the bot what its name is, who its owner is, which server to
connect to, and which channels to join.

Everything else is pretty much optional.

The :class:`~sopel.config.core_section.CoreSection` class represents the
``[core]`` section. See its documentation for detailed descriptions of each of
its attributes.

This file can be generated with ``sopel configure``.

.. seealso::

    The :doc:`cli` chapter for ``sopel configure`` subcommand.

.. contents::
    :local:
    :depth: 2


INI file structure
==================

Sopel uses an INI file structure, and uses `Python's ConfigParser`__ for that
purpose. Note that the exact behavior of the parser depends on the version of
Python you are running your instance of Sopel with (indentation and comments
in particular are handled differently between Python 2.7 and Python 3+).

On top of that, Sopel uses its own configuration class to handle certain types
of options, such as choice, integer, float, list, and boolean.

In this document, when a config option is a "list", it means you can provide
more than one value, each on its own line, like this::

    [core]
    single_option = only one value
    multi_option =
        first value
        second value
        "# escape value starting with # using double quotes"
        # this is a comment and won't be used as value
        yet another value

When a config option is a boolean, it means you can provide one of these
case-insensitive values as "true": ``1``, ``yes``, ``y``, ``true``, ``on``. Any
other value will be considered as "false".

When a config option is a choice, it means you can provide only one of the
values defined as valid for this option, or Sopel will complain about it.

.. note::

   The INI file structure Sopel uses does **not** require quoting of values,
   except for specific cases such as the escaped list value shown above.
   Quoting a value unnecessarily can lead to unexpected behavior such as an
   absolute pathname being interpreted as relative to Sopel's home directory.

.. __: https://docs.python.org/3/library/configparser.html#supported-ini-file-structure


Identity & Admins
=================

Your bot's identity is configured by the following options:

* :attr:`~CoreSection.nick`: this is your bot's nick, as it will appear to
  other users on the server
* :attr:`~CoreSection.user` (optional): this is your bot's user name, as the
  server will see it
* :attr:`~CoreSection.name` (optional): the name of the bot as it will appear
  to a ``WHOIS <nick>`` request

For example, given the following hostmask ``Sopel!sopelbot@address``, then
``Sopel`` is the value from :attr:`~CoreSection.nick`, and ``sopelbot`` is the
value from :attr:`~CoreSection.user`::

    [core]
    nick = Sopel
    user = sopelbot
    name = Sopel 7.0

In that case, a ``WHOIS Sopel`` request will give ``Sopel 7.0`` for its name.

User Modes
----------

To have Sopel set additional user modes upon connection, use the
:attr:`~CoreSection.modes` setting::

    [core]
    modes = BpR

In this example, upon connection to the IRC server, Sopel will send this::

    MODE Sopel +BpR

Which means: this is a Bot (B), don't show channels it is in (p), and only
registered users (R) can send it messages. The list of supported modes depends
on the IRC server the bot connects to.

.. important::

   The list of available modes depends on the implementation of the IRC server,
   and its configuration.

   For example, the `user modes on Libera Chat`__ are different from the list
   of available `user modes on an UnrealIRCd server`__.

   .. __: https://libera.chat/guides/usermodes
   .. __: https://www.unrealircd.org/docs/User_modes

Owner & Admins
--------------

A Sopel instance must have exactly one owner. This is configured by the
:attr:`~CoreSection.owner` setting. If the IRC server supports IRCv3 accounts,
Sopel can use :attr:`~CoreSection.owner_account` to increase the security of
ownership verification.

The same instance can have multiple admins. Similarly, it can be configured
by :attr:`~CoreSection.admin_accounts` or by :attr:`~CoreSection.admins`. If
``admin_accounts`` is set, ``admins`` will be ignored.

Example owner & admin configurations::

    # Using nickname matching
    [core]
    # Will be used for alerts and ownership verification
    owner = dgw
    admins =
            Exirel
            HumorBaby

    # Using account matching
    [core]
    # Will be used for alerts only
    owner = dgw
    # Will be used for ownership verification
    owner_account = dgws_account
    admin_accounts =
            Exirel
            HumorBaby

Both ``owner_account`` and ``admin_accounts`` are safer to use than
nick-based matching, but the IRC server must support accounts.
(Most, sadly, do not as of late 2019.)

.. important::

    The :attr:`~CoreSection.owner` setting should **always** contain the bot
    owner's nickname, even when using :attr:`~CoreSection.owner_account`. Both
    Sopel and plugins may send important messages or notices to the owner
    using ``bot.config.core.owner`` as the recipient.


IRC Server
==========

To connect to a server, your bot needs these directives:

* :attr:`~CoreSection.host`: the server's hostname. Can be a domain name
  (like ``irc.libera.chat``) or an IP address.
* :attr:`~CoreSection.port`: optional, the port to connect to. Usually 6697 for
  SSL connection and 6667 for unsecure connection, the default value the bot
  will use to connect to the server.
* :attr:`~CoreSection.use_ssl`: connect using SSL (see below)::

    [core]
    host = irc.libera.chat
    port = 6697
    use_ssl = true

You can also configure the host the bot will connect from with
:attr:`~CoreSection.bind_host`.

Ping Timeout
------------

By default, if Sopel doesn't get a PING from the server every 120s, it will
consider that the connection has timed out. This amount of time can be modified
with the :attr:`~CoreSection.timeout` directive.

Internally, Sopel will try to send a ``PING`` either:

* every 50s
* or 50s after the last message was received by the bot

This value can be modified with the :attr:`~CoreSection.timeout_ping_interval`.

SSL Connection
--------------

It is possible to connect to an IRC server with an SSL connection. For that,
you need to set :attr:`~CoreSection.use_ssl` to true::

    [core]
    use_ssl = yes
    verify_ssl = yes
    ca_certs = /path/to/sopel/ca_certs.pem

In that case:

* default port to connect to IRC will be 6697
* certificate will be verified if :attr:`~CoreSection.verify_ssl` is set to
  true

.. seealso::

   Sopel uses the built-in :func:`ssl.wrap_socket` function to wrap the socket
   used for the IRC connection.

.. note::

   Sopel will try to look at one of these files for the CA certs pem file
   required by :func:`ssl.wrap_socket`:

   * ``/etc/pki/tls/cert.pem``
   * ``/etc/ssl/certs/ca-certificates.crt`` (Debian)
   * ``/etc/ssl/cert.pem`` (FreeBSD base OpenSSL)
   * ``/usr/local/openssl/cert.pem`` (FreeBSD userland OpenSSL)
   * ``/etc/pki/tls/certs/ca-bundle.crt`` (RHEL 6 / Fedora)
   * ``/etc/pki/ca-trust/extracted/pem/tls-ca-bundle.pem`` (RHEL 7 / CentOS)
   * ``/etc/pki/tls/cacert.pem`` (OpenELEC)
   * ``/etc/ssl/ca-bundle.pem`` (OpenSUSE)

   This is required if :attr:`~CoreSection.verify_ssl` is set to true. It is
   possible to set the file used with :attr:`~CoreSection.ca_certs`. This is
   useful if e.g. Sopel cannot find the CA certs file, or you need Sopel to
   trust a CA not trusted by the system.

Channels
--------

By default, Sopel won't join any channels. The list of channels to
join is configured by :attr:`~CoreSection.channels`::

    [core]
    channels =
        "#sopel"
        "#sopelunkers isP@ssw0rded"

It is possible to slow down the initial joining of channels using
:attr:`~CoreSection.throttle_join` and :attr:`~CoreSection.throttle_wait`, for
example if the IRC network kicks clients that join too many channels too
quickly::

    [core]
    channels =
        "#sopel"
        "#sopelunkers isP@ssw0rded"
        # ... too many channels ...
        "#justonemore"
    throttle_join = 4
    throttle_wait = 2

In that example, Sopel will send ``JOIN`` and ``WHO`` commands 4 by 4 every 2s.

Flood Prevention
----------------

In order to avoid flooding the server, Sopel has a built-in flood prevention
mechanism. The flood burst limit can be controlled with these directives:

* :attr:`~CoreSection.flood_burst_lines`: the number of messages
  that can be sent before triggering the throttle mechanism.
* :attr:`~CoreSection.flood_refill_rate`: how much time (in seconds) must be
  spent before recovering flood limit.

The wait time when the flood limit is reached can be controlled with these:

* :attr:`~CoreSection.flood_empty_wait`: time to wait once burst limit has been
  reached before sending a new message.
* :attr:`~CoreSection.flood_max_wait`: absolute maximum time to wait before
  sending a new message once the burst limit has been reached.

And the extra wait penalty for longer messages can be controlled with these:

* :attr:`~CoreSection.flood_text_length`: maximum size of messages before they
  start getting an extra wait penalty.
* :attr:`~CoreSection.flood_penalty_ratio`: ratio used to compute said penalty.

For example this configuration::

    [core]
    flood_burst_lines = 10
    flood_empty_wait = 0.5
    flood_refill_rate = 2

will allow 10 messages at once before triggering the throttle mechanism, then
it'll wait 0.5s before sending a new message, and refill the burst limit every
2 seconds.

The wait time **cannot be longer** than :attr:`~CoreSection.flood_max_wait` (2s
by default). This maximum wait time includes any potential extra penalty for
longer messages.

Messages that are longer than :attr:`~CoreSection.flood_text_length` get an
extra wait penalty. The penalty is computed using a penalty ratio (controlled
by :attr:`~CoreSection.flood_penalty_ratio`, which is 1.4 by default)::

    length_overflow = max(0, (len(text) - flood_text_length))
    extra_penalty = length_overflow / (flood_text_length * flood_penalty_ratio)

For example with a message of 80 characters, the added extra penalty will be::

    length_overflow = max(0, 80 - 50)  # == 30
    extra_penalty = 30 / (50 * 1.4)  # == 0.428s (approximately)

With the default configuration, it means a minimum wait time of 0.928s before
sending any new message (0.5s + 0.428s).

You can **deactivate** this extra wait penalty by setting
:attr:`~CoreSection.flood_penalty_ratio` to 0.

The default configuration works fine with most tested networks, but individual
bots' owners are invited to tweak as necessary to respect their network's flood
policy.

.. versionadded:: 7.0

    Additional configuration options: ``flood_burst_lines``, ``flood_empty_wait``,
    and ``flood_refill_rate``.

.. versionadded:: 7.1

    Even more additional configuration options: ``flood_max_wait``,
    ``flood_text_length``, and ``flood_penalty_ratio``.

    It is now possible to deactivate the extra penalty for longer messages by
    setting ``flood_penalty_ratio`` to 0.

.. note::

    ``@dgw`` said once about Sopel's flood protection logic:

        *"It's some arcane magic from AT LEAST a decade ago."*

Perform commands on connect
---------------------------

The bot can be configured to send custom commands upon successful connection to
the IRC server. This can be used in situations where the bot's built-in
capabilities are not sufficient, or further automation is desired.
``$nickname`` can be used in a command as a placeholder, and it will be
replaced with the bot's nickname, as specified in the configuration
(:attr:`~CoreSection.nick`).

The list of commands to send is set with
:attr:`~CoreSection.commands_on_connect`. For example, the following
configuration::

    [core]
    commands_on_connect =
        PRIVMSG X@Channels.undernet.org :LOGIN MyUserName A$_Strong,*pasSWord
        PRIVMSG IDLEBOT :login $nickname idLEPasswoRD

will, upon connection:

1) identify to Undernet services (``PRIVMSG X@Channels...``)
2) login with ``IDLEBOT`` using the bot's nickname (``PRIVMSG IDLEBOT ...``)

.. seealso::

   This functionality is analogous to ZNC's ``perform`` module:
   https://wiki.znc.in/Perform


Authentication
==============

Sopel provides two ways to authenticate: a simple method, and multi-stage
authentication. If only one authentication method is available, then it's best
to stick to the simple method, using :attr:`~CoreSection.auth_method`.

Simple method
-------------

This is the most common use case: the bot will authenticate itself using one
and only one method, being a server-based or nick-based authentication.

To configure the authentication method, :attr:`~CoreSection.auth_method` must
be configured. For **server-based** methods:

* ``sasl``
* ``server``

And for **nick-based** methods:

* ``nickserv``
* ``authserv``
* ``Q``
* ``userserv``

Several additional options can be used to configure the authentication method
and the required credentials. You can follow the link for each to find more
details:

* :attr:`~CoreSection.auth_username`: account's username, if used by
  the ``auth_method``
* :attr:`~CoreSection.auth_password`: password for authentication
* :attr:`~CoreSection.auth_target`: authentication method's target, if required
  by the ``auth_method``:

  * ``sasl``: the SASL mechanism (``PLAIN`` by default)
  * ``nickserv``: the service's nickame to send credentials to
    (``NickServ`` by default)
  * ``userserv``: the service's nickame to send credentials to
    (``UserServ`` by default)

Example of nick-based authentication with NickServ service::

    [core]
    # select nick-based authentication
    auth_method = nickserv
    # auth_username is not required for nickserv
    # your bot's login password
    auth_password = SopelIsGreat!
    # default value
    auth_target = NickServ

And here is an example of server-based authentication using SASL::

    [core]
    # select SASL authentication
    auth_method = sasl
    # your bot's login username and password
    auth_username = BotAccount
    auth_password = SopelIsGreat!
    # default SASL mechanism
    auth_target = PLAIN

Example of authentication to a ZNC bouncer::

    [core]
    # select server-based authentication
    auth_method = server
    # auth_username is not used with server authentication, so instead
    # we combine the ZNC username, network name, and password here:
    auth_password = Sopel/libera:SopelIsGreat!

Don't forget to configure your ZNC to log in to the real network!

Finally, here is how to enable CertFP once you have a certificate that meets
your IRC network's requirements::

    [core]
    client_cert_file = /path/to/cert.pem  # your bot's client certificate
    # some networks require SASL EXTERNAL for CertFP to work
    auth_method = sasl                    # if required
    auth_target = EXTERNAL                # if required


Multi-stage
-----------

In some cases, an IRC bot needs to use both server-based and
nick-based authentication.

* :attr:`~CoreSection.server_auth_method`: defines the server-based
  authentication method to use (``sasl`` or ``server``); it will
  be used only if :attr:`~CoreSection.auth_method` does not define a
  server-based authentication method
* :attr:`~CoreSection.nick_auth_method`: defines the nick-based authentication
  method to use ( ``nickserv``, ``authserv``, ``Q``, or ``userserv``); it will
  be used only if :attr:`~CoreSection.auth_method` is not set

.. versionadded:: 7.0

   The multi-stage authentication has been added in Sopel 7.0 with its
   configuration options.

Server-based
............

When :attr:`~CoreSection.server_auth_method` is defined the settings used are:

* :attr:`~CoreSection.server_auth_username`: account's username
* :attr:`~CoreSection.server_auth_password`: account's password
* :attr:`~CoreSection.server_auth_sasl_mech`: the SASL mechanism to use
  (defaults to ``PLAIN``; ``EXTERNAL`` is also available)

For example, this will use NickServ ``IDENTIFY`` command and SASL mechanism::

    [core]
    # select nick-based authentication
    auth_method = nickserv
    # auth_username is not required for nickserv
    # your bot's login password
    auth_password = SopelIsGreat!
    # default value
    auth_target = NickServ

    # select SASL authentication
    server_auth_method = sasl
    # your bot's login username and password
    server_auth_username = BotAccount
    server_auth_password = SopelIsGreat!
    # default SASL mechanism
    server_auth_target = PLAIN

.. important::

    If :attr:`~CoreSection.auth_method` is already set to ``sasl`` or
    ``server`` then :attr:`~CoreSection.server_auth_method` (and its options)
    will be ignored.

Nick-based
..........

When :attr:`~CoreSection.nick_auth_method` is defined, the settings
used are:

* :attr:`~CoreSection.nick_auth_username`: account's username; may be
  optional for some authentication methods; defaults to the bot's nick
* :attr:`~CoreSection.nick_auth_password`: account's password
* :attr:`~CoreSection.nick_auth_target`: the target used to send authentication
  credentials; may be optional for some authentication methods; defaults to
  ``NickServ`` for ``nickserv``, and to ``UserServ`` for ``userserv``.

For example, this will use NickServ ``IDENTIFY`` command and SASL mechanism::

    [core]
    # select nick-based authentication
    nick_auth_method = nickserv
    # nick_auth_username is not required for nickserv
    # your bot's login password
    nick_auth_password = SopelIsGreat!
    # default value
    nick_auth_target = NickServ

    # select SASL auth
    server_auth_method = sasl
    # your bot's login username and password
    server_auth_username = BotAccount
    server_auth_password = SopelIsGreat!
    # default SASL mechanism
    server_auth_target = PLAIN

.. important::

    If :attr:`~CoreSection.auth_method` is already set then
    :attr:`~CoreSection.nick_auth_method` (and its options) will be ignored.


Database
========

Sopel uses SQLAlchemy to connect to and query its database. To configure the
type of database, set :attr:`~CoreSection.db_type` to one of these values:

* ``sqlite`` (default)
* ``mysql``
* ``postgres``
* ``mssql``
* ``oracle``
* ``firebird``
* ``sybase``

SQLite
------

There is only one option for SQLite, :attr:`~CoreSection.db_filename`, which
configures the path to the SQLite database file. Other options are ignored
when ``db_type`` is set to ``sqlite``.

Other Database
--------------

When ``db_type`` is *not* set to ``sqlite``, the following options
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

   Using SQLAlchemy for the database has been added in Sopel 7.0, which
   supports multiple types of databases. The configuration options required for
   these new types have been added at the same time.

.. important::

   Plugins originally written for Sopel 6.x and older might not work properly
   with non-``sqlite`` databases. If a plugin you want to use with Sopel 7+ has
   not been updated, feel free to test it and tell its author(s) the results.


Commands & Plugins
==================

Users can interact with Sopel through its commands, from Sopel's core or
from Sopel's plugins. A command is a prefix with a name. The prefix can be
configured with :attr:`~CoreSection.prefix`::

    [core]
    prefix = \.

.. note::

   This directive expects a **regex** pattern, so special regex characters must
   be escaped, as shown in the example above.

Other directives include:

* :attr:`~CoreSection.help_prefix`: the prefix used in help messages
* :attr:`~CoreSection.alias_nicks`: additional names users might call the bot;
  used by nick-based commands
* :attr:`~CoreSection.auto_url_schemes`: URL schemes (like ``http`` or ``ftp``)
  that should trigger the detection of URLs in messages

Plugins
-------

By default, Sopel will load all available plugins. To exclude a plugin, you
can put its name in the :attr:`~CoreSection.exclude` directive. Here, the
``reload`` and ``meetbot`` plugins are disabled::

    [core]
    exclude =
        reload
        meetbot

Alternatively, you can define a list of allowed plugins with
:attr:`~CoreSection.enable`: plugins not in this list will be ignored. In this
example, only the ``bugzilla`` and ``remind`` plugins are enabled (because
``meetbot`` is still excluded)::

    [core]
    enable =
        bugzilla
        remind
        meetbot
    exclude =
        reload
        meetbot

To detect plugins from extra directories, use the :attr:`~CoreSection.extra`
option.

Ignore User
-----------

To ignore users based on their hosts and/or nicks, you can use these options:

* :attr:`~CoreSection.host_blocks`
* :attr:`~CoreSection.nick_blocks`


Logging
=======

Sopel writes logs of its activities to its **log directory**, which is
configured by :attr:`~CoreSection.logdir`. Depending on the enabled options,
there may be as many as four log files per config:

* ``<configname>.sopel.log``: standard logging output
* ``<configname>.error.log``: errors only
* ``<configname>.exceptions.log``: exceptions and accompanying tracebacks
* ``<configname>.raw.log``: raw traffic between Sopel and the IRC server, if
  enabled (see :ref:`below <Raw Logs>`)

Sopel uses the built-in :func:`logging.basicConfig` function to configure its
logs with the following arguments:

* ``format``: set to :attr:`~CoreSection.logging_format` if configured
* ``datefmt``: set to :attr:`~CoreSection.logging_datefmt` if configured
* ``level``: set to :attr:`~CoreSection.logging_level`, default to ``WARNING``
  (see the Python documentation for `available logging levels`__)

.. __: https://docs.python.org/3/library/logging.html#logging-levels

Example of configuration for logging::

    [core]
    logging_level = INFO
    logging_format = [%(asctime)s] %(levelname)s - %(message)s
    logging_datefmt = %Y-%m-%d %H:%M:%S
    logdir = /path/to/logs

.. _logging-basename:
.. note::

    The ``<configname>`` prefix in logging filenames refers to the
    configuration's :attr:`~sopel.config.Config.basename` attribute.

.. versionadded:: 7.0

   Configuration options ``logging_format`` and ``logging_datefmt`` have been
   added to extend logging configuration.

.. versionchanged:: 7.0

   The log filename has been renamed from ``stdio.log`` to
   ``<configname>.sopel.log`` to disambiguate its purpose and prevent
   conflicts when running more than one instance of Sopel.

Log to a Channel
----------------

It is possible to send logs to an IRC channel, by configuring
:attr:`~CoreSection.logging_channel`. By default, it uses the same log level,
format, and date-format parameters as console logs. This can be overridden
with these settings:

* ``format`` with :attr:`~CoreSection.logging_channel_format`
* ``datefmt`` with :attr:`~CoreSection.logging_channel_datefmt`
* ``level`` with :attr:`~CoreSection.logging_channel_level`

Example of configuration to log errors only in the ``##bot_logs`` channel::

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
the flag :attr:`~CoreSection.log_raw` to true::

    [core]
    log_raw = on

In that case, IRC messages received and sent are stored into a file named
``<configname>.raw.log``, located in the log directory.

.. versionchanged:: 7.0

   The log filename has been renamed from ``raw.log`` to
   ``<configname>.raw.log`` to prevent conflicts when running more than one
   instance of Sopel.


Other
=====

* :attr:`~CoreSection.homedir`
* :attr:`~CoreSection.default_time_format`
* :attr:`~CoreSection.default_timezone`
* :attr:`~CoreSection.not_configured`
* :attr:`~CoreSection.reply_errors`
* :attr:`~CoreSection.pid_dir`
