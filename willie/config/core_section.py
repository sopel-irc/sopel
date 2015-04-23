# coding=utf8

from __future__ import unicode_literals
from __future__ import print_function

from willie.config.types import (
    StaticSection, ValidatedAttribute, ListAttribute, ChoiceAttribute,
    FilenameAttribute, _HomedirAttribute
)
from willie.tools import Identifier


class CoreSection(StaticSection):
    admins = ListAttribute('admins')
    """The list of people (other than the owner) who can administer the bot"""

    auth_method = ChoiceAttribute('auth_method', ['nickserv', 'authserv',
                                                  'sasl', 'server'])
    """The method to use to authenticate with the server.

    Can be ``nickserv``, ``authserv``, ``sasl``, or ``server``."""

    auth_password = ValidatedAttribute('auth_password')
    """The password to use to authenticate with the server."""

    auth_target = ValidatedAttribute('auth_target')
    """The user to use for nickserv authentication.

    May not apply, depending on ``auth_method``"""

    auth_username = ValidatedAttribute('auth_username')
    """The username/account to use to authenticate with the server.

    May not apply, depending on ``auth_method``."""

    bind_host = ValidatedAttribute('bind_host')
    """Bind the connection to a specific IP"""

    ca_certs = FilenameAttribute('ca_certs', default='/etc/pki/tls/cert.pem')
    """The path of the CA certs pem file"""

    channels = ListAttribute('channels')
    """List of channels for the bot to join when it connects"""

    db_filename = ValidatedAttribute('db_filename')
    """The filename for Willie's database."""

    default_time_format = ValidatedAttribute('default_time_format',
                                             default='%F - %T%Z')
    """The default format to use for time in messages."""

    default_timezone = ValidatedAttribute('default_timezone')
    """The default timezone to use for time in messages."""

    enable = ListAttribute('enable')
    """A whitelist of the only modules you want to enable."""

    exclude = ListAttribute('exclude')
    """A list of modules which should not be loaded."""

    extra = ListAttribute('extra')
    """A list of other directories you'd like to include modules from."""

    help_prefix = ValidatedAttribute('help_prefix', default='.')
    """The prefix to use in help"""

    homedir = _HomedirAttribute()
    """The directory in which the configuration and some other data are stored.
    """

    host = ValidatedAttribute('host')
    """The server to connect to."""

    host_blocks = ListAttribute('host_blocks')
    """A list of hostmasks which Willie should ignore.

    Regular expression syntax is used"""

    log_raw = ValidatedAttribute('log_raw', bool, default=True)
    """Whether a log of raw lines as sent and recieved should be kept."""

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

    name = ValidatedAttribute('name', default='Willie: http://willie.dftba.net')
    """The "real name" of your bot for WHOIS responses."""

    nick = ValidatedAttribute('nick', Identifier, default=Identifier('Willie'))
    """The nickname for the bot"""

    nick_blocks = ListAttribute('nick_blocks')
    """A list of nicks which Willie should ignore.

    Regular expression syntax is used."""

    not_configured = ValidatedAttribute('not_configured', bool, default=False)
    """For package maintainers. Not used in normal configurations.

    This allows software packages to install a default config file, with this
    set to true, so that the bot will not run until it has been properly
    configured."""

    owner = ValidatedAttribute('owner')
    """The IRC name of the owner of the bot."""

    pid_file_path = FilenameAttribute('pid_file_path')
    """The path of the file Willie uses to track its process ID.

    You probably do not need to change this unless you're managing Willie with
    systemd or similar."""

    port = ValidatedAttribute('port', int, default=6667)
    """The port to connect on."""

    prefix = ValidatedAttribute('prefix', default='\.')
    """The prefix to add to the beginning of commands.

    It is a regular expression (so the default, ``\.``, means commands start
    with a period), though using capturing groups will create problems."""

    timeout = ValidatedAttribute('timeout', int, default=120)
    """The amount of time acceptable between pings before timing out."""

    use_ssl = ValidatedAttribute('use_ssl', bool, default=False)
    """Whether to use a SSL secured connection."""

    user = ValidatedAttribute('user', default='willie')
    """The "user" for your bot (the part before the @ in the hostname)."""

    verify_ssl = ValidatedAttribute('verify_ssl', default=True)
    """Whether to require a trusted SSL certificate for SSL connections."""
