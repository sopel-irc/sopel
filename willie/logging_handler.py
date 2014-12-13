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
        except:
            self.handleError(record)

class ChannelOutputFormatter(logging.Formatter):
    def __init__(self):
        super(ChannelOutputFormatter, self).__init__(
            fmt='[%(filename)s] %(msg)s'
        )
    def formatException(self, exc_info):
        # logging will through a newline between the message and this, but
        # that's fine because Willie will strip it back out anyway
        return ' - ' + repr(exc_info[1])

def setup_logging(bot):
    level = bot.config.core.logging_level or 'WARNING'
    logging.basicConfig(level=level)
    logger = logging.getLogger('willie')
    if bot.config.core.logging_channel:
        handler = IrcLoggingHandler(bot, level)
        handler.setFormatter(ChannelOutputFormatter())
        logger.addHandler(handler)
