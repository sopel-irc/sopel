# coding=utf-8

from __future__ import unicode_literals, absolute_import, print_function, division

import os.path

from sopel.config.types import (
    StaticSection, ValidatedAttribute, ListAttribute, ChoiceAttribute,
    FilenameAttribute, NO_DEFAULT
)
from sopel.tools import Identifier


def _find_certs():
    """Find the TLS root CA store.

    :returns: str (path to file)
    """
    # check if the root CA store is at a known location
    locations = [
        '/etc/pki/tls/cert.pem',  # best first guess
        '/etc/ssl/certs/ca-certificates.crt',  # Debian
        '/etc/ssl/cert.pem',  # FreeBSD base OpenSSL
        '/usr/local/openssl/cert.pem',  # FreeBSD userland OpenSSL
        '/etc/pki/tls/certs/ca-bundle.crt',  # RHEL 6 / Fedora
        '/etc/pki/ca-trust/extracted/pem/tls-ca-bundle.pem',  # RHEL 7 / CentOS
        '/etc/pki/tls/cacert.pem',  # OpenELEC
        '/etc/ssl/ca-bundle.pem',  # OpenSUSE
    ]
    for certs in locations:
        if os.path.isfile(certs):
            return certs
    return None


def configure(config):
    config.core.configure_setting('nick', 'Enter the nickname for your bot.')
    config.core.configure_setting('host', 'Enter the server to connect to.')
    config.core.configure_setting('use_ssl', 'Should the bot connect with SSL?')
    if config.core.use_ssl:
        default_port = 6697
    else:
        default_port = 6667
    config.core.configure_setting('port', 'Enter the port to connect on.',
                                  default=default_port)
    config.core.configure_setting(
        'owner', "Enter your own IRC name (or that of the bot's owner)")
    config.core.configure_setting(
        'channels',
        'Enter the channels to connect to at startup, separated by commas.'
    )
    config.core.configure_setting(
        'commands_on_connect',
        'Enter commands to perform on successful connection to server (one per \'?\' prompt).'
    )


