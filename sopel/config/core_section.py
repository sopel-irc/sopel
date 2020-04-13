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

    :returns: path to CA store file
    :rtype: str
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
    """Interactively configure the bot's ``[core]`` config section.

    :param config: the bot's config object
    :type config: :class:`~.config.Config`
    """
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
    """The config section used for configuring the bot itself.

    .. important::
        All **Required** values must be specified, or Sopel will fail to start.
    """

    admins = ListAttribute('admins')
    """The list of people (other than the owner) who can administer the bot."""

    admin_accounts = ListAttribute('admin_accounts')
    """The list of admin accounts other than the owner's.

    Each account is allowed to administer the bot and can perform commands
    that are restricted to admins.

    .. important::
        This should not be set for networks that do not support IRCv3 account
        capabilities.
    """

    alias_nicks = ListAttribute('alias_nicks')
    """List of alternate names users may call the bot.

    These aliases are used along with the bot's nick for ``$nick`` and
    ``$nickname`` regex substitutions.

    For example, a bot named "William" (its :attr:`nick`) could have aliases
    "Bill", "Will", and "Liam". This would then allow both "William: Hi!" and
    "Bill: Hi!" to work with :func:`~sopel.module.nickname_commands`.
    """

    auth_method = ChoiceAttribute('auth_method', choices=[
        'nickserv', 'authserv', 'Q', 'sasl', 'server', 'userserv'])
    """Simple method to authenticate with the server.

    Can be one of ``nickserv``, ``authserv``, ``Q``, ``sasl``, ``server``, or
    ``userserv``.

    This allows only a single authentication method; to use both a server-based
    authentication method *and* a nick-based authentication method, see
    :attr:`server_auth_method` and :attr:`nick_auth_method`.

    For more information about these methods, see :ref:`Authentication`.

    .. note::
        If this is specified, :attr:`nick_auth_method` will be ignored, and this
        value will override :attr:`server_auth_method`.
    """

    auth_password = ValidatedAttribute('auth_password')
    """The password to use to authenticate with the :attr:`auth_method`.

    See :ref:`Authentication`.
    """

    auth_target = ValidatedAttribute('auth_target')
    """Target for authentication.

    :default:
        * ``NickServ`` if using the ``nickserv`` :attr:`auth_method`
        * ``PLAIN`` if using the ``sasl`` :attr:`auth_method`

    The nickname of the NickServ service, or the name of the desired SASL
    mechanism, if :attr:`auth_method` is set to one of these methods. This value
    is otherwise ignored.

    See :ref:`Authentication`.
    """

    auth_username = ValidatedAttribute('auth_username')
    """The user/account name to use when authenticating.

    May not apply, depending on :attr:`auth_method`. See :ref:`Authentication`.
    """

    auto_url_schemes = ListAttribute(
        'auto_url_schemes',
        strip=True,
        default=['http', 'https', 'ftp'])
    """List of URL schemes that will trigger URL callbacks.

    :default: ``['http', 'https', 'ftp']``

    Used by the URL callbacks feature to call plugins when links are posted in
    chat; see the :func:`sopel.module.url` decorator.

    The default value allows ``http``, ``https``, and ``ftp``.
    """

    bind_host = ValidatedAttribute('bind_host')
    """Bind the connection to a specific IP.

    :default: ``0.0.0.0`` (all interfaces)
    """

    ca_certs = FilenameAttribute('ca_certs', default=_find_certs())
    """The path to the CA certs ``.pem`` file.

    If not specified, Sopel will try to find the certificate trust store itself.
    """

    channels = ListAttribute('channels')
    """List of channels for the bot to join when it connects.

    If a channel key needs to be provided, separate it from the channel name
    with a space, e.g. ``"#channel password"``.
    """

    commands_on_connect = ListAttribute('commands_on_connect')
    """A list of commands to send upon successful connection to the IRC server.

    Each line is a message that will be sent to the server once connected.
    Example::

        commands_on_connect =
            PRIVMSG Q@CServe.quakenet.org :AUTH my_username MyPassword,@#$%!
            PRIVMSG MyOwner :I'm here!

    ``$nickname`` can be used in a command as a placeholder, and will be
    replaced with the bot's :attr:`nick`. For example, if the bot's nick is
    ``Sopel``, ``MODE $nickname +Xxw`` will be expanded to ``MODE Sopel +Xxw``.

    .. versionadded:: 7.0
    """

    db_driver = ValidatedAttribute('db_driver')
    """The driver to use for connecting to the database.

    This is optional, but can be specified if user wants to use a different
    driver than the default for the chosen :attr:`db_type`.

    .. seealso::

        Refer to :ref:`SQLAlchemy's documentation <engines_toplevel>` for more
        information.

    """

    db_filename = ValidatedAttribute('db_filename')
    """The filename for Sopel's database.

    Used only for SQLite. Ignored for all other :attr:`db_type` values.
    """

    db_host = ValidatedAttribute('db_host')
    """The host for Sopel's database.

    Ignored when using SQLite.
    """

    db_name = ValidatedAttribute('db_name')
    """The name of Sopel's database.

    Ignored when using SQLite.
    """

    db_pass = ValidatedAttribute('db_pass')
    """The password for Sopel's database.

    Ignored when using SQLite.
    """

    db_port = ValidatedAttribute('db_port')
    """The port for Sopel's database.

    Ignored when using SQLite.
    """

    db_type = ChoiceAttribute('db_type', choices=[
        'sqlite', 'mysql', 'postgres', 'mssql', 'oracle', 'firebird', 'sybase'], default='sqlite')
    """The type of database Sopel should connect to.

    :default: ``sqlite`` (part of Python's standard library)

    The full list of values Sopel recognizes is:

    * ``firebird``
    * ``mssql``
    * ``mysql``
    * ``oracle``
    * ``postgres``
    * ``sqlite``
    * ``sybase``

    Here are the additional PyPI packages you may need to install to use one of
    the most commonly requested alternatives:

    mysql
      ``pip install mysql-python`` (Python 2)

      ``pip install mysqlclient`` (Python 3)

    postgres
      ``pip install psycopg2``

    mssql
      ``pip install pymssql``

    .. seealso::

        Refer to :ref:`SQLAlchemy's documentation <dialect_toplevel>` for more
        information about the different dialects it supports.

    .. note::

        Plugins originally written for Sopel 6.x and older *might* not work
        correctly with ``db_type``\\s other than ``sqlite``.

    """

    db_user = ValidatedAttribute('db_user')
    """The user for Sopel's database.

    Ignored when using SQLite.
    """

    default_time_format = ValidatedAttribute('default_time_format',
                                             default='%Y-%m-%d - %T%Z')
    """The default format to use for time in messages.

    :default: ``%Y-%m-%d - %T%Z``

    Used when plugins format times with :func:`sopel.tools.time.format_time`.

    .. seealso::

        Time format reference is available in the documentation for Python's
        :func:`time.strftime` function.

    """

    default_timezone = ValidatedAttribute('default_timezone', default='UTC')
    """The default timezone to use for time in messages.

    :default: ``UTC``

    Used when plugins format times with :func:`sopel.tools.time.format_time`.
    """

    enable = ListAttribute('enable')
    """A list of the only plugins you want to enable.

    If set, Sopel will *only* load the plugins named here. All other available
    plugins will be ignored.

    To load *all* available plugins, clear this setting.

    To disable only a few plugins, see :attr:`exclude`.

    See :ref:`Plugins` for an overview of all plugin-related settings.
    """

    exclude = ListAttribute('exclude')
    """A list of plugins which should not be loaded.

    If set, Sopel will load all available plugins *except* those named here.

    A plugin named both here and in :attr:`enable` **will not** be loaded;
    :attr:`exclude` takes priority.

    See :ref:`Plugins` for an overview of all plugin-related settings.
    """

    extra = ListAttribute('extra')
    """A list of other directories in which to search for plugin files.

    See :ref:`Plugins` for an overview of all plugin-related settings.
    """

    flood_burst_lines = ValidatedAttribute('flood_burst_lines', int, default=4)
    """How many messages can be sent in burst mode.

    :default: ``4``

    See :ref:`Flood Prevention` to learn what each flood-related setting does.

    .. versionadded:: 7.0
    """

    flood_empty_wait = ValidatedAttribute('flood_empty_wait', float, default=0.7)
    """How long to wait between sending messages when not in burst mode, in seconds.

    :default: ``0.7``

    See :ref:`Flood Prevention` to learn what each flood-related setting does.

    .. versionadded:: 7.0
    """

    flood_refill_rate = ValidatedAttribute('flood_refill_rate', int, default=1)
    """How quickly burst mode recovers, in messages per second.

    :default: ``1``

    See :ref:`Flood Prevention` to learn what each flood-related setting does.

    .. versionadded:: 7.0
    """

    help_prefix = ValidatedAttribute('help_prefix', default='.')
    """The prefix to use in help output.

    :default: ``.``

    If :attr:`prefix` is changed from the default, this setting **must** be
    updated to reflect the prefix your bot will actually respond to, or the
    built-in ``help`` functionality will provide incorrect example usage.
    """

    @property
    def homedir(self):
        """The directory in which various files are stored at runtime.

        By default, this is the same directory as the config file. It cannot be
        changed at runtime.
        """
        return self._parent.homedir

    host = ValidatedAttribute('host', default='chat.freenode.net')
    """The IRC server to connect to.

    :default: ``chat.freenode.net``

    **Required.**
    """

    host_blocks = ListAttribute('host_blocks')
    """A list of hostnames which Sopel should ignore.

    Messages from any user whose connection hostname matches one of these values
    will be ignored. :ref:`Regular expression syntax <re-syntax>` is supported.

    Also see the :attr:`nick_blocks` list.
    """

    log_raw = ValidatedAttribute('log_raw', bool, default=False)
    """Whether a log of raw lines as sent and received should be kept.

    See :ref:`Raw Logs`.
    """

    logdir = FilenameAttribute('logdir', directory=True, default='logs')
    """Directory in which to place logs.

    See :ref:`Logging`.
    """

    logging_channel = ValidatedAttribute('logging_channel', Identifier)
    """The channel to send logging messages to.

    See :ref:`Log to a Channel`.
    """

    logging_channel_datefmt = ValidatedAttribute('logging_channel_datefmt')
    """The format string to use for timestamps in IRC channel logs.

    If not specified, this falls back to using :attr:`logging_datefmt`.

    See :ref:`Log to a Channel`.

    .. versionadded:: 7.0
    .. seealso::

        Time format reference is available in the documentation for Python's
        :func:`time.strftime` function.

    """

    logging_channel_format = ValidatedAttribute('logging_channel_format')
    """The logging format string to use in IRC channel logs.

    If not specified, this falls back to using :attr:`logging_format`.

    See :ref:`Log to a Channel`.

    .. versionadded:: 7.0
    """

    logging_channel_level = ChoiceAttribute('logging_channel_level',
                                            ['CRITICAL', 'ERROR', 'WARNING',
                                             'INFO', 'DEBUG'],
                                            'WARNING')
    """The lowest severity of logs to display in IRC channel logs.

    If not specified, this falls back to using :attr:`logging_level`.

    See :ref:`Log to a Channel`.

    .. versionadded:: 7.0
    """

    logging_datefmt = ValidatedAttribute('logging_datefmt')
    """The format string to use for timestamps in logs.

    If not set, the ``datefmt`` argument is not provided, and :mod:`logging`
    will use the Python default.

    .. versionadded:: 7.0
    .. seealso::

        Time format reference is available in the documentation for Python's
        :func:`time.strftime` function.

    """

    logging_format = ValidatedAttribute(
        'logging_format',
        default='[%(asctime)s] %(name)-20s %(levelname)-8s - %(message)s')
    """The logging format string to use for logs.

    :default: ``[%(asctime)s] %(name)-20s %(levelname)-8s - %(message)s``

    The default log line format will output the timestamp, the package that
    generated the log line, the log level of the line, and (finally) the actual
    message. For example::

        [2019-10-21 12:47:44,272] sopel.irc            INFO     - Connected.

    .. versionadded:: 7.0
    .. seealso::
        Python's logging format documentation: :ref:`logrecord-attributes`
    """

    logging_level = ChoiceAttribute('logging_level',
                                    ['CRITICAL', 'ERROR', 'WARNING', 'INFO',
                                     'DEBUG'],
                                    'INFO')
    """The lowest severity of logs to display.

    :default: ``INFO``

    Valid values sorted by increasing verbosity:

    * ``CRITICAL``
    * ``ERROR``
    * ``WARNING``
    * ``INFO``
    * ``DEBUG``
    """

    modes = ValidatedAttribute('modes', default='B')
    """User modes to be set on connection.

    :default: ``B``

    Include only the mode letters; this value is automatically prefixed with
    ``+`` before Sopel sends the MODE command to IRC.
    """

    name = ValidatedAttribute('name', default='Sopel: https://sopel.chat/')
    """The "real name" of your bot for ``WHOIS`` responses.

    :default: ``Sopel: https://sopel.chat/``
    """

    nick = ValidatedAttribute('nick', Identifier, default=Identifier('Sopel'))
    """The nickname for the bot.

    :default: ``Sopel``

    **Required.**
    """

    nick_auth_method = ChoiceAttribute('nick_auth_method', choices=[
        'nickserv', 'authserv', 'Q', 'userserv'])
    """The nick authentication method.

    Can be one of ``nickserv``, ``authserv``, ``Q``, or ``userserv``.

    See :ref:`Authentication` for more details.

    .. versionadded:: 7.0
    """

    nick_auth_password = ValidatedAttribute('nick_auth_password')
    """The password to use to authenticate the bot's nick.

    See :ref:`Authentication` for more details.

    .. versionadded:: 7.0
    """

    nick_auth_target = ValidatedAttribute('nick_auth_target')
    """The target user for nick authentication.

    :default: ``NickServ`` for ``nickserv`` authentication; ``UserServ`` for
              ``userserv`` authentication

    May not apply, depending on the chosen :attr:`nick_auth_method`. See
    :ref:`Authentication` for more details.

    .. versionadded:: 7.0
    """

    nick_auth_username = ValidatedAttribute('nick_auth_username')
    """The username/account to use for nick authentication.

    :default: the value of :attr:`nick`

    May not apply, depending on the chosen :attr:`nick_auth_method`. See
    :ref:`Authentication` for more details.

    .. versionadded:: 7.0
    """

    nick_blocks = ListAttribute('nick_blocks')
    """A list of nicks which Sopel should ignore.

    Messages from any user whose nickname matches one of these values will be
    ignored. :ref:`Regular expression syntax <re-syntax>` is supported.

    Also see the :attr:`host_blocks` list.
    """

    not_configured = ValidatedAttribute('not_configured', bool, default=False)
    """For package maintainers. Not used in normal configurations.

    :default: ``False``

    This allows software packages to install a default config file, with this
    option set to ``True``, so that the bot will not run until it has been
    properly configured.
    """

    owner = ValidatedAttribute('owner', default=NO_DEFAULT)
    """The IRC name of the owner of the bot.

    **Required** even if :attr:`owner_account` is set.
    """

    owner_account = ValidatedAttribute('owner_account')
    """The services account name of the owner of the bot.

    This should only be set on networks which support IRCv3 account
    capabilities.
    """

    pid_dir = FilenameAttribute('pid_dir', directory=True, default='.')
    """The directory in which to put the file Sopel uses to track its process ID.

    :default: ``.``

    If the given value is not an absolute path, it will be interpreted relative
    to the directory containing the config file with which Sopel was started.

    You probably do not need to change this unless you're managing Sopel with
    ``systemd`` or similar.
    """

    port = ValidatedAttribute('port', int, default=6667)
    """The port to connect on.

    :default: ``6667`` normally; ``6697`` if :attr:`use_ssl` is ``True``

    **Required.**
    """

    prefix = ValidatedAttribute('prefix', default='\\.')
    """The prefix to add to the beginning of commands.

    :default: ``\\.``

    **Required.**

    It is a regular expression (so the default, ``\\.``, means commands start
    with a period), though using capturing groups will create problems.
    """

    reply_errors = ValidatedAttribute('reply_errors', bool, default=True)
    """Whether to reply to the sender of a message that triggered an error.

    :default: ``True``

    If ``True``, Sopel will send information about the triggered exception to
    the sender of the message that caused the error.

    If ``False``, Sopel will only log the error and will appear to fail silently
    from the triggering IRC user's perspective.
    """

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

    :default: ``PLAIN``

    .. versionadded:: 7.0
    """

    server_auth_username = ValidatedAttribute('server_auth_username')
    """The username/account to use to authenticate with the server.

    .. versionadded:: 7.0
    """

    throttle_join = ValidatedAttribute('throttle_join', int, default=0)
    """Slow down the initial join of channels to prevent getting kicked.

    :default: ``0``

    Sopel will only join this many channels at a time, sleeping for a second
    between each batch to avoid getting kicked for joining too quickly. This is
    unnecessary on most networks.

    If not set, or set to 0, Sopel won't slow down the initial join.

    .. seealso::

        :attr:`throttle_wait` controls Sopel's waiting time between joining
        batches of channels.

    """

    throttle_wait = ValidatedAttribute('throttle_wait', int, default=1)
    """Time in seconds Sopel waits between joining batches of channels.

    :default: ``1``

    For example, with ``throttle_join = 2`` and ``throttle_wait = 5`` it will
    wait 5s every 2 channels it joins.

    If :attr:`throttle_join` is ``0``, this setting has no effect.

    .. seealso::

        :attr:`throttle_join` controls channel batch size.

    """

    timeout = ValidatedAttribute('timeout', int, default=120)
    """The number of seconds acceptable between pings before timing out.

    :default: ``120``
    """

    use_ssl = ValidatedAttribute('use_ssl', bool, default=False)
    """Whether to use a SSL/TLS encrypted connection.

    :default: ``False``
    """

    user = ValidatedAttribute('user', default='sopel')
    """The "user" for your bot (the part before the ``@`` in the hostname).

    :default: ``sopel``

    **Required.**
    """

    verify_ssl = ValidatedAttribute('verify_ssl', bool, default=True)
    """Whether to require a trusted certificate for encrypted connections.

    :default: ``True``
    """
