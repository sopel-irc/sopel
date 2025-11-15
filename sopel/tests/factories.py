"""Test factories: they create objects for testing purposes.

.. versionadded:: 7.0

.. important::

    These factories are documented to help plugin authors to use them. However
    Sopel recommends the usage of `pytest`__ and provides a set of fixtures
    to get properly configurated factories in :mod:`sopel.tests.pytest_plugin`,
    instead of trying to instanciate the factories manually.

    .. __: https://docs.pytest.org/en/stable/

"""
from __future__ import annotations

import re
from typing import TYPE_CHECKING

from sopel import bot, config, plugins, trigger

from .mocks import MockIRCBackend, MockIRCServer, MockUser


if TYPE_CHECKING:
    from collections.abc import Iterable
    import pathlib


class BotFactory:
    """Factory to create bots.

    An instance of this factory can be used as a callable to create an instance
    of :class:`~sopel.bot.Sopel` with a fake connection backend. It requires an
    instance of :class:`~sopel.config.Config`, which can be obtained through
    the :class:`ConfigFactory`.

    .. seealso::

        The :func:`~sopel.tests.pytest_plugin.botfactory` fixture can be used
        to instantiate this factory.
    """
    def preloaded(
        self,
        settings: config.Config,
        preloads: Iterable[str] | None = None,
    ) -> bot.Sopel:
        """Create a bot and preload its plugins.

        :param settings: Sopel's configuration for testing purposes
        :param preloads: list of plugins to preload, setup, and register
        :return: a test instance of the bot

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
        """Create a test Sopel instance.

        :param settings: test settings used by the test bot
        :return: an instance of Sopel ready for testing purpose

        This method will create an instance of :class:`~sopel.bot.Sopel` using
        the ``settings`` provided and a
        :class:`~sopel.tests.mocks.MockIRCBackend` that can be used to fake
        messages received from an IRC server.
        """
        obj = bot.Sopel(settings, daemon=False)
        obj.backend = MockIRCBackend(obj)
        return obj


class ConfigFactory:
    """Factory to create settings.

    :param tmpdir: a test folder to store documentation files

    An instance of this factory can be used as a callable to create an instance
    of :class:`~sopel.config.Config`.

    .. versionchanged:: 8.1

        This factory used to depend on pytest's fixture ``tmpdir``, but is now
        using Python's standard :class:`pathlib.Path` instead.

    .. seealso::

        The :func:`~sopel.tests.pytest_plugin.configfactory` fixture can be
        used to instantiate this factory.
    """
    def __init__(self, tmpdir: pathlib.Path) -> None:
        self.tmpdir: pathlib.Path = tmpdir

    def __call__(self, name: str, data: str) -> config.Config:
        """Call the factory with the settings to create.

        :param name: filename of the configuration file; should ends with the
                     ``.cfg`` file extension
        :param data: settings content as per Sopel's configuration file format
        :return: an instance of test configuration
        """
        tmpfile = self.tmpdir / name
        tmpfile.write_text(data, encoding='utf-8')
        return config.Config(str(tmpfile))


class TriggerFactory:
    """Factory to create triggers.

    An instance of this factory can be used as a callable to create an instance
    of :class:`sopel.trigger.Trigger`. It requires an instance of
    Sopel, which can be obtained through the :class:`BotFactory`, as well as
    the trigger's content.

    .. seealso::

        The :func:`~sopel.tests.pytest_plugin.triggerfactory` fixture can be
        used to instantiate this factory.
    """
    def wrapper(
        self,
        mockbot: bot.Sopel,
        raw: str,
        pattern: str | None = None,
    ) -> bot.SopelWrapper:
        """Create a trigger and return a wrapped instance of Sopel.

        :param mockbot: a test instance of Sopel
        :param raw: the raw trigger's content
        :param pattern: an optional regex pattern (default to ``.*``)
        :return: a wrapped instance of Sopel with the created trigger

        This method is a shortcut over calling the factory to create a trigger
        and get an instance of :class:`~sopel.bot.SopelWrapper` with it.
        """
        trigger = self(mockbot, raw, pattern=pattern)
        return bot.SopelWrapper(mockbot, trigger)

    def __call__(
        self,
        mockbot: bot.Sopel,
        raw: str,
        pattern: str | None = None,
    ) -> trigger.Trigger:
        """Call the factory with a test bot to return a test trigger message.

        :param mockbot: a test instance of Sopel
        :param raw: the raw trigger's content
        :param pattern: an optional regex pattern (default to ``.*``)
        :return: an instance of a test server
        """
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
            statusmsg_prefixes=mockbot.isupport.get('STATUSMSG'),
        )
        return trigger.Trigger(mockbot.settings, pretrigger, match)


class IRCFactory:
    """Factory to create mock IRC servers.

    An instance of this factory can be used as a callable to create an instance
    of :class:`sopel.tests.mocks.MockIRCServer`. It requires an instance of
    Sopel, which can be obtained through the :class:`BotFactory`.

    .. seealso::

        The :func:`~sopel.tests.pytest_plugin.ircfactory` fixture can be used
        to create this factory.
    """
    def __call__(
        self,
        mockbot: bot.Sopel,
        join_threads: bool = True,
    ) -> MockIRCServer:
        """Call the factory with a test bot to return a test server.

        :param mockbot: a test instance of Sopel
        :param join_threads: an optional flag to wait on running triggers
                             (default to true)
        :return: an instance of a test server
        """
        return MockIRCServer(mockbot, join_threads)


class UserFactory:
    """Factory to create mock users.

    An instance of this factory can be used as a callable to create an instance
    of :class:`sopel.tests.mocks.MockUser`. It requires the information of the
    test user such as its nick, account, and hostname.

    .. seealso::

        The :func:`~sopel.tests.pytest_plugin.userfactory` fixture can be used
        to create this factory.
    """
    def __call__(
        self,
        nick: str | None = None,
        user: str | None = None,
        host: str | None = None,
    ) -> MockUser:
        """Call the factory with a nick to create a test user.

        :param nick: a user's nick
        :param user: a user's account
        :param host: a user's hostname
        :return: an instance of a test user
        """
        return MockUser(nick, user, host)
