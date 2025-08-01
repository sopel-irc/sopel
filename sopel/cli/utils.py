from __future__ import annotations

import inspect
import logging
import os
import sys

from sopel import config, plugins


# Allow clean import *
__all__ = [
    'enumerate_configs',
    'find_config',
    'add_common_arguments',
    'load_settings',
    'wizard',
    'plugins_wizard',
    # colors
    'green',
    'yellow',
    'red',
]

LOGGER = logging.getLogger(__name__)

RESET = '\033[0m'
RED = '\033[31m'
GREEN = '\033[32m'
YELLOW = '\033[33m'


def _colored(text, color, reset=True):
    text = color + text
    if reset:
        return text + RESET
    return text


def green(text, reset=True):
    """Add ANSI escape sequences to make the text green in terminal.

    :param str text: text to colorized in green
    :param bool reset: if the text color must be reset after (default ``True``)
    :return: text with ANSI escape sequences for green color
    :rtype: str
    """
    return _colored(text, GREEN, reset)


def yellow(text, reset=True):
    """Add ANSI escape sequences to make the text yellow in terminal.

    :param str text: text to colorized in yellow
    :param bool reset: if the text color must be reset after (default ``True``)
    :return: text with ANSI escape sequences for yellow color
    :rtype: str
    """
    return _colored(text, YELLOW, reset)


def red(text, reset=True):
    """Add ANSI escape sequences to make the text red in terminal.

    :param str text: text to colorized in red
    :param bool reset: if the text color must be reset after (default ``True``)
    :return: text with ANSI escape sequences for red color
    :rtype: str
    """
    return _colored(text, RED, reset)


def wizard(filename):
    """Global Configuration Wizard.

    :param str filename: name of the new file to be created
    :return: the created configuration object

    This wizard function helps the creation of a Sopel configuration file,
    with its core section and its plugins' sections.
    """
    configdir, basename = os.path.split(filename)
    if not basename:
        raise config.ConfigurationError(
            'Sopel requires a filename for its configuration, not a directory')

    try:
        if not os.path.isdir(configdir):
            print('Creating config directory at {}'.format(configdir))
            os.makedirs(configdir)
            print('Config directory created')
    except Exception:
        stderr('There was a problem creating {}'.format(configdir))
        raise

    name, ext = os.path.splitext(basename)
    if not ext:
        # Always add .cfg if filename does not have an extension
        filename = os.path.join(configdir, name + '.cfg')
    elif ext != '.cfg':
        # It is possible to use a non-cfg file for Sopel
        # but the wizard does not allow it at the moment
        raise config.ConfigurationError(
            'Sopel uses ".cfg" as configuration file extension, not "%s".' % ext)

    settings = config.Config(filename, validate=False)

    print("Please answer the following questions "
          "to create your configuration file (%s):\n" % filename)
    config.core_section.configure(settings)
    if settings.option(
        'Would you like to see if there are any plugins '
        'that need configuring'
    ):
        _plugins_wizard(settings)

    try:
        settings.save()
    except Exception:  # TODO: Be specific
        stderr("Encountered an error while writing the config file. "
               "This shouldn't happen. Check permissions.")
        raise

    print("Config file written successfully!")
    return settings


def plugins_wizard(filename):
    """Plugins Configuration Wizard.

    :param str filename: path to an existing Sopel configuration
    :return: the configuration object

    This wizard function helps to configure plugins for an existing Sopel
    config file.
    """
    if not os.path.isfile(filename):
        raise config.ConfigurationNotFound(filename)

    settings = config.Config(filename, validate=False)
    _plugins_wizard(settings)

    try:
        settings.save()
    except Exception:  # TODO: Be specific
        stderr("Encountered an error while writing the config file. "
               "This shouldn't happen. Check permissions.")
        raise

    return settings