class CoreSection(StaticSection):
    """The config section used for configuring the bot itself."""

    admins = ListAttribute('admins')
    """The list of people (other than the owner) who can administer the bot."""

    admin_accounts = ListAttribute('admin_accounts')
    """The list of admin accounts other than the owner's.

    Each account is allowed to administer the bot and can perform commands
    that are restricted to admins.

    This should not be set for networks that do not support IRCv3 account
    capabilities.
    """

    alias_nicks = ListAttribute('alias_nicks')
    """List of alternate names for regex substitutions.

    These aliases are used as the bot's nick for ``$nick`` and ``$nickname``
    regex substitutions.
    """

    auth_method = ChoiceAttribute('auth_method', choices=[
        'nickserv', 'authserv', 'Q', 'sasl', 'server', 'userserv'])
    """Simple method to authenticate with the server.

    Can be ``nickserv``, ``authserv``, ``Q``, ``sasl``, or ``server`` or
    ``userserv``.

    This allows only a single authentication method; to use both a server-based
    authentication method as well as a nick-based authentication method, see
    ``server_auth_method`` and ``nick_auth_method``.

    If this is specified, ``nick_auth_method`` will be ignored, and it takes
    precedence over ``server_auth_method``.
    """

    auth_password = ValidatedAttribute('auth_password')
    """The password to use to authenticate with the server."""

    auth_target = ValidatedAttribute('auth_target')
    """The user to use for nickserv authentication, or the SASL mechanism.

    May not apply, depending on ``auth_method``. Defaults to NickServ for
    nickserv auth, and PLAIN for SASL auth.
    """

    auth_username = ValidatedAttribute('auth_username')
    """The username/account to use to authenticate with the server.

    May not apply, depending on ``auth_method``.
    """

    auto_url_schemes = ListAttribute(
        'auto_url_schemes',
        strip=True,
        default=['http', 'https', 'ftp'])
    """List of URL schemes that will trigger URL callbacks.

    Used by the URL callbacks feature; see :func:`sopel.module.url` decorator
    for plugins.

    The default value allows ``http``, ``https``, and ``ftp``.
    """

    bind_host = ValidatedAttribute('bind_host')
    """Bind the connection to a specific IP."""

    ca_certs = FilenameAttribute('ca_certs', default=_find_certs())
    """The path of the CA certs pem file."""

    channels = ListAttribute('channels')
    """List of channels for the bot to join when it connects."""

    db_type = ChoiceAttribute('db_type', choices=[
        'sqlite', 'mysql', 'postgres', 'mssql', 'oracle', 'firebird', 'sybase'], default='sqlite')
    """The type of database to use for Sopel's database.

    mysql - pip install mysql-python (Python 2) or pip install mysqlclient (Python 3)
    postgres - pip install psycopg2
    mssql - pip install pymssql

    See https://docs.sqlalchemy.org/en/latest/dialects/ for a full list of
    dialects.
    """

    db_filename = ValidatedAttribute('db_filename')
    """The filename for Sopel's database. (SQLite only)"""

    db_driver = ValidatedAttribute('db_driver')
    """The driver for Sopel's database.

    This is optional, but can be specified if user wants to use a different
    driver.

    .. seealso::

        https://docs.sqlalchemy.org/en/latest/core/engines.html
    """

    db_user = ValidatedAttribute('db_user')
    """The user for Sopel's database."""

    db_pass = ValidatedAttribute('db_pass')
    """The password for Sopel's database."""

    db_host = ValidatedAttribute('db_host')
    """The host for Sopel's database."""

    db_port = ValidatedAttribute('db_port')
    """The port for Sopel's database."""

    db_name = ValidatedAttribute('db_name')
    """The name of Sopel's database."""

    default_time_format = ValidatedAttribute('default_time_format',
                                             default='%Y-%m-%d - %T%Z')
    """The default format to use for time in messages."""

    default_timezone = ValidatedAttribute('default_timezone', default='UTC')
    """The default timezone to use for time in messages."""

    enable = ListAttribute('enable')
    """A whitelist of the only plugins you want to enable."""

    exclude = ListAttribute('exclude')
    """A list of plugins which should not be loaded."""

    extra = ListAttribute('extra')
    """A list of other directories you'd like to include plugins from."""

    help_prefix = ValidatedAttribute('help_prefix', default='.')
    """The prefix to use in help output."""

    @property
    def homedir(self):
        """The directory in which various files are stored at runtime.

        By default, this is the same directory as the config. It can not be
        changed at runtime.
        """
        return self._parent.homedir

    host = ValidatedAttribute('host', default='irc.dftba.net')
    """The server to connect to."""

    host_blocks = ListAttribute('host_blocks')
    """A list of hostmasks which Sopel should ignore.

    Regular expression syntax is used.
    """

    log_raw = ValidatedAttribute('log_raw', bool, default=False)
    """Whether a log of raw lines as sent and received should be kept."""

    logdir = FilenameAttribute('logdir', directory=True, default='logs')
    """Directory in which to place logs."""

    logging_channel = ValidatedAttribute('logging_channel', Identifier)
    """The channel to send logging messages to."""

    logging_channel_datefmt = ValidatedAttribute('logging_channel_datefmt')
    """The logging format string to use for timestamps in IRC channel logs.

    If not specified, this falls back to using ``logging_datefmt``.

    .. versionadded:: 7.0
    """

    logging_channel_format = ValidatedAttribute('logging_channel_format')
    """The logging format string to use in IRC channel logs.

    If not specified, this falls back to using ``logging_format``.

    .. versionadded:: 7.0
    """

    logging_channel_level = ChoiceAttribute('logging_channel_level',
                                            ['CRITICAL', 'ERROR', 'WARNING',
                                             'INFO', 'DEBUG'],
                                            'WARNING')
    """The lowest severity of logs to display in IRC channel logs.

    If not specified, this falls back to using ``logging_level``.

    .. versionadded:: 7.0
    """

    logging_datefmt = ValidatedAttribute('logging_datefmt')
    """The logging format string to use for timestamps in logs.

    If not specified, the datefmt is not provided, and logging will use
    the Python default.

    .. versionadded:: 7.0
    """

    logging_format = ValidatedAttribute(
        'logging_format',
        default='[%(asctime)s] %(name)-20s %(levelname)-8s - %(message)s')
    """The logging format string to use for logs.

    If not specified, the default format is::

        [%(asctime)s] %(name)-20s %(levelname)-8s - %(message)s

    which will output the timestamp, the package that generated the log line,
    the log level of the line, and (finally) the actual message. For example::

        [2019-10-21 12:47:44,272] sopel.irc            INFO     - Connected.

    .. versionadded:: 7.0
    .. seealso::
        Python's logging format documentation:
        https://docs.python.org/3/library/logging.html#logrecord-attributes
    """

    logging_level = ChoiceAttribute('logging_level',
                                    ['CRITICAL', 'ERROR', 'WARNING', 'INFO',
                                     'DEBUG'],
                                    'INFO')
    """The lowest severity of logs to display.

    If not specified, this defaults to ``INFO``.
    """

    modes = ValidatedAttribute('modes', default='B')
    """User modes to be set on connection."""

    name = ValidatedAttribute('name', default='Sopel: https://sopel.chat')
    """The "real name" of your bot for ``WHOIS`` responses."""

    nick = ValidatedAttribute('nick', Identifier, default=Identifier('Sopel'))
    """The nickname for the bot."""

    nick_auth_method = ChoiceAttribute('nick_auth_method', choices=[
        'nickserv', 'authserv', 'Q', 'userserv'])
    """The nick authentication method.

    Can be ``nickserv``, ``authserv``, ``Q``, or ``userserv``.

    .. versionadded:: 7.0
    """

    nick_auth_password = ValidatedAttribute('nick_auth_password')
    """The password to use to authenticate the bot's nick.

    .. versionadded:: 7.0
    """

    nick_auth_target = ValidatedAttribute('nick_auth_target')
    """The target user for nick authentication.

    May not apply, depending on ``nick_auth_method``.

    Defaults to ``NickServ`` for ``nickserv``, and ``UserServ`` for
    ``userserv``.

    .. versionadded:: 7.0
    """

    nick_auth_username = ValidatedAttribute('nick_auth_username')
    """The username/account to use for nick authentication.

    May not apply, depending on ``nick_auth_method``.

    Defaults to the value of ``nick``.

    .. versionadded:: 7.0
    """

    nick_blocks = ListAttribute('nick_blocks')
    """A list of nicks which Sopel should ignore.

    Regular expression syntax is used.
    """

    not_configured = ValidatedAttribute('not_configured', bool, default=False)
    """For package maintainers. Not used in normal configurations.

    This allows software packages to install a default config file, with this
    set to true, so that the bot will not run until it has been properly
    configured.
    """

    owner = ValidatedAttribute('owner', default=NO_DEFAULT)
    """The IRC name of the owner of the bot."""

    owner_account = ValidatedAttribute('owner_account')
    """The services account name of the owner of the bot.

    This should only be set on networks which support IRCv3 account
    capabilities.
    """

    commands_on_connect = ListAttribute('commands_on_connect')
    """A list of commands to perform upon successful connection to IRC server.

    Each line is a message that will be sent to the server once connected.
    Example::

        PRIVMSG Q@CServe.quakenet.org :AUTH my_username MyPassword,@#$%!
        PRIVMSG MyOwner :I'm here!

    ``$nickname`` can be used in a command as a placeholder, and it will be
    replaced with the bot's :attr:`~CoreSection.nick`. For example when the
    nick is ``Sopel``, then this ``MODE $nickname +Xxw`` will become
    ``MODE Sopel +Xxw``.

    .. versionadded:: 7.0
    """

    pid_dir = FilenameAttribute('pid_dir', directory=True, default='.')
    """The directory in which to put the file Sopel uses to track its process ID.

    You probably do not need to change this unless you're managing Sopel with
    ``systemd`` or similar.
    """

    port = ValidatedAttribute('port', int, default=6667)
    """The port to connect on."""

    prefix = ValidatedAttribute('prefix', default='\\.')
    """The prefix to add to the beginning of commands.

    It is a regular expression (so the default, ``\\.``, means commands start
    with a period), though using capturing groups will create problems.
    """

    reply_errors = ValidatedAttribute('reply_errors', bool, default=True)
    """Whether to message the sender of a message that triggered an error with the exception."""

    server_auth_method = ChoiceAttribute('server_auth_method', choices=['sasl', 'server'])
    """The server authentication method.

    Can be ``sasl`` or ``server``.

    .. versionadded:: 7.0
    """

    server_auth_password = ValidatedAttribute('server_auth_password')
    """The password to use to authenticate with the server.

    .. versionadded:: 7.0
    """

    server_auth_sasl_mech = ValidatedAttribute('server_auth_sasl_mech')
    """The SASL mechanism.

    Defaults to PLAIN.

    .. versionadded:: 7.0
    """

    server_auth_username = ValidatedAttribute('server_auth_username')
    """The username/account to use to authenticate with the server.

    .. versionadded:: 7.0
    """

    throttle_join = ValidatedAttribute('throttle_join', int, default=0)
    """Slow down the initial join of channels to prevent getting kicked.

    Sopel will only join this many channels at a time, sleeping for a second
    between each batch. This is unnecessary on most networks.

    If not set, or set to 0, Sopel won't slow down the initial join.

    .. seealso::

       :attr:`throttle_wait` controls the time Sopel waits between batches
       of channels.

    """

    throttle_wait = ValidatedAttribute('throttle_wait', int, default=1)
    """Time in seconds Sopel waits at the initial join of channels.

    By default, it waits 1s between batches.

    For example, with ``throttle_join = 2`` and ``throttle_wait = 5`` it will
    wait 5s every 2 channels it joins.

    .. seealso::

        :attr:`throttle_join` controls channel batch size.

    """

    timeout = ValidatedAttribute('timeout', int, default=120)
    """The amount of time acceptable between pings before timing out."""

    use_ssl = ValidatedAttribute('use_ssl', bool, default=False)
    """Whether to use a SSL secured connection."""

    user = ValidatedAttribute('user', default='sopel')
    """The "user" for your bot (the part before the @ in the hostname)."""

    verify_ssl = ValidatedAttribute('verify_ssl', bool, default=True)
    """Whether to require a trusted SSL certificate for SSL connections."""

    flood_burst_lines = ValidatedAttribute('flood_burst_lines', int, default=4)
    """How many messages can be sent in burst mode.

    .. versionadded:: 7.0
    """

    flood_empty_wait = ValidatedAttribute('flood_empty_wait', float, default=0.7)
    """How long to wait between sending messages when not in burst mode, in seconds.

    .. versionadded:: 7.0
    """

    flood_refill_rate = ValidatedAttribute('flood_refill_rate', int, default=1)
    """How quickly burst mode recovers, in messages per second.

    .. versionadded:: 7.0
    """
