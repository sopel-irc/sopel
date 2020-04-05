# coding=utf-8
"""Test factories: they create objects for testing purposes.

.. versionadded:: 7.0
"""
from __future__ import unicode_literals, absolute_import, print_function, division

import re

from sopel import bot, config, plugins, trigger
from .mocks import MockIRCServer, MockUser, MockIRCBackend


class BotFactory(object):
    """Factory to create bot.

    .. seealso::

        The :func:`~sopel.tests.pytest_plugin.botfactory` fixture can be used
        to instantiate this factory.
    """
    def preloaded(self, settings, preloads=None):
        """Create a bot and preload its plugins.

        :param settings: Sopel's configuration for testing purposes
        :type settings: :class:`sopel.config.Config`
        :param list preloads: list of plugins to preload, setup, and register
        :return: a test instance of the bot
        :rtype: :class:`sopel.bot.Sopel`

        This will instantiate a :class:`~sopel.bot.Sopel` object, replace its
        backend with a :class:`~.mocks.MockIRCBackend`, and then preload
        plugins. This will automatically load the ``coretasks`` plugin, and
        every other plugin from ``preloads``::

            factory = BotFactory()
            bot = factory.with_autoloads(settings, ['emoticons', 'remind'])

        .. note::

            This will automatically setup plugins: be careful with plugins that
            require access to external services on setup.

            You may also need to manually call shutdown routines for the
            loaded plugins.

        """
        preloads = set(preloads or []) | {'coretasks'}
        mockbot = self(settings)

        usable_plugins = plugins.get_usable_plugins(settings)
        for name in preloads:
            plugin = usable_plugins[name][0]
            plugin.load()
            plugin.setup(mockbot)
            plugin.register(mockbot)

        return mockbot

    def __call__(self, settings):
        obj = bot.Sopel(settings, daemon=False)
        obj.backend = MockIRCBackend(obj)
        return obj


class ConfigFactory(object):
    """Factory to create settings.

    .. seealso::

        The :func:`~sopel.tests.pytest_plugin.configfactory` fixture can be
        used to instantiate this factory.
    """
    def __init__(self, tmpdir):
        self.tmpdir = tmpdir

    def __call__(self, name, data):
        tmpfile = self.tmpdir.join(name)
        tmpfile.write(data)
        return config.Config(tmpfile.strpath)


class TriggerFactory(object):
    """Factory to create trigger.

    .. seealso::

        The :func:`~sopel.tests.pytest_plugin.triggerfactory` fixture can be
        used to instantiate this factory.
    """
    def wrapper(self, mockbot, raw, pattern=None):
        trigger = self(mockbot, raw, pattern=pattern)
        return bot.SopelWrapper(mockbot, trigger)

    def __call__(self, mockbot, raw, pattern=None):
        return trigger.Trigger(
            mockbot.settings,
            trigger.PreTrigger(mockbot.nick, raw),
            re.match(pattern or r'.*', raw))


class IRCFactory(object):
    """Factory to create mock IRC server.

    .. seealso::

        The :func:`~sopel.tests.pytest_plugin.ircfactory` fixture can be used
        to create this factory.
    """
    def __call__(self, mockbot):
        return MockIRCServer(mockbot)


class UserFactory(object):
    """Factory to create mock user.

    .. seealso::

        The :func:`~sopel.tests.pytest_plugin.userfactory` fixture can be used
        to create this factory.
    """
    def __call__(self, nick=None, user=None, host=None):
        return MockUser(nick, user, host)