def _plugins_wizard(settings):
    usable_plugins = plugins.get_usable_plugins(settings)
    for plugin, is_enabled in usable_plugins.values():
        if not is_enabled:
            # Do not configure non-enabled plugins
            continue

        name = plugin.name
        try:
            _plugin_wizard(settings, plugin)
        except Exception as e:
            LOGGER.exception('Error loading %s: %s', name, e)


def _plugin_wizard(settings, plugin):
    plugin.load()
    prompt = "Configure {}".format(plugin.get_label())
    if plugin.has_configure() and settings.option(prompt):
        plugin.configure(settings)


def enumerate_configs(config_dir, extension='.cfg'):
    """List configuration files from ``config_dir`` with ``extension``.

    :param str config_dir: path to the configuration directory
    :param str extension: configuration file's extension (default to ``.cfg``)
    :return: a list of configuration filenames found in ``config_dir`` with
             the correct ``extension``
    :rtype: list

    Example::

        >>> from sopel import cli, config
        >>> os.listdir(config.DEFAULT_HOMEDIR)
        ['config.cfg', 'extra.ini', 'plugin.cfg', 'README']
        >>> cli.enumerate_configs(config.DEFAULT_HOMEDIR)
        ['config.cfg', 'plugin.cfg']
        >>> cli.enumerate_configs(config.DEFAULT_HOMEDIR, '.ini')
        ['extra.ini']

    """
    if not os.path.isdir(config_dir):
        return

    for item in os.listdir(config_dir):
        if item.endswith(extension):
            yield item


def find_config(config_dir: str, name: str, extension: str = '.cfg') -> str:
    """Build the absolute path for the given configuration file ``name``.

    :param config_dir: path to the configuration directory
    :param name: configuration file ``name``
    :param extension: configuration file's extension (defaults to ``.cfg``)
    :return: the absolute path to the configuration file, either in the current
             directory or in the ``config_dir`` directory

    This function appends the extension if absent before checking the following:

    * If ``name`` is an absolute path, it is returned whether it exists or not
    * If ``name`` exists in the ``config_dir``, the absolute path is returned
    * If ``name`` exists in the current directory, its absolute path is returned
    * Otherwise, the path to the nonexistent file within ``config_dir`` is returned

    Example::

        >>> from sopel.cli import utils
        >>> from sopel import config
        >>> os.getcwd()
        '/sopel'
        >>> os.listdir()
        ['local.cfg', 'extra.ini']
        >>> os.listdir(config.DEFAULT_HOMEDIR)
        ['config.cfg', 'extra.ini', 'logs', 'plugins']
        >>> utils.find_config(config.DEFAULT_HOMEDIR, 'local.cfg')
        '/sopel/local.cfg'
        >>> utils.find_config(config.DEFAULT_HOMEDIR, 'config')
        '/home/username/.sopel/config.cfg'
        >>> utils.find_config(config.DEFAULT_HOMEDIR, 'extra', '.ini')
        '/home/username/.sopel/extra.ini'

    .. versionchanged:: 8.0

        Files in the ``config_dir`` are now preferred, and files without the
        requested extension are no longer returned.

    """
    if not name.endswith(extension):
        name = name + extension

    if os.path.isabs(name):
        return name
    conf_dir_name = os.path.join(config_dir, name)
    if os.path.isfile(conf_dir_name):
        return conf_dir_name
    elif os.path.isfile(name):
        return os.path.abspath(name)
    return conf_dir_name


