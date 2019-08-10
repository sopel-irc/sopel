# coding=utf-8
from __future__ import unicode_literals, absolute_import, print_function, division

import logging
import os
from logging.config import dictConfig


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


def setup_logging(bot):
    log_directory = bot.config.core.logdir
    base_level = bot.config.core.logging_level or 'INFO'
    base_format = bot.config.core.logging_format
    base_datefmt = bot.config.core.logging_datefmt

    logging_config = {
        'version': 1,
        'formatters': {
            'sopel': {
                'format': base_format,
                'datefmt': base_datefmt,
            },
        },
        'loggers': {
            'sopel': {
                'level': base_level,
                'handlers': ['console', 'logfile', 'errorfile'],
            },
            'sopel.raw': {
                'level': 'DEBUG',
                'propagate': False,
                'handlers': ['raw'],
            },
        },
        'handlers': {
            'console': {
                'level': 'DEBUG',
                'class': 'logging.StreamHandler',
            },
            'logfile': {
                'level': 'DEBUG',
                'class': 'logging.handlers.TimedRotatingFileHandler',
                'filename': os.path.join(
                    log_directory, bot.config.basename + '.sopel.log'),
                'when': 'midnight',
            },
            'errorfile': {
                'level': 'ERROR',
                'class': 'logging.handlers.TimedRotatingFileHandler',
                'filename': os.path.join(
                    log_directory, bot.config.basename + '.error.log'),
                'when': 'midnight',
            },
            'raw': {
                'level': 'DEBUG',
                'class': 'logging.handlers.TimedRotatingFileHandler',
                'filename': os.path.join(
                    log_directory, bot.config.basename + '.raw.log'),
                'when': 'midnight',
            },
        },
    }
    dictConfig(logging_config)

    # configure channel logging if required by configuration
    if bot.config.core.logging_channel:
        channel_level = bot.config.core.logging_channel_level or base_level
        channel_format = bot.config.core.logging_channel_format or base_format
        channel_datefmt = bot.config.core.logging_channel_datefmt or base_datefmt
        channel_params = {}
        if channel_format:
            channel_params['fmt'] = channel_format
        if channel_datefmt:
            channel_params['datefmt'] = channel_datefmt
        formatter = ChannelOutputFormatter(**channel_params)
        handler = IrcLoggingHandler(bot, channel_level)
        handler.setFormatter(formatter)

        # set channel handler to `sopel` logger
        logger = logging.getLogger('sopel')
        logger.addHandler(handler)


def get_logger(name=None):
    """Return a logger for a module, if the name is given.

    This is equivalent to `logging.getLogger('sopel.modules.' + name)` when
    name is given, and `logging.getLogger('sopel')` when it is not. The latter
    case is intended for use in Sopel's core; modules should call
    `get_logger(__name__)` to get a logger."""
    if name:
        return logging.getLogger('sopel.modules.' + name)
    else:
        return logging.getLogger('sopel')
