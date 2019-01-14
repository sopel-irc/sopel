# coding=utf-8

from __future__ import unicode_literals, absolute_import, print_function, division

import os.path

from sopel.config.types import (
    StaticSection, ValidatedAttribute, ListAttribute, ChoiceAttribute,
    FilenameAttribute, NO_DEFAULT
)
from sopel.tools import Identifier


def _find_certs():
    """
    Find the TLS root CA store.

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


class CoreSection(StaticSection):
    """The config section used for configuring the bot itself."""
    admins = ListAttribute('admins')
    """The list of people (other than the owner) who can administer the bot"""

    admin_accounts = ListAttribute('admin_accounts')
    """The list of accounts (other than the owner's) who can administer the bot.

    This should not be set for networks that do not support IRCv3 account
    capabilities."""

    alias_nicks = ListAttribute('alias_nicks')
    """List of alternate names recognized as the bot's nick for $nick and
    $nickname regex substitutions"""

    auth_method = ChoiceAttribute('auth_method', choices=[
        'nickserv', 'authserv', 'Q', 'sasl', 'server', 'userserv'])
    """The method to use to authenticate with the server.

    Can be ``nickserv``, ``authserv``, ``Q``, ``sasl``, or ``server`` or ``userserv``."""

    auth_password = ValidatedAttribute('auth_password')
    """The password to use to authenticate with the server."""

    auth_target = ValidatedAttribute('auth_target')
    """The user to use for nickserv authentication, or the SASL mechanism.

    May not apply, depending on ``auth_method``. Defaults to NickServ for
    nickserv auth, and PLAIN for SASL auth."""

    auth_username = ValidatedAttribute('auth_username')
    """The username/account to use to authenticate with the server.

    May not apply, depending on ``auth_method``."""

    bind_host = ValidatedAttribute('bind_host')
    """Bind the connection to a specific IP"""

    ca_certs = FilenameAttribute('ca_certs', default=_find_certs())
    """The path of the CA certs pem file"""

    channels = ListAttribute('channels')
    """List of channels for the bot to join when it connects"""

    db_filename = ValidatedAttribute('db_filename')
    """The filename for Sopel's database."""

    default_time_format = ValidatedAttribute('default_time_format',
                                             default='%Y-%m-%d - %T%Z')
    """The default format to use for time in messages."""

    default_timezone = ValidatedAttribute('default_timezone', default='UTC')
    """The default timezone to use for time in messages."""

    enable = ListAttribute('enable')
    """A whitelist of the only modules you want to enable."""

    exclude = ListAttribute('exclude')
    """A list of modules which should not be loaded."""

    extra = ListAttribute('extra')
    """A list of other directories you'd like to include modules from."""

    help_prefix = ValidatedAttribute('help_prefix', default='.')
    """The prefix to use in help"""

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

    Regular expression syntax is used"""

    log_raw = ValidatedAttribute('log_raw', bool, default=False)
    """Whether a log of raw lines as sent and received should be kept."""

    logdir = FilenameAttribute('logdir', directory=True, default='logs')
    """Directory in which to place logs."""

    logging_channel = ValidatedAttribute('logging_channel', Identifier)
    """The channel to send logging messages to."""

    logging_level = ChoiceAttribute('logging_level',
                                    ['CRITICAL', 'ERROR', 'WARNING', 'INFO',
                                     'DEBUG'],
                                    'WARNING')
    """The lowest severity of logs to display."""

    modes = ValidatedAttribute('modes', default='B')
    """User modes to be set on connection."""

    name = ValidatedAttribute('name', default='Sopel: https://sopel.chat')
    """The "real name" of your bot for WHOIS responses."""

    nick = ValidatedAttribute('nick', Identifier, default=Identifier('Sopel'))
    """The nickname for the bot"""

    nick_blocks = ListAttribute('nick_blocks')
    """A list of nicks which Sopel should ignore.

    Regular expression syntax is used."""

    not_configured = ValidatedAttribute('not_configured', bool, default=False)
    """For package maintainers. Not used in normal configurations.

    This allows software packages to install a default config file, with this
    set to true, so that the bot will not run until it has been properly
    configured."""

    owner = ValidatedAttribute('owner', default=NO_DEFAULT)
    """The IRC name of the owner of the bot."""

    owner_account = ValidatedAttribute('owner_account')
    """The services account name of the owner of the bot.

    This should only be set on networks which support IRCv3 account
    capabilities.
    """

    pid_dir = FilenameAttribute('pid_dir', directory=True, default='.')
    """The directory in which to put the file Sopel uses to track its process ID.

    You probably do not need to change this unless you're managing Sopel with
    systemd or similar."""

    port = ValidatedAttribute('port', int, default=6667)
    """The port to connect on."""

    prefix = ValidatedAttribute('prefix', default='\\.')
    """The prefix to add to the beginning of commands.

    It is a regular expression (so the default, ``\\.``, means commands start
    with a period), though using capturing groups will create problems."""

    reply_errors = ValidatedAttribute('reply_errors', bool, default=True)
    """Whether to message the sender of a message that triggered an error with the exception."""

    throttle_join = ValidatedAttribute('throttle_join', int)
    """Slow down the initial join of channels to prevent getting kicked.

    Sopel will only join this many channels at a time, sleeping for a second
    between each batch. This is unnecessary on most networks."""

    timeout = ValidatedAttribute('timeout', int, default=120)
    """The amount of time acceptable between pings before timing out."""

    use_ssl = ValidatedAttribute('use_ssl', bool, default=False)
    """Whether to use a SSL secured connection."""

    user = ValidatedAttribute('user', default='sopel')
    """The "user" for your bot (the part before the @ in the hostname)."""

    verify_ssl = ValidatedAttribute('verify_ssl', bool, default=True)
    """Whether to require a trusted SSL certificate for SSL connections."""
