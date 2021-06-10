# coding=utf-8

from __future__ import absolute_import, division, print_function, unicode_literals

import os.path

from sopel.config.types import (
    BooleanAttribute,
    ChoiceAttribute,
    FilenameAttribute,
    ListAttribute,
    NO_DEFAULT,
    SecretAttribute,
    StaticSection,
    ValidatedAttribute,
)
from sopel.tools import Identifier


COMMAND_DEFAULT_PREFIX = r'\.'
"""Default prefix used for commands."""
COMMAND_DEFAULT_HELP_PREFIX = '.'
"""Default help prefix used in commands' usage messages."""
URL_DEFAULT_SCHEMES = ['http', 'https', 'ftp']
"""Default URL schemes allowed for URLs."""


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

    .. note::

        You can use the command ``sopel configure`` to generate a config file
        with the minimal required options.

    """

    admins = ListAttribute('admins')
    """The list of people (other than the owner) who can administer the bot.

    Example:

    .. code-block:: ini

        admin =
            YourFavAdmin
            TheOtherAdmin
            YetAnotherRockstarAdmin
    """

    admin_accounts = ListAttribute('admin_accounts')
    """The list of admin accounts other than the owner's.

    Each account is allowed to administer the bot and can perform commands
    that are restricted to admins.

    Example:

    .. code-block:: ini

        admin_accounts =
            favadmin
            otheradm
            yetanotherone

    .. important::

        This should not be set for networks that do not support IRCv3 account
        capabilities. In that case, use :attr:`admins` instead.

    """

    alias_nicks = ListAttribute('alias_nicks')
    """List of alternate names users may call the bot.

    These aliases are used along with the bot's nick for ``$nick`` and
    ``$nickname`` regex substitutions.

    For example, a bot named "William" (its :attr:`nick`) could have these
    aliases:

    .. code-block:: ini

        alias_nicks =
            Bill
            Will
            Liam

    This would then allow both "William: Hi!" and "Bill: Hi!" to work with
    :func:`~sopel.plugin.nickname_command`.
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

    auth_password = SecretAttribute('auth_password')
    """The password to use to authenticate with the :attr:`auth_method`.

    See :ref:`Authentication`.
    """

    auth_target = ValidatedAttribute('auth_target')
    """Target for authentication.

    :default:
        * ``NickServ`` if using the ``nickserv`` :attr:`auth_method`
        * ``UserServ`` if using the ``userserv`` :attr:`auth_method`
        * ``PLAIN`` if using the ``sasl`` :attr:`auth_method`

    The nickname of the NickServ or UserServ service, or the name of the
    desired SASL mechanism, if :attr:`auth_method` is set to one of these
    methods. This value is otherwise ignored.

    See :ref:`Authentication`.
    """

    auth_username = ValidatedAttribute('auth_username')
    """The user/account name to use when authenticating.

    Required for an :attr:`auth_method` of ``authserv``, ``Q``, or
    ``userserv`` — otherwise ignored.

    See :ref:`Authentication`.
    """

    auto_url_schemes = ListAttribute(
        'auto_url_schemes',
        strip=True,
        default=URL_DEFAULT_SCHEMES)
    """List of URL schemes that will trigger URL callbacks.

    :default: ``['http', 'https', 'ftp']``

    Used by the URL callbacks feature to call plugins when links are posted in
    chat; see the :func:`sopel.plugin.url` decorator.

    The default value allows ``http``, ``https``, and ``ftp``. It is equivalent
    to this configuration example:

    .. code-block:: ini

        auto_url_schemes =
            http
            https
            ftp

    """

    bind_host = ValidatedAttribute('bind_host')
    """Bind the connection to a specific IP.

    :default: ``0.0.0.0`` (all interfaces)

    This is equivalent to the default value:

    .. code-block:: ini

        bind_host = 0.0.0.0

    """

    ca_certs = FilenameAttribute('ca_certs', default=_find_certs())
    """The path to the CA certs ``.pem`` file.

    Example:

    .. code-block:: ini

        ca_certs = /etc/ssl/certs/ca-certificates.crt

    If not specified, Sopel will try to find the certificate trust store
    itself from a set of known locations.

    If the given value is not an absolute path, it will be interpreted relative
    to the directory containing the config file with which Sopel was started.
    """

    channels = ListAttribute('channels')
    """List of channels for the bot to join when it connects.

    If a channel key needs to be provided, separate it from the channel name
    with a space:

    .. code-block:: ini

        channels =
            "#channel"
            "#logs"
            &rare_prefix_channel
            "#private password"

    .. important::

        If you edit the config file manually, make sure to wrap each line
        starting with a ``#`` in double quotes, as shown in the example above.
        An unquoted ``#`` denotes a comment, which will be ignored by Sopel's
        configuration parser.

    """

    commands_on_connect = ListAttribute('commands_on_connect')
    """A list of commands to send upon successful connection to the IRC server.

    Each line is a message that will be sent to the server once connected,
    in the order they are defined:

    .. code-block:: ini

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

    db_pass = SecretAttribute('db_pass')
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

    This is equivalent to the default value:

    .. code-block:: ini

        db_type = sqlite

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

    This is equivalent to the default value:

    .. code-block:: ini

        default_time_format = %Y-%m-%d - %T%Z

    .. seealso::

        Time format reference is available in the documentation for Python's
        :func:`time.strftime` function.

    """

    default_timezone = ValidatedAttribute('default_timezone', default='UTC')
    """The default timezone to use for time in messages.

    :default: ``UTC``

    .. highlight:: ini

    Used when plugins format times with :func:`sopel.tools.time.format_time`.

    For example, to make Sopel fall back on British time::

        default_timezone = Europe/London

    And this is equivalent to the default value::

        default_timezone = UTC

    """

    enable = ListAttribute('enable')
    """A list of the only plugins you want to enable.

    .. highlight:: ini

    If set, Sopel will *only* load the plugins named here. All other available
    plugins will be ignored::

        enable =
            url
            xkcd
            help

    In that case, only the ``url``, ``xkcd``, and ``help`` plugins will be
    enabled and loaded by Sopel.

    To load *all* available plugins, clear this setting by removing it, or
    by making it empty::

        enable =

    To disable only a few plugins, see :attr:`exclude`.

    .. seealso::

        The :ref:`Plugins` chapter for an overview of all plugin-related
        settings.

    """

    exclude = ListAttribute('exclude')
    """A list of plugins which should not be loaded.

    .. highlight:: ini

    If set, Sopel will load all available plugins *except* those named here::

        exclude =
            url
            calc
            meetbot

    In that case, ``url``, ``calc``, and ``meetbot`` will be excluded, and they
    won't be loaded by Sopel.

    A plugin named both here and in :attr:`enable` **will not** be loaded;
    :attr:`exclude` takes priority.

    .. seealso::

        The :ref:`Plugins` chapter for an overview of all plugin-related
        settings.

    """

    extra = ListAttribute('extra')
    """A list of other directories in which to search for plugin files.

    Example:

    .. code-block:: ini

        extra =
            /home/myuser/custom-sopel-plugins/
            /usr/local/lib/ad-hoc-plugins/

    .. seealso::

        The :ref:`Plugins` chapter for an overview of all plugin-related
        settings.

    """

    flood_burst_lines = ValidatedAttribute('flood_burst_lines', int, default=4)
    """How many messages can be sent in burst mode.

    :default: ``4``

    This is equivalent to the default value:

    .. code-block:: ini

        flood_burst_lines = 4

    .. seealso::

        The :ref:`Flood Prevention` chapter to learn what each flood-related
        setting does.

    .. versionadded:: 7.0
    """

    flood_empty_wait = ValidatedAttribute('flood_empty_wait', float, default=0.7)
    """How long to wait between sending messages when not in burst mode, in seconds.

    :default: ``0.7``

    This is equivalent to the default value:

    .. code-block:: ini

        flood_empty_wait = 0.7

    .. seealso::

        The :ref:`Flood Prevention` chapter to learn what each flood-related
        setting does.

    .. versionadded:: 7.0
    """

    flood_max_wait = ValidatedAttribute('flood_max_wait', float, default=2)
    """How much time to wait at most when flood protection kicks in.

    :default: ``2``

    This is equivalent to the default value:

    .. code-block:: ini

        flood_max_wait = 2

    .. seealso::

        The :ref:`Flood Prevention` chapter to learn what each flood-related
        setting does.

    .. versionadded:: 7.1
    """

    flood_penalty_ratio = ValidatedAttribute('flood_penalty_ratio',
                                             float,
                                             default=1.4)
    """Ratio of the message length used to compute the added wait penalty.

    :default: ``1.4``

    Messages longer than :attr:`flood_text_length` will get an added
    wait penalty (in seconds) that will be computed like this::

        overflow = max(0, (len(text) - flood_text_length))
        rate = flood_text_length * flood_penalty_ratio
        penalty = overflow / rate

    .. note::

        If the penalty ratio is 0, this penalty will be disabled.

    This is equivalent to the default value:

    .. code-block:: ini

        flood_penalty_ratio = 1.4

    .. seealso::

        The :ref:`Flood Prevention` chapter to learn what each flood-related
        setting does.

    .. versionadded:: 7.1
    """

    flood_refill_rate = ValidatedAttribute('flood_refill_rate', int, default=1)
    """How quickly burst mode recovers, in messages per second.

    :default: ``1``

    This is equivalent to the default value:

    .. code-block:: ini

        flood_refill_rate = 1

    .. seealso::

        The :ref:`Flood Prevention` chapter to learn what each flood-related
        setting does.

    .. versionadded:: 7.0
    """

    flood_text_length = ValidatedAttribute('flood_text_length', int, default=50)
    """Length of text at which an extra wait penalty is added.

    :default: ``50``

    Messages longer than this (in bytes) get an added wait penalty if the
    flood protection limit is reached.

    This is equivalent to the default value:

    .. code-block:: ini

        flood_text_length = 50

    .. seealso::

        The :ref:`Flood Prevention` chapter to learn what each flood-related
        setting does.

    .. versionadded:: 7.1
    """

    help_prefix = ValidatedAttribute('help_prefix',
                                     default=COMMAND_DEFAULT_HELP_PREFIX)
    """The prefix to use in help output.

    :default: ``.``

    This is equivalent to the default value:

    .. code-block:: ini

        help_prefix = .

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

    host = ValidatedAttribute('host', default='irc.libera.chat')
    """The IRC server to connect to.

    :default: ``irc.libera.chat``

    **Required**:

    .. code-block:: ini

        host = irc.libera.chat

    """

    host_blocks = ListAttribute('host_blocks')
    """A list of hostnames which Sopel should ignore.

    Messages from any user whose connection hostname matches one of these
    values will be ignored. :ref:`Regular expression syntax <re-syntax>`
    is supported, so remember to escape special characters:

    .. code-block:: ini

        host_blocks =
            (.+\\.)*domain\\.com

    .. seealso::

        The :attr:`nick_blocks` list can be used to block users by their nick.

    .. note::

        We are working on a better block system; see `issue #1355`__ for more
        information and update.

    .. __: https://github.com/sopel-irc/sopel/issues/1355

    """

    log_raw = BooleanAttribute('log_raw', default=False)
    """Whether a log of raw lines as sent and received should be kept.

    :default: ``no``

    To enable this logging:

    .. code-block:: ini

        log_raw = yes

    .. seealso::

        The :ref:`Raw Logs` chapter.

    """

    logdir = FilenameAttribute('logdir', directory=True, default='logs')
    """Directory in which to place logs.

    :default: ``logs``

    If the given value is not an absolute path, it will be interpreted relative
    to the directory containing the config file with which Sopel was started.

    .. seealso::

        The :ref:`Logging` chapter.

    """

    logging_channel = ValidatedAttribute('logging_channel', Identifier)
    """The channel to send logging messages to.

    .. seealso::

        The :ref:`Log to a Channel` chapter.

    """

    logging_channel_datefmt = ValidatedAttribute('logging_channel_datefmt')
    """The format string to use for timestamps in IRC channel logs.

    If not specified, this falls back to using :attr:`logging_datefmt`.

    .. seealso::

        Time format reference is available in the documentation for Python's
        :func:`time.strftime` function.

        For more information about logging, see :ref:`Log to a Channel`.

    .. versionadded:: 7.0
    """

    logging_channel_format = ValidatedAttribute('logging_channel_format')
    """The logging format string to use in IRC channel logs.

    If not specified, this falls back to using :attr:`logging_format`.

    .. seealso::

        The :ref:`Log to a Channel` chapter.

    .. versionadded:: 7.0
    """

    logging_channel_level = ChoiceAttribute('logging_channel_level',
                                            ['CRITICAL', 'ERROR', 'WARNING',
                                             'INFO', 'DEBUG'],
                                            'WARNING')
    """The lowest severity of logs to display in IRC channel logs.

    If not specified, this falls back to using :attr:`logging_level`.

    .. seealso::

        The :ref:`Log to a Channel` chapter.

    .. versionadded:: 7.0
    """

    logging_datefmt = ValidatedAttribute('logging_datefmt')
    """The format string to use for timestamps in logs.

    If not set, the ``datefmt`` argument is not provided, and :mod:`logging`
    will use the Python default.

    .. seealso::

        Time format reference is available in the documentation for Python's
        :func:`time.strftime` function.

    .. versionadded:: 7.0
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

    This is equivalent to the default value:

    .. code-block:: ini

       logging_format = [%(asctime)s] %(name)-20s %(levelname)-8s - %(message)s

    .. seealso::

        Python's logging format documentation: :ref:`logrecord-attributes`

    .. versionadded:: 7.0
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

    For example to log only at WARNING level and above:

    .. code-block:: ini

        logging_level = WARNING

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

    **Required**:

    .. code-block:: ini

        nick = Sopel

    """

    nick_auth_method = ChoiceAttribute('nick_auth_method', choices=[
        'nickserv', 'authserv', 'Q', 'userserv'])
    """The nick authentication method.

    Can be one of ``nickserv``, ``authserv``, ``Q``, or ``userserv``.

    .. seealso::

        The :ref:`Authentication` chapter for more details.

    .. versionadded:: 7.0
    """

    nick_auth_password = SecretAttribute('nick_auth_password')
    """The password to use to authenticate the bot's nick.

    .. seealso::

        The :ref:`Authentication` chapter for more details.

    .. versionadded:: 7.0
    """

    nick_auth_target = ValidatedAttribute('nick_auth_target')
    """The target user for nick authentication.

    :default: ``NickServ`` for ``nickserv`` authentication; ``UserServ`` for
              ``userserv`` authentication

    May not apply, depending on the chosen :attr:`nick_auth_method`.

    .. seealso::

        The :ref:`Authentication` chapter for more details.

    .. versionadded:: 7.0
    """

    nick_auth_username = ValidatedAttribute('nick_auth_username')
    """The username/account to use for nick authentication.

    :default: the value of :attr:`nick`

    May not apply, depending on the chosen :attr:`nick_auth_method`.

    .. seealso::

        The :ref:`Authentication` chapter for more details.

    .. versionadded:: 7.0
    """

    nick_blocks = ListAttribute('nick_blocks')
    """A list of nicks which Sopel should ignore.

    Messages from any user whose nickname matches one of these values will be
    ignored. :ref:`Regular expression syntax <re-syntax>` is supported, so
    remember to escape special characters:

    .. code-block:: ini

        nick_blocks =
            ExactNick
            _*RegexMatch_*

    .. seealso::

        The :attr:`host_blocks` list can be used to block users by their host.

    .. note::

        We are working on a better block system; see `issue #1355`__ for more
        information and update.

    .. __: https://github.com/sopel-irc/sopel/issues/1355

    """

    not_configured = BooleanAttribute('not_configured', default=False)
    """For package maintainers. Not used in normal configurations.

    :default: ``False``

    This allows software packages to install a default config file, with this
    option set to ``True``, so that commands to start, stop, or restart the bot
    won't work until the bot has been properly configured.
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

    .. highlight:: ini

    **Required**::

        port = 6667

    And usually when SSL is enabled::

        port = 6697
        use_ssl = yes

    """

    prefix = ValidatedAttribute('prefix', default=COMMAND_DEFAULT_PREFIX)
    """The prefix to add to the beginning of commands as a regular expression.

    :default: ``\\.``

    .. highlight:: ini

    **Required**::

        prefix = \\.

    With the default value, users will invoke commands like this:

    .. code-block:: irc

        <nick> .help

    Since it's a regular expression, you can use multiple prefixes::

        prefix = \\.|\\?

    .. important::

        As the prefix is a regular expression, don't forget to escape it when
        necessary. It is not recommended to use capturing groups, as it
        **will** create problems with argument parsing for commands.

    .. note::

        Remember to change the :attr:`help_prefix` value accordingly::

            prefix = \\?
            help_prefix = ?

        In that example, users will invoke commands like this:

        .. code-block:: irc

            <nick> ?help xkcd
            <Sopel> ?xkcd - Finds an xkcd comic strip
            <Sopel> Takes one of 3 inputs:
            [...]

    """

    reply_errors = BooleanAttribute('reply_errors', default=True)
    """Whether to reply to the sender of a message that triggered an error.

    :default: ``True``

    If ``True``, Sopel will send information about the triggered exception to
    the sender of the message that caused the error.

    If ``False``, Sopel will only log the error and will appear to fail
    silently from the triggering IRC user's perspective.
    """

    server_auth_method = ChoiceAttribute('server_auth_method',
                                         choices=['sasl', 'server'])
    """The server authentication method.

    Can be ``sasl`` or ``server``.

    .. versionadded:: 7.0
    """

    server_auth_password = SecretAttribute('server_auth_password')
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

    In this example, Sopel will try to join 4 channels at a time:

    .. code-block:: ini

        throttle_join = 4

    .. seealso::

        :attr:`throttle_wait` controls Sopel's waiting time between joining
        batches of channels.

    """

    throttle_wait = ValidatedAttribute('throttle_wait', int, default=1)
    """Time in seconds Sopel waits between joining batches of channels.

    :default: ``1``

    In this example:

    .. code-block:: ini

        throttle_wait = 5
        throttle_join = 2

    Sopel will join 2 channels every 5s.

    If :attr:`throttle_join` is ``0``, this setting has no effect.

    .. seealso::

        :attr:`throttle_join` controls channel batch size.

    """

    timeout = ValidatedAttribute('timeout', int, default=120)
    """The number of seconds acceptable since the last message before timing out.

    :default: ``120``

    You can change the timeout like this:

    .. code-block:: ini

        # increase to 200 seconds
        timeout = 200

    """

    timeout_ping_interval = ValidatedAttribute('timeout_ping_interval',
                                               int,
                                               default=0)
    """The number of seconds before sending a PING command to the server.

    :default: (auto)

    The default value is made to send at least 2 PINGs before the bot thinks
    there is a timeout, given that :attr:`timeout` is 120s by default:

    * t+54s: first PING
    * t+108s: second PING
    * t+120s: if no response, then a timeout is detected

    This makes the timeout detection more lenient and forgiving, by allowing a
    12s window for the server to send something that will prevent a timeout.

    You can change the PING interval like this:

    .. code-block:: ini

        # timeout up to 250s
        timeout = 250
        # PING every 80s (about 3 times every 240s + 10s window)
        timeout_ping_interval = 80

    .. note::

        Internally, the default value is 0 and the value used will be
        automatically calculated as 45% of the :attr:`timeout`::

            ping_interval = timeout * 0.45

        So for a timeout of 120s it's a PING every 54s. For a timeout of 250s
        it's a PING every 112.5s.

    """

    use_ssl = BooleanAttribute('use_ssl', default=False)
    """Whether to use a SSL/TLS encrypted connection.

    :default: ``False``

    Example with SSL on:

    .. code-block:: ini

        use_ssl = yes

    """

    user = ValidatedAttribute('user', default='sopel')
    """The "user" for your bot (the part before the ``@`` in the hostname).

    :default: ``sopel``

    **Required**:

    .. code-block:: ini

        user = sopel

    """

    verify_ssl = BooleanAttribute('verify_ssl', default=True)
    """Whether to require a trusted certificate for encrypted connections.

    :default: ``True``

    Example with SSL on:

    .. code-block:: ini

        use_ssl = yes
        verify_ssl = yes

    """
