# coding=utf-8
from __future__ import absolute_import, division, print_function, unicode_literals

import logging
from logging.config import dictConfig
import os

from sopel import tools


class IrcLoggingHandler(logging.Handler):
    """Logging handler for output to an IRC channel.

    :param bot: a Sopel instance
    :type bot: :class:`sopel.bot.Sopel`
    :param level: minimum level of log messages to report through this handler
    :type level: :ref:`logging level <levels>`

    Implementation of a :class:`logging.Handler`.
    """
    def __init__(self, bot, level):
        super(IrcLoggingHandler, self).__init__(level)
        self._bot = bot
        self._channel = bot.settings.core.logging_channel

    def emit(self, record):
        """Emit a log ``record`` to the IRC channel.

        :param record: the log record to output
        :type record: :class:`logging.LogRecord`
        """
        if self._bot.backend is None or not self._bot.backend.is_connected():
            # Don't emit logs when the bot is not connected.
            return

        try:
            msg = self.format(record)
            self._bot.say(msg, self._channel)
        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception:  # TODO: Be specific
            self.handleError(record)


class ChannelOutputFormatter(logging.Formatter):
    """Output formatter for log messages destined for an IRC channel.

    :param fmt: log line format
    :type fmt: :ref:`format string <formatstrings>`
    :param datefmt: date format
    :type datefmt: :ref:`format string <formatstrings>`

    Implementation of a :class:`logging.Formatter`.
    """
    def __init__(self, fmt='[%(filename)s] %(message)s', datefmt=None):
        super(ChannelOutputFormatter, self).__init__(fmt=fmt, datefmt=datefmt)

    def formatException(self, exc_info):
        """Format the exception info as a string for output.

        :param tuple exc_info: standard exception information returned by
                               :func:`~sys.exc_info`
        """
        # logging will throw a newline between the message and this, but
        # that's fine because Sopel will strip it back out anyway
        return ' - ' + repr(exc_info[1])


def setup_logging(settings):
    """Set up logging based on the bot's configuration ``settings``.

    :param settings: configuration settings object
    :type settings: :class:`sopel.config.Config`
    """
    log_directory = settings.core.logdir
    base_level = settings.core.logging_level or 'WARNING'
    base_format = settings.core.logging_format
    base_datefmt = settings.core.logging_datefmt

    logging_config = {
        'version': 1,
        'formatters': {
            'sopel': {
                'format': base_format,
                'datefmt': base_datefmt,
            },
            'raw': {
                'format': '%(asctime)s %(message)s',
                'datefmt': base_datefmt,
            },
        },
        'loggers': {
            # all purpose, sopel root logger
            'sopel': {
                'level': base_level,
                'handlers': ['console', 'logfile', 'errorfile'],
            },
            # raw IRC log
            'sopel.raw': {
                'level': 'DEBUG',
                'propagate': False,
                'handlers': ['raw'],
            },
            # asynchat exception logger
            'sopel.exceptions': {
                'level': 'INFO',
                'propagate': False,
                'handlers': ['exceptionfile'],
            },
        },
        'handlers': {
            # output on stderr
            'console': {
                'level': 'DEBUG',
                'class': 'logging.StreamHandler',
                'formatter': 'sopel',
            },
            # generic purpose log file
            'logfile': {
                'level': 'DEBUG',
                'class': 'logging.handlers.TimedRotatingFileHandler',
                'filename': os.path.join(
                    log_directory, settings.basename + '.sopel.log'),
                'when': 'midnight',
                'formatter': 'sopel',
            },
            # caught error log file
            'errorfile': {
                'level': 'ERROR',
                'class': 'logging.handlers.TimedRotatingFileHandler',
                'filename': os.path.join(
                    log_directory, settings.basename + '.error.log'),
                'when': 'midnight',
                'formatter': 'sopel',
            },
            # uncaught error file
            'exceptionfile': {
                'level': 'ERROR',
                'class': 'logging.handlers.TimedRotatingFileHandler',
                'filename': os.path.join(
                    log_directory, settings.basename + '.exceptions.log'),
                'when': 'midnight',
                'formatter': 'sopel',
            },
            # raw IRC log file
            'raw': {
                'level': 'DEBUG',
                'class': 'logging.handlers.TimedRotatingFileHandler',
                'filename': os.path.join(
                    log_directory, settings.basename + '.raw.log'),
                'when': 'midnight',
                'formatter': 'raw',
            },
        },
    }
    dictConfig(logging_config)


@tools.deprecated(
    reason='use sopel.tools.get_logger instead',
    version='7.0',
    warning_in='8.0',
    removed_in='9.0',
)
def get_logger(name=None):
    """Return a logger for a module, if the name is given.

    .. deprecated:: 7.0

        Sopel's own code should use :func:`logging.getLogger(__name__)
        <logging.getLogger>` instead, and external plugins should use
        :func:`sopel.tools.get_logger`.

        This will emit a deprecation warning in Sopel 8.0, and it will be
        removed in Sopel 9.0.

    """
    if not name:
        return logging.getLogger('sopel')

    parts = name.strip().split('.')
    if len(parts) > 1 or parts[0] in ['sopel', 'sopel_modules']:
        return logging.getLogger(name)

    # assume it's a plugin name, as intended by the original get_logger
    return tools.get_logger(name)