def add_common_arguments(parser):
    """Add common and configuration-related arguments to a ``parser``.

    :param parser: Argument parser (or subparser)
    :type parser: argparse.ArgumentParser

    This function adds the common arguments for Sopel's command line tools.
    It adds the following arguments:

    * ``-c``/``--config``: the name of the Sopel config, or its absolute path
    * ``--config-dir``: the directory to scan for config files

    This can be used on an argument parser, or an argument subparser, to handle
    these cases::

        [sopel-command] -c [filename]
        [sopel-command] [action] -c [filename]
        [sopel-command] --config-dir [directory] -c [name]

    Then, when the parser parses the command line arguments, it will expose
    ``config`` and ``configdir`` options that can be used to find and load
    Sopel's settings.

    The default value for ``config`` is either the value of the environment
    variable ``SOPEL_CONFIG``, or the string ``default``.

    .. seealso::

        The :func:`sopel.cli.utils.load_settings` function uses an ``options``
        object from a parser configured with such arguments.

    """
    parser.add_argument(
        '-c', '--config',
        default=os.environ.get('SOPEL_CONFIG') or 'default',
        metavar='filename',
        dest='config',
        help=inspect.cleandoc("""
            Use a specific configuration file.
            A config name can be given and the configuration file will be
            found in Sopel's homedir (defaults to ``~/.sopel/default.cfg``).
            An absolute pathname can be provided instead to use an
            arbitrary location.
            When the ``SOPEL_CONFIG`` environment variable is set and not
            empty, it is used as the default value.
        """))
    parser.add_argument(
        '--config-dir',
        default=os.environ.get('SOPEL_CONFIG_DIR') or config.DEFAULT_HOMEDIR,
        dest='configdir',
        help=inspect.cleandoc("""
            Look for configuration files in this directory.
            By default, Sopel will search in ``~/.sopel``.
            When the ``SOPEL_CONFIG_DIR`` environment variable is set and not
            empty, it is used as the default value.
        """))


def load_settings(options):
    """Load Sopel's settings using the command line's ``options``.

    :param options: parsed arguments
    :return: sopel configuration
    :rtype: :class:`sopel.config.Config`
    :raise sopel.config.ConfigurationNotFound: raised when configuration file
                                               is not found
    :raise sopel.config.ConfigurationError: raised when configuration is
                                            invalid

    This function loads Sopel's settings from ``options.config``. This option's
    value should be from one of these sources:

    * given by the command line argument,
    * ``SOPEL_CONFIG`` environment variable, if the argument is not used,
    * otherwise it should default to ``default``,

    then it returns it as a :class:`~sopel.config.Config` object.

    If the configuration file can not be found, a
    :exc:`sopel.config.ConfigurationNotFound` error will be raised.

    .. note::

        This function expects that ``options`` exposes two attributes:
        ``config`` and ``configdir``.

        The :func:`sopel.cli.utils.add_common_arguments` function should be
        used to add these options to the argument parser. This function is also
        responsible for using the environment variable or the default value.

    """
    filename = find_config(options.configdir, options.config)

    if not os.path.isfile(filename):
        raise config.ConfigurationNotFound(filename=filename)

    return config.Config(filename)


def get_many_text(items, one, two, many):
    """Get the right text based on the number of ``items``."""
    message = ''
    if not items:
        return message

    items_count = len(items)

    if items_count == 1:
        message = one.format(item=items[0])
    elif items_count == 2:
        message = two.format(first=items[0], second=items[1])
    else:
        left = ', '.join(items[:-1])
        last = items[-1]
        message = many.format(left=left, last=last)

    return message


def check_pid(pid):
    """Check if a process is running with the given ``PID``.

    :param int pid: PID to check
    :return bool: ``True`` if the given PID is running, ``False`` otherwise

    *Availability: POSIX systems only.*

    .. versionchanged:: 8.0

        Moved from :mod:`sopel.tools` to :mod:`sopel.cli.utils`.

    .. note::

        Matching the :py:func:`os.kill` behavior this function needs on Windows
        was rejected in
        `Python issue #14480 <https://bugs.python.org/issue14480>`_, so
        :func:`check_pid` cannot be used on Windows systems.

    """
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    else:
        return True


def stderr(string):
    """Print the given ``string`` to stderr.

    :param str string: the string to output

    Just a convenience function.

    .. versionchanged:: 8.0

        Moved from :mod:`sopel.tools` to :mod:`sopel.cli.utils`.

    """
    print(string, file=sys.stderr)
