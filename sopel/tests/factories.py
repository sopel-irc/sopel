"""Test factories: they create objects for testing purposes.

.. versionadded:: 7.0
"""
from __future__ import annotations

import re
from typing import Iterable, Optional

from sopel import bot, config, plugins, trigger
from .mocks import MockIRCBackend, MockIRCServer, MockUser


class BotFactory:
    """Factory to create bot.

    .. seealso::

        The :func:`~sopel.tests.pytest_plugin.botfactory` fixture can be used
        to instantiate this factory.
    """
    def preloaded(
        self,
        settings: config.Config,
        preloads: Optional[Iterable[str]] = None,
    ) -> bot.Sopel:
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
            bot = factory.preloaded(settings, ['emoticons', 'remind'])

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

    def __call__(self, settings: config.Config) -> bot.Sopel:
        obj = bot.Sopel(settings, daemon=False)
        obj.backend = MockIRCBackend(obj)
        return obj


class ConfigFactory:
    """Factory to create settings.

    .. seealso::

        The :func:`~sopel.tests.pytest_plugin.configfactory` fixture can be
        used to instantiate this factory.
    """
    def __init__(self, tmpdir):
        self.tmpdir = tmpdir

    def __call__(self, name: str, data: str) -> config.Config:
        tmpfile = self.tmpdir.join(name)
        tmpfile.write(data)
        return config.Config(tmpfile.strpath)


class TriggerFactory:
    """Factory to create trigger.

    .. seealso::

        The :func:`~sopel.tests.pytest_plugin.triggerfactory` fixture can be
        used to instantiate this factory.
    """
    def wrapper(
        self,
        mockbot: bot.Sopel,
        raw: str,
        pattern: Optional[str] = None,
    ) -> bot.SopelWrapper:
        trigger = self(mockbot, raw, pattern=pattern)
        return bot.SopelWrapper(mockbot, trigger)

    def __call__(
        self,
        mockbot: bot.Sopel,
        raw: str,
        pattern: Optional[str] = None,
    ) -> trigger.Trigger:
        match = re.match(pattern or r'.*', raw)
        if match is None:
            raise ValueError(
                'Cannot create a Trigger without a matching pattern')

        url_schemes = mockbot.settings.core.auto_url_schemes
        pretrigger = trigger.PreTrigger(
            mockbot.nick,
            raw,
            url_schemes=url_schemes,
            identifier_factory=mockbot.make_identifier,
        )
        return trigger.Trigger(mockbot.settings, pretrigger, match)


class IRCFactory:
    """Factory to create mock IRC server.

    .. seealso::

        The :func:`~sopel.tests.pytest_plugin.ircfactory` fixture can be used
        to create this factory.
    """
    def __call__(
        self,
        mockbot: bot.Sopel,
        join_threads: bool = True,
    ) -> MockIRCServer:
        return MockIRCServer(mockbot, join_threads)


class UserFactory:
    """Factory to create mock user.

    .. seealso::

        The :func:`~sopel.tests.pytest_plugin.userfactory` fixture can be used
        to create this factory.
    """
    def __call__(
        self,
        nick: Optional[str] = None,
        user: Optional[str] = None,
        host: Optional[str] = None,
    ) -> MockUser:
        return MockUser(nick, user, host)
