"""Plugin objects' definition.

.. versionadded:: 8.1

The core of a plugin consists of several objects, either plugin callables or
plugin jobs. These objects are represented by instances of
:class:`PluginCallable` and :class:`PluginJob` respectively.

.. seealso::

    The decorators in :mod:`sopel.plugin` create these objects directly.

.. important::

    This is all relatively new. Its usage and documentation is for Sopel core
    development. It is subject to rapid changes between versions without much
    (or any) warning.

    Do **not** build your plugin based on what is here, you do **not** need to.

"""
# Copyright 2025, Florian Strzelecki <florian.strzelecki@gmail.com>
#
# Licensed under the Eiffel Forum License 2.
from __future__ import annotations

import abc
import enum
import inspect
import logging
import re
from typing import (
    Any,
    Callable,
    Literal,
    Protocol,
    Type,
    TYPE_CHECKING,
    TypeVar,
)

from typing_extensions import override

from sopel.config.core_section import COMMAND_DEFAULT_HELP_PREFIX
from sopel.lifecycle import deprecated


if TYPE_CHECKING:
    from types import ModuleType

    from sopel.bot import Sopel, SopelWrapper
    from sopel.config import Config
    from sopel.trigger import Trigger


LOGGER = logging.getLogger(__name__)


TypedPluginObject = TypeVar('TypedPluginObject', bound='AbstractPluginObject')
"""A :class:`~typing.TypeVar` bound to :class:`AbstractPluginObject`.

When used in the :meth:`AbstractPluginObject.from_plugin_object` class method,
it means the return value must be an instance of the class used to call that
method and not a different subclass of ``AbstractPluginObject``.

.. versionadded:: 8.1
"""


class TypedPluginCallableHandler(Protocol):
    """Protocol definition of a plugin callable handler function.

    A callable handler function must accept two positional arguments:

    * an instance of :class:`~sopel.bot.SopelWrapper`
    * an instance of :class:`~sopel.trigger.Trigger`

    .. versionadded:: 8.1
    """
    __name__: str

    def __call__(
        self,
        bot: SopelWrapper,
        trigger: Trigger,
        *arg: Any,
        **kwargs: Any,
    ) -> Any:
        ...


class TypedPluginJobHandler(Protocol):
    """Protocol definition of a plugin job handler function.

    A job handler function must accept one positional argument:

    * an instance of :class:`~sopel.bot.Sopel`

    .. versionadded:: 8.1
    """
    __name__: str

    def __call__(self, bot: Sopel, *arg: Any, **kwargs: Any) -> Any:
        ...


class TypedCallablePredicate(Protocol):
    """Protocol definition of a plugin callable predicate function.

    A predicate function must accept two positional arguments:

    * an instance of :class:`~sopel.bot.SopelWrapper`
    * an instance of :class:`~sopel.trigger.Trigger`

    And it must return a boolean:

    * if True, the plugin callable can execute
    * otherwise, the predicate prevents the execution of the plugin callable

    .. versionadded:: 8.1
    """
    def __call__(self, bot: SopelWrapper, trigger: Trigger) -> bool:
        ...


class AbstractPluginObject(abc.ABC):
    """Abstract definition of a plugin object.

    A plugin object encapsulates the logic and attributes required for a plugin
    to register and execute this object.

    .. versionadded:: 8.1
    """
    _sopel_callable = True

    plugin_name: str | None
    label: str | None
    threaded: bool
    doc: str | None

    @property
    @deprecated(
        reason='`rule_label` is replaced by the `label` attribute.',
        version='8.1',
        removed_in='9.0',
    )
    def rule_label(self):
        return self.label

    @property
    @deprecated(
        reason='`thread` is replaced by the `threaded` attribute.',
        version='8.1',
        removed_in='9.0',
    )
    def thread(self):
        return self.threaded

    @classmethod
    def from_plugin_object(
        cls: Type[TypedPluginObject],
        obj: AbstractPluginObject,
    ) -> TypedPluginObject:
        """Convert a plugin ``obj`` to this type of plugin object.

        :param obj: the plugin object to convert from
        :return: an instance of the new plugin object from ``obj``

        This class method will create a new instance of plugin object based on
        ``obj``'s generic attributes (like its label) and the same callable,
        assuming ``obj`` is a different type of plugin object.

        .. seealso::

            The :py:deco:`~sopel.plugin.label` decorator returns a
            :class:`PluginGeneric` that needs to be converted into a plugin
            callable or a plugin job by this class method.

        """
        handler = cls(obj.get_handler())
        handler.plugin_name = obj.plugin_name
        handler.label = obj.label
        handler.threaded = obj.threaded
        handler.doc = obj.doc

        return handler

    @abc.abstractmethod
    def __init__(self, handler: Callable) -> None:
        ...

    @abc.abstractmethod
    def get_handler(self) -> Callable:
        """Return this plugin object's handler.

        :return: the plugin object's handler
        """


