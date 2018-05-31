# coding=utf-8
from __future__ import unicode_literals, absolute_import, print_function, division

import logging


class IrcLoggingHandler(logging.Handler):
    def __init__(self, bot, level):
        super(IrcLoggingHandler, self).__init__(level)
        self._bot = bot
        self._channel = bot.config.core.logging_channel

    def emit(self, record):
        try:
            msg = self.format(record)
            self._bot.msg(self._channel, msg)
        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception:  # TODO: Be specific
            self.handleError(record)


class ChannelOutputFormatter(logging.Formatter):
    def __init__(self):
        super(ChannelOutputFormatter, self).__init__(
            fmt='[%(filename)s] %(message)s'
        )

    def formatException(self, exc_info):
        # logging will through a newline between the message and this, but
        # that's fine because Sopel will strip it back out anyway
        return ' - ' + repr(exc_info[1])


def setup_logging(bot):
    level = bot.config.core.logging_level or 'WARNING'
    logging.basicConfig(level=level)
    logger = logging.getLogger('sopel')
    if bot.config.core.logging_channel:
        handler = IrcLoggingHandler(bot, level)
        handler.setFormatter(ChannelOutputFormatter())
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
