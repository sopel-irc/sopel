# coding=utf-8
from __future__ import unicode_literals, absolute_import, print_function, division

import logging
import os
from logging.config import dictConfig

from .tools import deprecated


class IrcLoggingHandler(logging.Handler):
    def __init__(self, bot, level):
        super(IrcLoggingHandler, self).__init__(level)
        self._bot = bot
        self._channel = bot.config.core.logging_channel

    def emit(self, record):
        try:
            msg = self.format(record)
            self._bot.say(msg, self._channel)
        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception:  # TODO: Be specific
            self.handleError(record)


class ChannelOutputFormatter(logging.Formatter):
    def __init__(self, fmt='[%(filename)s] %(message)s', datefmt=None):
        super(ChannelOutputFormatter, self).__init__(fmt=fmt, datefmt=datefmt)

    def formatException(self, exc_info):
        # logging will through a newline between the message and this, but
        # that's fine because Sopel will strip it back out anyway
        return ' - ' + repr(exc_info[1])


def setup_logging(settings):
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
            # catched error log file
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


@deprecated(
    'Use `sopel.logger.get_plugin_logger` instead',
    version='7.0',
    removed_in='8.0')
def get_logger(name=None):
    """Return a logger for a module, if the name is given.

    This is equivalent to ``logging.getLogger('sopel.modules.' + name)`` when
    name is given, and ``logging.getLogger('sopel')`` when it is not.
    The latter case is intended for use in Sopel's core; modules should call
    ``get_logger(__name__)`` to get a logger.

    .. deprecated:: 7.0

        Use ``logging.getLogger(__name__)`` in Sopel's code instead, and
        :func:`get_plugin_logger` for external plugins.

    """
    if name:
        return logging.getLogger('sopel.modules.' + name)
    else:
        return logging.getLogger('sopel')


def get_plugin_logger(plugin_name):
    """Return a logger for a plugin.

    :param str plugin_name: name of the plugin
    :return: the logger for the given plugin

    This::

        from sopel import logger
        LOGGER = logger.get_plugin_logger('my_custom_plugin')

    is equivalent to this::

        import logging
        LOGGER = logging.getLogger('sopel.externals.my_custom_plugin')

    Internally, Sopel configures logging for the ``sopel`` namespace, so
    external plugins can't benefit from it with ``logging.getLogger(__name__)``
    as they won't be in the same namespace. This function uses the
    ``plugin_name`` with a prefix inside this namespace.
    """
    return logging.getLogger('sopel.externals.%s' % plugin_name)