class PluginGeneric(AbstractPluginObject):
    @classmethod
    def ensure_callable(
        cls: Type[PluginGeneric],
        obj: Callable | AbstractPluginObject,
    ) -> AbstractPluginObject:
        """Ensure that ``obj`` is a proper plugin object.

        :param obj: a function or a plugin object
        :return: a properly defined plugin object

        If ``obj`` is already an instance of ``AbstractPluginObject``, it is
        returned as-is. Otherwise, a new ``PluginGeneric`` is created from it.

        .. note::

            Since a generic plugin object doesn't hold much value, it never
            converts a specific plugin object into a generic one as to prevent
            meta-data loss.

        """
        if isinstance(obj, AbstractPluginObject):
            return obj

        handler = cls(obj)

        # shared meta data
        handler.label = getattr(obj, 'rule_label', handler.label)
        handler.threaded = getattr(obj, 'thread', handler.threaded)

        return handler

    def __init__(self, handler: Callable) -> None:
        self._handler = handler

        # shared meta data
        self.plugin_name = None
        self.label = self._handler.__name__
        self.threaded = True
        self.doc = inspect.getdoc(self._handler)

    @override
    def get_handler(self) -> Callable:
        return self._handler


class PluginCallable(AbstractPluginObject):
    """Plugin callable, i.e. execute a plugin function when triggered.

    :param handler: a function to be called when the plugin callable is invoked

    .. note::

        You can guard against execution with :attr:`predicates`: all
        predicates must return ``True`` for the callable to execute.
    """
    @property
    @deprecated(
        reason='`echo` is replaced by the `allow_echo` attribute.',
        version='8.1',
        removed_in='9.0',
    )
    def echo(self):
        return self.allow_echo

    @property
    @deprecated(
        reason='`event` is replaced by the `events` attribute.',
        version='8.1',
        removed_in='9.0',
    )
    def event(self):
        return self.events

    @property
    @deprecated(
        reason='`example` is replaced by the `examples` attribute.',
        version='8.1',
        removed_in='9.0',
    )
    def example(self):
        return self.examples

    @property
    @deprecated(
        reason='`rule` is replaced by the `rules` attribute.',
        version='8.1',
        removed_in='9.0',
    )
    def rule(self):
        return self.rules

    @classmethod
    def ensure_callable(
        cls: Type[PluginCallable],
        obj: TypedPluginCallableHandler | AbstractPluginObject,
    ) -> PluginCallable:
        """Ensure that ``obj`` is a plugin callable.

        :param obj: a function or a plugin object
        :return: a properly defined plugin callable

        If ``obj`` is already an instance of ``AbstractPluginObject``, it
        converts it into a plugin callable. Otherwise, a new plugin callable is
        created, using the ``obj`` as its handler.
        """
        if isinstance(obj, cls):
            return obj

        if isinstance(obj, AbstractPluginObject):
            handler = cls.from_plugin_object(obj)
            obj = obj.get_handler()
        else:
            handler = cls(obj)

        # shared meta data
        handler.label = getattr(obj, 'rule_label', handler.label)
        handler.threaded = getattr(obj, 'thread', handler.threaded)

        # meta
        handler.allow_bots = getattr(obj, 'allow_bots', handler.allow_bots)
        handler.allow_echo = getattr(obj, 'echo', handler.allow_echo)
        handler.priority = getattr(obj, 'priority', handler.priority)
        handler.output_prefix = getattr(
            obj, 'output_prefix', handler.output_prefix)
        handler._docs = getattr(obj, '_docs', handler._docs)

        # rules
        handler.events = getattr(obj, 'event', handler.events)
        handler.ctcp = getattr(obj, 'ctcp', handler.ctcp)
        handler.rules = getattr(obj, 'rule', handler.rules)
        handler.rule_lazy_loaders = getattr(
            obj, 'rule_lazy_loaders', handler.rule_lazy_loaders)
        handler.find_rules = getattr(obj, 'find_rules', handler.find_rules)
        handler.search_rules = getattr(
            obj, 'search_rules', handler.search_rules)

        # urls
        handler.url_regex = getattr(obj, 'url_regex', handler.url_regex)
        handler.url_lazy_loaders = getattr(
            obj, 'url_lazy_loaders', handler.url_lazy_loaders)

        # named rules
        handler.commands = getattr(
            obj, 'commands', handler.commands)
        handler.nickname_commands = getattr(
            obj, 'nickname_commands', handler.nickname_commands)
        handler.action_commands = getattr(
            obj, 'action_commands', handler.action_commands)

        # rate limiting
        handler.rate_limit_admins = getattr(obj, 'rate_limit_admins', False)
        handler.user_rate = getattr(obj, 'user_rate', None)
        handler.channel_rate = getattr(obj, 'channel_rate', None)
        handler.global_rate = getattr(obj, 'global_rate', None)
        handler.user_rate_message = getattr(obj, 'user_rate_message', None)
        handler.channel_rate_message = getattr(
            obj, 'channel_rate_message', None)
        handler.global_rate_message = getattr(obj, 'global_rate_message', None)
        handler.default_rate_message = getattr(
            obj, 'default_rate_message', None)
        handler.unblockable = getattr(obj, 'unblockable', handler.unblockable)

        return handler

    @property
    def is_limitable(self) -> bool:
        """Check if the callable is subject to rate limiting.

        :return: ``True`` if it is subject to rate limiting

        Limitable callables aren't necessarily triggerable directly, but they
        all must pass through Sopel's rate-limiting machinery during
        dispatching.
        """
        allowed = any([
            self.rules,
            self.rule_lazy_loaders,
            self.find_rules,
            self.find_rules_lazy_loaders,
            self.search_rules,
            self.search_rules_lazy_loaders,
            self.events,
            self.ctcp,
            self.commands,
            self.nickname_commands,
            self.action_commands,
            self.url_regex,
            self.url_lazy_loaders,
        ])

        return allowed

    @property
    def is_triggerable(self) -> bool:
        """Check if the callable can handle the bot's triggers.

        :return: ``True`` if it can handle the bot's triggers

        A triggerable is a callable that will be used by the bot to handle a
        particular trigger (i.e. an IRC message): it can be a regex rule, an
        event, a CTCP command, a command, a nickname command, or an action
        command. However, it must not be a job or a URL callback.

        .. seealso::

            Many of the decorators defined in :mod:`sopel.plugin` make the
            decorated function a triggerable object.

        """
        forbidden = any([
            self.url_regex,
            self.url_lazy_loaders,
        ])

        allowed = any([
            self.rules,
            self.rule_lazy_loaders,
            self.find_rules,
            self.find_rules_lazy_loaders,
            self.search_rules,
            self.search_rules_lazy_loaders,
            self.events,
            self.ctcp,
            self.commands,
            self.nickname_commands,
            self.action_commands,
        ])

        return allowed and not forbidden

    @property
    def is_url_callback(self) -> bool:
        """Check if the callable can handle a URL callback.

        :return: ``True`` if it can handle a URL callback

        A URL callback handler is a callable that will be used by the bot to
        handle a particular URL in an IRC message.

        .. seealso::

            Both :func:`sopel.plugin.url` :func:`sopel.plugin.url_lazy` make
            the decorated function a URL callback handler.

        """
        allowed = any([
            self.url_regex,
            self.url_lazy_loaders,
        ])

        return allowed

    def __init__(
        self,
        handler: TypedPluginCallableHandler,
    ) -> None:
        self._handler = handler

        # shared meta data
        self.plugin_name: str | None = None
        self.label: str = self._handler.__name__
        self.threaded: bool = True
        self.doc = inspect.getdoc(self._handler)

        # documentation
        self.examples: list[dict] = []
        self._docs: dict = {}

        # rules
        self.events: list = []
        self.ctcp: list = []
        self.commands: list = []
        self.nickname_commands: list = []
        self.action_commands: list = []
        self.rules: list = []
        self.rule_lazy_loaders: list = []
        self.find_rules: list = []
        self.find_rules_lazy_loaders: list = []
        self.search_rules: list = []
        self.search_rules_lazy_loaders: list = []
        self.url_regex: list = []
        self.url_lazy_loaders: list = []

        # allow special conditions
        self.allow_bots: bool = False
        self.allow_echo: bool = False

        # how to run it
        self.priority: Literal['low', 'medium', 'high'] = 'medium'
        self.unblockable: bool = False
        self.predicates: list[TypedCallablePredicate] = []

        # rate limiting
        self.rate_limit_admins: bool = False
        self.user_rate: int | None = None
        self.channel_rate: int | None = None
        self.global_rate: int | None = None
        self.default_rate_message: str | None = None
        self.user_rate_message: str | None = None
        self.channel_rate_message: str | None = None
        self.global_rate_message: str | None = None

        # output management
        self.output_prefix: str = ''

    def __call__(
        self,
        bot: SopelWrapper,
        trigger: Trigger,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        if all(predicate(bot, trigger) for predicate in self.predicates):
            return self._handler(bot, trigger, *args, **kwargs)
        return None

    @override
    def get_handler(self) -> TypedPluginCallableHandler:
        return self._handler

    def setup(self, settings: Config) -> None:
        """Setup of the plugin callable.

        :param settings: the bot's configuration

        This method will be called by the bot before registering the callable.
        It ensures the value of various meta-data.
        """
        nick = settings.core.nick
        help_prefix = settings.core.help_prefix
        docs = []
        examples = []

        if self.is_limitable:
            self.user_rate = self.user_rate or 0
            self.channel_rate = self.channel_rate or 0
            self.global_rate = self.global_rate or 0

        if not self.is_triggerable and not self.is_url_callback:
            return

        if not self.events:
            self.events = ['PRIVMSG']
        else:
            self.events = [event.upper() for event in self.events]

        if self.ctcp:
            # Can be implementation-dependent
            _regex_type = type(re.compile(''))
            self.ctcp = [
                (ctcp_pattern
                    if isinstance(ctcp_pattern, _regex_type)
                    else re.compile(ctcp_pattern, re.IGNORECASE))
                for ctcp_pattern in self.ctcp
            ]

        if not any([
            self.commands,
            self.action_commands,
            self.nickname_commands,
        ]):
            # no need to handle documentation for non-command
            return

        docstring = inspect.getdoc(self._handler)
        if docstring:
            docs = docstring.splitlines()

        if self.examples:
            # If no examples are flagged as user-facing,
            # just show the first one like Sopel<7.0 did
            examples = [
                rec["example"]
                for rec in self.examples
                if rec["is_help"]
            ] or [self.examples[0]["example"]]

            for i, example in enumerate(examples):
                example = example.replace('$nickname', nick)
                if example[0] != help_prefix and not example.startswith(nick):
                    example = example.replace(
                        COMMAND_DEFAULT_HELP_PREFIX, help_prefix, 1)
                examples[i] = example

        if docs or examples:
            for command in self.commands + self.nickname_commands:
                self._docs[command] = (docs, examples)


class PluginJob(AbstractPluginObject):
    @property
    @deprecated(
        reason='`interval` is replaced by the `intervals` attribute.',
        version='8.1',
        removed_in='9.0',
    )
    def interval(self):
        return self.intervals

    @classmethod
    def ensure_callable(
        cls: Type[PluginJob],
        obj: TypedPluginJobHandler | AbstractPluginObject,
    ) -> PluginJob:
        """Ensure that ``obj`` is a plugin job.

        :param obj: a function or a plugin object
        :return: a properly defined plugin job

        If ``obj`` is already an instance of ``AbstractPluginObject``, it
        converts it into a plugin job. Otherwise, a new plugin job is created,
        using the ``obj`` as its handler.
        """
        if isinstance(obj, cls):
            return obj

        if isinstance(obj, AbstractPluginObject):
            handler = cls.from_plugin_object(obj)
            obj = obj.get_handler()
        else:
            handler = cls(obj)

        # jobs
        handler.intervals = getattr(obj, 'interval', handler.intervals)
        handler.threaded = getattr(obj, 'thread', handler.threaded)

        return handler

    def __init__(self, handler: TypedPluginJobHandler):
        self._handler = handler

        # shared meta data
        self.plugin_name: str | None = None
        self.label: str = self._handler.__name__
        self.threaded: bool = True
        self.doc = inspect.getdoc(self._handler)

        # job
        self.intervals: list = []

    def __call__(self, bot: Sopel, *args: Any, **kwargs: Any) -> Any:
        return self._handler(bot, *args, **kwargs)

    @override
    def get_handler(self) -> TypedPluginJobHandler:
        return self._handler

    def setup(self, settings: Config) -> None:
        """Optional setup.

        :param settings: the bot's configuration

        This method will be called by the bot before registering the job.

        .. note::

            This method is a no-op. It exists for subclasses that may need to
            perform operations before registration.

        """


@deprecated(version='8.1', removed_in='9.0')
def clean_callable(func, config):
    """Clean the callable. (compile regexes, fix docs, set defaults)

    :param func: the callable to clean
    :type func: callable
    :param config: Sopel's settings
    :type config: :class:`sopel.config.Config`

    This function will set all the default attributes expected for a Sopel
    callable, i.e. properties related to threading, docs, examples, rate
    limiting, commands, rules, and other features.

    .. deprecated:: 8.1

        This function is made obsolete by the new plugin callable system and
        will be removed in Sopel 9.

    .. versionchanged:: 8.1

        This function used to be defined in ``sopel.loader`` and now sit with
        the Sopel plugin's internal machinery.
    """
    nick = config.core.nick
    help_prefix = config.core.help_prefix
    func._docs = {}
    doc = []
    examples = []

    docstring = inspect.getdoc(func)
    if docstring:
        doc = docstring.splitlines()

    func.thread = getattr(func, 'thread', True)

    if is_limitable(func):
        # These attributes are a waste of memory on callables that don't pass
        # through Sopel's rate-limiting machinery
        func.user_rate = getattr(func, 'user_rate', 0)
        func.channel_rate = getattr(func, 'channel_rate', 0)
        func.global_rate = getattr(func, 'global_rate', 0)
        func.user_rate_message = getattr(func, 'user_rate_message', None)
        func.channel_rate_message = getattr(func, 'channel_rate_message', None)
        func.global_rate_message = getattr(func, 'global_rate_message', None)
        func.default_rate_message = getattr(func, 'default_rate_message', None)
        func.unblockable = getattr(func, 'unblockable', False)

    if not is_triggerable(func) and not is_url_callback(func):
        # Adding the remaining default attributes below is potentially
        # confusing to other code (and a waste of memory) for jobs.
        return

    func.allow_bots = getattr(func, 'allow_bots', False)
    func.echo = getattr(func, 'echo', False)
    func.priority = getattr(func, 'priority', 'medium')
    func.output_prefix = getattr(func, 'output_prefix', '')

    if not hasattr(func, 'event'):
        func.event = ['PRIVMSG']
    else:
        func.event = [event.upper() for event in func.event]

    if any(hasattr(func, attr) for attr in ['commands', 'nickname_commands', 'action_commands']):
        if hasattr(func, 'example'):
            # If no examples are flagged as user-facing,
            # just show the first one like Sopel<7.0 did
            examples = [
                rec["example"]
                for rec in func.example
                if rec["is_help"]
            ] or [func.example[0]["example"]]
            for i, example in enumerate(examples):
                example = example.replace('$nickname', nick)
                if example[0] != help_prefix and not example.startswith(nick):
                    example = example.replace(
                        COMMAND_DEFAULT_HELP_PREFIX, help_prefix, 1)
                examples[i] = example
        if doc or examples:
            cmds: list[str] = []
            cmds.extend(getattr(func, 'commands', []))
            cmds.extend(getattr(func, 'nickname_commands', []))
            for command in cmds:
                func._docs[command] = (doc, examples)

    if hasattr(func, 'ctcp'):
        # Can be implementation-dependent
        _regex_type = type(re.compile(''))
        func.ctcp = [
            (ctcp_pattern
                if isinstance(ctcp_pattern, _regex_type)
                else re.compile(ctcp_pattern, re.IGNORECASE))
            for ctcp_pattern in func.ctcp
        ]


@deprecated(version='8.1', removed_in='9.0')
def is_limitable(obj):
    """Check if ``obj`` needs to carry attributes related to limits.

    :param obj: any :term:`function` to check
    :return: ``True`` if ``obj`` must have limit-related attributes

    Limitable callables aren't necessarily triggerable directly, but they all
    must pass through Sopel's rate-limiting machinery during dispatching.
    Therefore, they must have the attributes checked by that machinery.

    .. deprecated:: 8.1

        This function is made obsolete by the new plugin callable system and
        will be removed in Sopel 9.
    """
    forbidden_attrs = (
        'interval',
    )
    forbidden = any(hasattr(obj, attr) for attr in forbidden_attrs)

    allowed_attrs = (
        'rule',
        'rule_lazy_loaders',
        'find_rules',
        'find_rules_lazy_loaders',
        'search_rules',
        'search_rules_lazy_loaders',
        'event',
        'ctcp',
        'commands',
        'nickname_commands',
        'action_commands',
        'url_regex',
        'url_lazy_loaders',
    )
    allowed = any(hasattr(obj, attr) for attr in allowed_attrs)

    return allowed and not forbidden


@deprecated(version='8.1', removed_in='9.0')
def is_triggerable(obj):
    """Check if ``obj`` can handle the bot's triggers.

    :param obj: any :term:`function` to check
    :return: ``True`` if ``obj`` can handle the bot's triggers

    A triggerable is a callable that will be used by the bot to handle a
    particular trigger (i.e. an IRC message): it can be a regex rule, an
    event, a CTCP command, a command, a nickname command, or an action
    command. However, it must not be a job or a URL callback.

    .. seealso::

        Many of the decorators defined in :mod:`sopel.plugin` make the
        decorated function a triggerable object.

    .. deprecated:: 8.1

        This function is made obsolete by the new plugin callable system and
        will be removed in Sopel 9.
    """
    forbidden_attrs = (
        'interval',
        'url_regex',
        'url_lazy_loaders',
    )
    forbidden = any(hasattr(obj, attr) for attr in forbidden_attrs)

    allowed_attrs = (
        'rule',
        'rule_lazy_loaders',
        'find_rules',
        'find_rules_lazy_loaders',
        'search_rules',
        'search_rules_lazy_loaders',
        'event',
        'ctcp',
        'commands',
        'nickname_commands',
        'action_commands',
    )
    allowed = any(hasattr(obj, attr) for attr in allowed_attrs)

    return allowed and not forbidden


@deprecated(version='8.1', removed_in='9.0')
def is_url_callback(obj):
    """Check if ``obj`` can handle a URL callback.

    :param obj: any :term:`function` to check
    :return: ``True`` if ``obj`` can handle a URL callback

    A URL callback handler is a callable that will be used by the bot to
    handle a particular URL in an IRC message.

    .. seealso::

        Both :func:`sopel.plugin.url` :func:`sopel.plugin.url_lazy` make the
        decorated function a URL callback handler.

    .. deprecated:: 8.1

        This function is made obsolete by the new plugin callable system and
        will be removed in Sopel 9.
    """
    forbidden_attrs = (
        'interval',
    )
    forbidden = any(hasattr(obj, attr) for attr in forbidden_attrs)

    allowed_attrs = (
        'url_regex',
        'url_lazy_loaders',
    )
    allowed = any(hasattr(obj, attr) for attr in allowed_attrs)

    return allowed and not forbidden


def clean_module(
    module: ModuleType,
    config: Config,
) -> tuple[
    list[PluginCallable],   # rules
    list[PluginJob],        # jobs
    list[Callable],         # shutdown
    list[PluginCallable],   # urls
]:
    """Clean a module and return its command, rule, job, etc. callables.

    :param module: the module to clean
    :type module: :term:`module`
    :param config: Sopel's settings
    :type config: :class:`sopel.config.Config`
    :return: a tuple with triggerable, job, shutdown, and url functions
    :rtype: tuple

    This function will parse the ``module`` looking for callables:

    * shutdown actions
    * triggerables (commands, rules, etc.)
    * jobs
    * URL callbacks

    This function will set all the default attributes expected for a Sopel
    callable, i.e. properties related to threading, docs, examples, rate
    limiting, commands, rules, and other features.

    .. versionchanged:: 8.1

        This function used to be defined in ``sopel.loader`` and now sit with
        the Sopel plugin's internal machinery.
    """
    callables: list[PluginCallable] = []
    jobs: list[PluginJob] = []
    shutdowns: list[Callable] = []
    urls: list[PluginCallable] = []
    handler: AbstractPluginObject
    for obj in vars(module).values():
        if callable(obj):
            is_sopel_callable = getattr(obj, '_sopel_callable', False) is True
            if getattr(obj, '__name__', None) == 'shutdown':
                shutdowns.append(obj)
                continue
            elif not is_sopel_callable:
                continue
            elif not isinstance(obj, AbstractPluginObject):
                # compatibility with old-style plugin callables
                # TODO: to be removed in Sopel 9
                clean_callable(obj, config)
                if getattr(obj, 'interval', []):
                    handler = PluginJob.ensure_callable(obj)
                else:
                    handler = PluginCallable.ensure_callable(obj)
            else:
                handler = obj

            if isinstance(handler, PluginJob):
                handler.setup(config)

                if handler.intervals:
                    jobs.append(handler)
                else:
                    LOGGER.error(
                        'Plugin job "%s" has no interval defined',
                        handler.label,
                    )
                    continue

            elif isinstance(handler, PluginCallable):
                handler.setup(config)
                if handler.is_triggerable:
                    callables.append(handler)

                if handler.is_url_callback:
                    urls.append(handler)

            else:
                # it's a subclass of AbstractPluginObject that isn't a
                # plugin job or callable, and it cannot be handled
                continue

    return callables, jobs, shutdowns, urls


class CapabilityNegotiation(enum.Enum):
    """Capability Negotiation status."""

    DONE = enum.auto()
    """The capability negotiation can end.

    This must be returned by a capability request handler to signify to the bot
    that the capability has been properly negotiated and negotiation can end if
    all other conditions are met.
    """

    CONTINUE = enum.auto()
    """The capability negotiation must continue.

    This must be returned by a capability request handler to signify to the bot
    that the capability requires further processing (e.g. SASL
    authentication) and negotiation must not end yet.

    The plugin author MUST signal the bot once the negotiation is done.
    """

    ERROR = enum.auto()
    """The capability negotiation callback was improperly executed.

    If a capability request's handler returns this status, or if it raises an
    exception, the bot will mark the request as errored. A handler can use this
    return value to inform the bot that something wrong happened, without being
    an error in the code itself.
    """


class CapabilityHandler(Protocol):
    """:class:`~typing.Protocol` definition for capability handler.

    When a plugin requests a capability, it can define a callback handler for
    that request using :class:`capability` as a decorator. That handler will be
    called upon Sopel receiving either an ``ACK`` (capability enabled) or a
    ``NAK`` (capability denied) CAP message.

    Example::

        from sopel import plugin
        from sopel.bot import SopelWrapper

        @plugin.capability('example/cap-name')
        def capability_handler(
            cap_req: tuple[str, ...],
            bot: SopelWrapper,
            acknowledged: bool,
        ) -> plugin.CapabilityNegotiation:
            if acknowledged:
                # do something if acknowledged
                # i.e.
                # activate a plugin's feature
                pass
            else:
                # do something else if not
                # i.e. use a fallback mechanism
                # or deactivate a plugin's feature if needed
                pass

            # always return if Sopel can send "CAP END" (DONE)
            # or if the plugin must notify the bot for that later (CONTINUE)
            return plugin.CapabilityNegotiation.DONE

    .. note::

        This protocol class should be used for type checking and documentation
        purposes only.

    """
    def __call__(
        self,
        cap_req: tuple[str, ...],
        bot: SopelWrapper,
        acknowledged: bool,
    ) -> CapabilityNegotiation:
        """A capability handler must be a callable with this signature.

        :param cap_req: the capability request, as a tuple of string
        :param bot: the bot instance
        :param acknowledged: that flag that tells if the capability is enabled
                             or denied
        :return: the return value indicates if the capability negotiation is
                 complete for this request or not
        """


class Capability:
    """Capability request representation.

    .. seealso::

        The decorator :func:`sopel.plugin.capability`.
    """
    def __init__(
        self,
        *cap_req: str,
        handler: CapabilityHandler | None = None,
    ) -> None:
        cap_req_text = ' '.join(cap_req)
        if len(cap_req_text.encode('utf-8')) > 500:
            # "CAP * ACK " is 10 bytes, leaving 500 bytes for the capabilities.
            # Sopel cannot allow multi-line requests, as it won't know how to
            # deal properly with multi-line ACK.
            # The spec says a client SHOULD send multiple requests; however
            # the spec also says that a server will ACK or NAK a whole request
            # at once. So technically, multiple REQs are not the same as a
            # single REQ.
            raise ValueError('Capability request too long: %s' % cap_req_text)

        self._cap_req: tuple[str, ...] = tuple(sorted(cap_req))
        self._handler: CapabilityHandler | None = handler

    def __str__(self) -> str:
        caps = ", ".join(repr(cap) for cap in self._cap_req)
        handler = ""
        if self._handler and hasattr(self._handler, "__name__"):
            handler = " ({}())".format(self._handler.__name__)
        return "<capability {}{}>".format(caps, handler)

    @property
    def cap_req(self) -> tuple[str, ...]:
        """Capability request as a sorted tuple.

        This is the capability request that will be sent to the server as is.
        A request is acknowledged or denied for all the capabilities it
        contains, so the request ``(example/cap1, example/cap2)`` is not the
        same as two requests, one for ``example/cap1`` and the other for
        ``example/cap2``. This makes each request unique.
        """
        return self._cap_req

    def callback(
        self,
        bot: SopelWrapper,
        acknowledged: bool,
    ) -> tuple[bool, CapabilityNegotiation | None]:
        """Execute the acknowlegement callback of a capability request.

        :param bot: a Sopel instance
        :param acknowledged: tell if the capability request is acknowledged
                             (``True``) or deny (``False``)
        :return: a 2-value tuple that contains if the request is done and the
                 result of the handler (if any)

        It executes the handler when the capability request receives an
        acknowledgement (either positive or negative), and returns the result.
        The handler's return value is used to know if the capability
        request is done, or if the bot must wait for resolution from the plugin
        that requested the capability.

        This method returns a 2-value tuple:

        * the first value tells if the negotiation is done for this request
        * the second is the handler's return value (if any)

        If no handler is registered, this automatically returns
        ``(True, None)``, as the negotiation is considered done (without any
        result).

        This doesn't prevent the handler from raising an exception.
        """
        result: CapabilityNegotiation | None = None
        if self._handler is not None:
            result = self._handler(self.cap_req, bot, acknowledged)
            LOGGER.debug(
                'Cap request "%s" got "%s", '
                'executed successfuly with status: %s',
                ' '.join(self.cap_req),
                'ACK' if acknowledged else 'NAK',
                result.name,
            )
        return (result is None or result == CapabilityNegotiation.DONE, result)

    def __call__(
        self,
        handler: CapabilityHandler,
    ) -> Capability:
        """Register a capability negotiation callback."""
        if self._handler is not None:
            raise RuntimeError("Cannot re-use capability decorator")
        self._handler = handler
        return self
