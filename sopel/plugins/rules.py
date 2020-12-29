# coding=utf-8
"""Sopel's plugin rules management.

.. versionadded:: 7.1

.. important::

    This is all fresh and new. Its usage and documentation is for Sopel core
    development and advanced developers. It is subject to rapid changes
    between versions without much (or any) warning.

    Do **not** build your plugin based on what is here, you do **not** need to.

"""
# Copyright 2020, Florian Strzelecki <florian.strzelecki@gmail.com>
#
# Licensed under the Eiffel Forum License 2.
from __future__ import absolute_import, division, print_function, unicode_literals


import datetime
import functools
import inspect
import itertools
import logging
import re
import threading


from sopel import tools
from sopel.config.core_section import (
    COMMAND_DEFAULT_HELP_PREFIX, COMMAND_DEFAULT_PREFIX, URL_DEFAULT_SCHEMES)


try:
    from urllib.parse import urlparse
except ImportError:
    # TODO: remove when dropping Python 2.7
    from urlparse import urlparse

try:
    from inspect import getfullargspec as inspect_getargspec
except ImportError:
    # TODO: remove when dropping Python 2.7
    from inspect import getargspec as inspect_getargspec


__all__ = [
    'Manager',
    'Rule',
    'FindRule',
    'SearchRule',
    'Command',
    'NickCommand',
    'ActionCommand',
    'URLCallback',
]


LOGGER = logging.getLogger(__name__)

IGNORE_RATE_LIMIT = 1  # equivalent to sopel.plugin.NOLIMIT
"""Return value used to indicate that rate-limiting should be ignored."""
PRIORITY_HIGH = 'high'
"""Highest rule priority."""
PRIORITY_MEDIUM = 'medium'
"""Medium rule priority."""
PRIORITY_LOW = 'low'
"""Lowest rule priority."""
PRIORITY_SCALES = {
    PRIORITY_HIGH: 0,
    PRIORITY_MEDIUM: 100,
    PRIORITY_LOW: 1000,
}
"""Mapping of priority label to priority scale."""


def _has_labeled_rule(registry, label, plugin=None):
    rules = (
        itertools.chain(*registry.values())
        if plugin is None
        else registry.get(plugin, [])
    )
    return any(rule.get_rule_label() == label for rule in rules)


def _has_named_rule(registry, name, follow_alias=False, plugin=None):
    rules = registry.values() if plugin is None else [registry.get(plugin, {})]

    has_name = any(
        (name in plugin_rules)
        for plugin_rules in rules
    )
    aliases = (
        rule.has_alias(name)
        for plugin_rules in rules
        for rule in plugin_rules.values()
    )

    return has_name or (follow_alias and any(aliases))


def _clean_callable_examples(examples):
    valid_keys = [
        # message
        'example',
        'result',
        # flags
        'is_private_message',
        'is_help',
        'is_pattern',
        'is_admin',
        'is_owner',
    ]

    return tuple(
        dict(
            (key, value)
            for key, value in example.items()
            if key in valid_keys
        )
        for example in examples
    )


class Manager(object):
    """Manager of plugin rules.

    This manager stores plugin rules and can then provide the matching rules
    for a given trigger.

    To register a rule:

    * :meth:`register` for generic rules
    * :meth:`register_command` for named rules with a prefix
    * :meth:`register_nick_command` for named rules based on nick calling
    * :meth:`register_action_command` for named rules based on ``ACTION``
    * :meth:`register_url_callback` for URL callback rules

    Then to match the rules against a ``trigger``, see the
    :meth:`get_triggered_rules`, which returns a list of ``(rule, match)``,
    sorted by priorities (high first, medium second, and low last).
    """
    def __init__(self):
        self._rules = tools.SopelMemoryWithDefault(list)
        self._commands = tools.SopelMemoryWithDefault(dict)
        self._nick_commands = tools.SopelMemoryWithDefault(dict)
        self._action_commands = tools.SopelMemoryWithDefault(dict)
        self._url_callbacks = tools.SopelMemoryWithDefault(list)
        self._register_lock = threading.Lock()

    def unregister_plugin(self, plugin_name):
        """Unregister all the rules from a plugin.

        :param str plugin_name: the name of the plugin to remove
        :return: the number of rules unregistered for this plugin
        :rtype: int

        All rules, commands, nick commands, and action commands of that plugin
        will be removed from the manager.
        """
        registries = [
            self._rules,
            self._commands,
            self._nick_commands,
            self._action_commands,
            self._url_callbacks,
        ]

        unregistered_rules = 0
        with self._register_lock:
            for registry in registries:
                rules_count = len(registry[plugin_name])
                del registry[plugin_name]
                unregistered_rules = unregistered_rules + rules_count

        LOGGER.debug(
            '[%s] Successfully unregistered %d rules',
            plugin_name,
            unregistered_rules)

        return unregistered_rules

    def register(self, rule):
        """Register a plugin rule.

        :param rule: the rule to register
        :type rule: :class:`Rule`
        """
        with self._register_lock:
            self._rules[rule.get_plugin_name()].append(rule)
        LOGGER.debug('Rule registered: %s', str(rule))

    def register_command(self, command):
        """Register a plugin command.

        :param command: the command to register
        :type command: :class:`Command`
        """
        with self._register_lock:
            plugin = command.get_plugin_name()
            self._commands[plugin][command.name] = command
        LOGGER.debug('Command registered: %s', str(command))

    def register_nick_command(self, command):
        """Register a plugin nick command.

        :param command: the nick command to register
        :type command: :class:`NickCommand`
        """
        with self._register_lock:
            plugin = command.get_plugin_name()
            self._nick_commands[plugin][command.name] = command
        LOGGER.debug('Nick Command registered: %s', str(command))

    def register_action_command(self, command):
        """Register a plugin action command.

        :param command: the action command to register
        :type command: :class:`ActionCommand`
        """
        with self._register_lock:
            plugin = command.get_plugin_name()
            self._action_commands[plugin][command.name] = command
        LOGGER.debug('Action Command registered: %s', str(command))

    def register_url_callback(self, url_callback):
        """Register a plugin URL callback.

        :param url_callback: the URL callback to register
        :type url_callback: :class:`URLCallback`
        """
        with self._register_lock:
            plugin = url_callback.get_plugin_name()
            self._url_callbacks[plugin].append(url_callback)
        LOGGER.debug('URL callback registered: %s', str(url_callback))

    def has_rule(self, label, plugin=None):
        """Tell if the manager knows a rule with this ``label``.

        :param str label: the label of the rule to look for
        :param str plugin: optional filter on the plugin name
        :return: ``True`` if the rule exists, ``False`` otherwise
        :rtype: bool

        The optional parameter ``plugin`` can be provided to limit the rules
        to only those from that plugin.
        """
        return _has_labeled_rule(self._rules, label, plugin)

    def has_command(self, name, follow_alias=True, plugin=None):
        """Tell if the manager knows a command with this ``name``.

        :param str label: the label of the rule to look for
        :param bool follow_alias: optional flag to include aliases
        :param str plugin: optional filter on the plugin name
        :return: ``True`` if the command exists, ``False`` otherwise
        :rtype: bool

        By default, this method follows aliases to search commands. If the
        optional parameter ``follow_alias`` is ``False``, then it won't find
        commands by their aliases::

            >>> command = Command('hi', prefix='"', aliases=['hey'])
            >>> manager.register_command(command)
            >>> manager.has_command('hi')
            True
            >>> manager.has_command('hey')
            True
            >>> manager.has_command('hey', follow_alias=False)
            False

        The optional parameter ``plugin`` can be provided to limit the commands
        to the ones of said plugin.
        """
        return _has_named_rule(self._commands, name, follow_alias, plugin)

    def has_nick_command(self, name, follow_alias=True, plugin=None):
        """Tell if the manager knows a nick command with this ``name``.

        :param str label: the label of the rule to look for
        :param bool follow_alias: optional flag to include aliases
        :param str plugin: optional filter on the plugin name
        :return: ``True`` if the command exists, ``False`` otherwise
        :rtype: bool

        This method works like :meth:`has_command`, but with nick commands.
        """
        return _has_named_rule(self._nick_commands, name, follow_alias, plugin)

    def has_action_command(self, name, follow_alias=True, plugin=None):
        """Tell if the manager knows an action command with this ``name``.

        :param str label: the label of the rule to look for
        :param bool follow_alias: optional flag to include aliases
        :param str plugin: optional filter on the plugin name
        :return: ``True`` if the command exists, ``False`` otherwise
        :rtype: bool

        This method works like :meth:`has_command`, but with action commands.
        """
        return _has_named_rule(
            self._action_commands, name, follow_alias, plugin)

    def has_url_callback(self, label, plugin=None):
        """Tell if the manager knows a URL callback with this ``label``.

        :param str label: the label of the URL callback to look for
        :param str plugin: optional filter on the plugin name
        :return: ``True`` if the URL callback exists, ``False`` otherwise
        :rtype: bool

        The optional parameter ``plugin`` can be provided to limit the URL
        callbacks to only those from that plugin.
        """
        return _has_labeled_rule(self._url_callbacks, label, plugin)

    def get_all_commands(self):
        """Retrieve all the registered commands, by plugin.

        :return: a list of 2-value tuples as ``(key, value)``, where each key
                 is a plugin name, and the value is a ``dict`` of its
                 :term:`commands <Command>`
        """
        # expose a copy of the registered commands
        return self._commands.items()

    def get_all_nick_commands(self):
        """Retrieve all the registered nick commands, by plugin.

        :return: a list of 2-value tuples as ``(key, value)``, where each key
                 is a plugin name, and the value is a ``dict`` of its
                 :term:`nick commands <Nick command>`
        """
        # expose a copy of the registered commands
        return self._nick_commands.items()

    def get_all_action_commands(self):
        """Retrieve all the registered action commands, by plugin.

        :return: a list of 2-value tuples as ``(key, value)``, where each key
                 is a plugin name, and the value is a ``dict`` of its
                 :term:`action commands <Action command>`
        """
        # expose a copy of the registered action commands
        return self._action_commands.items()

    def get_all_generic_rules(self):
        """Retrieve all the registered generic rules, by plugin.

        :return: a list of 2-value tuples as ``(key, value)``, where each key
                 is a plugin name, and the value is a ``list`` of its
                 :term:`generic rules <Generic rule>`
        """
        # expose a copy of the registered generic rules
        return self._rules.items()

    def get_all_url_callbacks(self):
        """Retrieve all the registered URL callbacks, by plugin.

        :return: a list of 2-value tuples as ``(key, value)``, where each key
                 is a plugin name, and the value is a ``list`` of its
                 :term:`URL callbacks <URL callback>`
        """
        # expose a copy of the registered generic rules
        return self._url_callbacks.items()

    def get_triggered_rules(self, bot, pretrigger):
        """Get triggered rules with their match objects, sorted by priorities.

        :param bot: Sopel instance
        :type bot: :class:`sopel.bot.Sopel`
        :param pretrigger: IRC line
        :type pretrigger: :class:`sopel.trigger.PreTrigger`
        :return: a tuple of ``(rule, match)``, sorted by priorities
        :rtype: tuple
        """
        generic_rules = self._rules.values()
        command_rules = (
            rules_dict.values()
            for rules_dict in self._commands.values())
        nick_rules = (
            rules_dict.values()
            for rules_dict in self._nick_commands.values())
        action_rules = (
            rules_dict.values()
            for rules_dict in self._action_commands.values())
        url_callback_rules = self._url_callbacks.values()

        rules = itertools.chain(
            itertools.chain(*generic_rules),
            itertools.chain(*command_rules),
            itertools.chain(*nick_rules),
            itertools.chain(*action_rules),
            itertools.chain(*url_callback_rules),
        )
        matches = (
            (rule, match)
            for rule in rules
            for match in rule.match(bot, pretrigger)
        )
        # Returning a tuple instead of a sorted object ensures that:
        #   1. it's not a lazy object
        #   2. it's an immutable iterable
        # We can't accept lazy evaluation or yield results; it has to be a
        # static list of (rule/match), otherwise Python will raise an error
        # if any rule execution tries to alter the list of registered rules.
        # Making it immutable is the cherry on top.
        return tuple(sorted(matches, key=lambda x: x[0].priority_scale))

    def check_url_callback(self, bot, url):
        """Tell if the ``url`` matches any of the registered URL callbacks.

        :param bot: Sopel instance
        :type bot: :class:`sopel.bot.Sopel`
        :param str url: URL to check
        :return: ``True`` when ``url`` matches any URL callbacks,
                 ``False`` otherwise
        :rtype: bool
        """
        return any(
            any(rule.parse(url))
            for plugin_rules in self._url_callbacks.values()
            for rule in plugin_rules
        )


class AbstractRule(object):
    """Abstract definition of a plugin's rule.

    Any rule class must be an implementation of this abstract class, as it
    defines the Rule interface:

    * plugin name
    * priority
    * label
    * doc, usages, and tests
    * output prefix
    * matching patterns, events, and intents
    * allow echo-message
    * threaded execution or not
    * rate limiting feature
    * text parsing
    * and finally, trigger execution (i.e. actually doing something)

    """
    @classmethod
    def from_callable(cls, settings, handler):
        """Instantiate a rule object from ``settings`` and ``handler``.

        :param settings: Sopel's settings
        :type settings: :class:`sopel.config.Config`
        :param callable handler: a function-based rule handler
        :return: an instance of this class created from the ``handler``
        :rtype: :class:`AbstractRule`

        Sopel's function-based rule handlers are simple callables, decorated
        with :mod:`sopel.plugin`'s decorators to add attributes, such as rate
        limit, threaded execution, output prefix, priority, and so on. In order
        to load these functions as rule objects, this class method can be used;
        it takes the bot's ``settings`` and a cleaned ``handler``.

        A "cleaned handler" is a function, decorated appropriately, and passed
        through the filter of the
        :func:`loader's clean<sopel.loader.clean_callable>` function.
        """
        raise NotImplementedError

    @property
    def priority_scale(self):
        """Rule's priority on a numeric scale.

        This attribute can be used to sort rules between each other, the
        highest priority rules coming first. The default priority for a rule
        is "medium".
        """
        priority_key = self.get_priority()

        return (
            PRIORITY_SCALES.get(priority_key) or
            PRIORITY_SCALES[PRIORITY_MEDIUM]
        )

    def get_plugin_name(self):
        """Get the rule's plugin name.

        :rtype: str

        The rule's plugin name will be used in various places to select,
        register, unregister, and manipulate the rule based on its plugin,
        which is referenced by its name.
        """
        raise NotImplementedError

    def get_rule_label(self):
        """Get the rule's label.

        :rtype: str

        A rule can have a label, which can identify the rule by string, the
        same way a plugin can be identified by its name. This label can be used
        to select, register, unregister, and manipulate the rule based on its
        own label. Note that the label has no effect on the rule's execution.
        """
        raise NotImplementedError

    def get_usages(self):
        """Get the rule's usage examples.

        :rtype: tuple

        A rule can have usage examples, i.e. a list of examples showing how
        the rule can be used, or in what context it can be triggered.
        """
        raise NotImplementedError

    def get_test_parameters(self):
        """Get parameters for automated tests.

        :rtype: tuple

        A rule can have automated tests attached to it, and this method must
        return the test parameters:

        * the expected IRC line
        * the expected line of results, as said by the bot
        * if the user should be an admin or not
        * if the results should be used as regex pattern

        .. seealso::

            :meth:`sopel.plugin.example` for more about test parameters.

        """
        raise NotImplementedError

    def get_doc(self):
        """Get the rule's documentation.

        :rtype: str

        A rule's documentation is a short text that can be displayed to a user
        on IRC upon asking for help about this rule. The equivalent of Python
        docstrings, but for IRC rules.
        """
        raise NotImplementedError

    def get_priority(self):
        """Get the rule's priority.

        :rtype: str

        A rule can have a priority, based on the three pre-defined priorities
        used by Sopel: ``PRIORITY_HIGH``, ``PRIORITY_MEDIUM``, and
        ``PRIORITY_LOW``.

        .. seealso::

            The :attr:`AbstractRule.priority_scale` property uses this method
            to look up the numeric priority value, which is used to sort rules
            by priority.

        """
        raise NotImplementedError

    def get_output_prefix(self):
        """Get the rule's output prefix.

        :rtype: str

        .. seealso::

            See the :class:`sopel.bot.SopelWrapper` class for more information
            on how the output prefix can be used.
        """
        raise NotImplementedError

    def match(self, bot, pretrigger):
        """Match a pretrigger according to the rule.

        :param bot: Sopel instance
        :type bot: :class:`sopel.bot.Sopel`
        :param pretrigger: Line to match
        :type pretrigger: :class:`sopel.trigger.PreTrigger`

        This method must return a list of `match objects`__.

        .. __: https://docs.python.org/3.6/library/re.html#match-objects
        """
        raise NotImplementedError

    def match_event(self, event):
        """Tell if the rule matches this ``event``.

        :param str event: potential matching event
        :return: ``True`` when ``event`` matches the rule, ``False`` otherwise
        :rtype: bool
        """
        raise NotImplementedError

    def match_intent(self, intent):
        """Tell if the rule matches this ``intent``.

        :param str intent: potential matching intent
        :return: ``True`` when ``intent`` matches the rule, ``False`` otherwise
        :rtype: bool
        """
        raise NotImplementedError

    def allow_echo(self):
        """Tell if the rule should match echo messages.

        :return: ``True`` when the rule allows echo messages,
                 ``False`` otherwise
        :rtype: bool
        """
        raise NotImplementedError

    def is_threaded(self):
        """Tell if the rule's execution should be in a thread.

        :return: ``True`` if the execution should be in a thread,
                 ``False`` otherwise
        :rtype: bool
        """
        raise NotImplementedError

    def is_unblockable(self):
        """Tell if the rule is unblockable.

        :return: ``True`` when the rule is unblockable, ``False`` otherwise
        :rtype: bool
        """
        raise NotImplementedError

    def is_rate_limited(self, nick):
        """Tell when the rule reached the ``nick``'s rate limit.

        :return: ``True`` when the rule reached the limit, ``False`` otherwise
        :rtype: bool
        """
        raise NotImplementedError

    def is_channel_rate_limited(self, channel):
        """Tell when the rule reached the ``channel``'s rate limit.

        :return: ``True`` when the rule reached the limit, ``False`` otherwise
        :rtype: bool
        """
        raise NotImplementedError

    def is_global_rate_limited(self):
        """Tell when the rule reached the server's rate limit.

        :return: ``True`` when the rule reached the limit, ``False`` otherwise
        :rtype: bool
        """
        raise NotImplementedError

    def parse(self, text):
        """Parse ``text`` and yield matches.

        :param str text: text to parse by the rule
        :return: yield a list of match object
        :rtype: generator of `re.match`__

        .. __: https://docs.python.org/3.6/library/re.html#match-objects
        """
        raise NotImplementedError

    def execute(self, bot, trigger):
        """Execute the triggered rule.

        :param bot: Sopel wrapper
        :type bot: :class:`sopel.bot.SopelWrapper`
        :param trigger: IRC line
        :type trigger: :class:`sopel.trigger.Trigger`

        This is the method called by the bot when a rule matches a ``trigger``.
        """
        raise NotImplementedError


class Rule(AbstractRule):
    """Generic rule definition.

    A generic rule (or simply "a rule") uses regular expressions to match
    at most once per IRC line per regular expression, i.e. you can trigger
    between 0 and the number of regex the rule has per IRC line.

    Here is an example with a rule with the pattern ``r'hello (\\w+)'``:

    .. code-block:: irc

        <user> hello here
        <Bot> You triggered a rule, saying hello to "here"
        <user> hello sopelunkers
        <Bot> You triggered a rule, saying hello to "sopelunkers"

    Generic rules are not triggered by any specific name, unlike commands which
    have names and aliases.
    """
    @classmethod
    def kwargs_from_callable(cls, handler):
        """Generate the keyword arguments to create a new instance.

        :param callable handler: callable used to generate keyword arguments
        :return: a map of keyword arguments
        :rtype: dict

        This classmethod takes the ``handler``'s attributes to generate a map
        of keyword arguments for the class. This can be used by the
        :meth:`from_callable` classmethod to instantiate a new rule object.

        The expected attributes are the ones set by decorators from the
        :mod:`sopel.plugin` module.
        """
        # manage examples:
        # - usages are for documentation only
        # - tests are examples that can be run and tested
        examples = _clean_callable_examples(
            getattr(handler, 'example', None) or tuple())

        usages = tuple(
            example
            for example in examples
            if example.get('is_help')
        ) or examples and (examples[0],)
        tests = tuple(example for example in examples if example.get('result'))

        return {
            'plugin': getattr(handler, 'plugin_name', None),
            'label': getattr(handler, 'rule_label', None),
            'priority': getattr(handler, 'priority', PRIORITY_MEDIUM),
            'events': getattr(handler, 'event', []),
            'intents': getattr(handler, 'intents', []),
            'allow_echo': getattr(handler, 'echo', False),
            'threaded': getattr(handler, 'thread', True),
            'output_prefix': getattr(handler, 'output_prefix', ''),
            'unblockable': getattr(handler, 'unblockable', False),
            'rate_limit': getattr(handler, 'rate', 0),
            'channel_rate_limit': getattr(handler, 'channel_rate', 0),
            'global_rate_limit': getattr(handler, 'global_rate', 0),
            'usages': usages or tuple(),
            'tests': tests,
            'doc': inspect.getdoc(handler),
        }

    @classmethod
    def from_callable(cls, settings, handler):
        regexes = tuple(handler.rule)
        kwargs = cls.kwargs_from_callable(handler)
        kwargs['handler'] = handler

        return cls(regexes, **kwargs)

    def __init__(self,
                 regexes,
                 plugin=None,
                 label=None,
                 priority=PRIORITY_MEDIUM,
                 handler=None,
                 events=None,
                 intents=None,
                 allow_echo=False,
                 threaded=True,
                 output_prefix=None,
                 unblockable=False,
                 rate_limit=0,
                 channel_rate_limit=0,
                 global_rate_limit=0,
                 usages=None,
                 tests=None,
                 doc=None):
        # core
        self._regexes = regexes
        self._plugin_name = plugin
        self._label = label
        self._priority = priority or PRIORITY_MEDIUM
        self._handler = handler

        # filters
        self._events = events or ['PRIVMSG']
        self._intents = intents or []
        self._allow_echo = bool(allow_echo)

        # execution
        self._threaded = bool(threaded)
        self._output_prefix = output_prefix or ''

        # rate limiting
        self._unblockable = bool(unblockable)
        self._rate_limit = rate_limit
        self._channel_rate_limit = channel_rate_limit
        self._global_rate_limit = global_rate_limit

        # metrics
        self._metrics_nick = {}
        self._metrics_sender = {}
        self._metrics_global = None

        # docs & tests
        self._usages = usages or tuple()
        self._tests = tests or tuple()
        self._doc = doc or ''

    def __str__(self):
        try:
            label = self.get_rule_label()
        except RuntimeError:
            label = '(generic)'

        plugin = self.get_plugin_name() or '(no-plugin)'

        return '<%s %s.%s (%d)>' % (
            self.__class__.__name__, plugin, label, len(self._regexes))

    def get_plugin_name(self):
        return self._plugin_name

    def get_rule_label(self):
        """Get the rule's label.

        :rtype: str
        :raise RuntimeError: when the label is undefined

        Return its label if it has one, or the value of its ``handler``'s
        ``__name__``, if it has a handler. If both methods fail, a
        :exc:`RuntimeError` is raised because the rule has an undefined label.
        """
        if self._label:
            return self._label

        if self._handler and self._handler.__name__:
            return self._handler.__name__

        raise RuntimeError('Undefined rule label')

    def get_usages(self):
        return tuple(
            {
                'text': usage['example'],
                'result': usage.get('result', None),
                'is_pattern': bool(usage.get('is_pattern')),
                'is_admin': bool(usage.get('is_admin')),
                'is_owner': bool(usage.get('is_owner')),
                'is_private_message': bool(usage.get('is_private_message')),
            }
            for usage in self._usages
            if usage.get('example')
        )

    def get_test_parameters(self):
        return self._tests or tuple()

    def get_doc(self):
        return self._doc

    def get_priority(self):
        return self._priority

    def get_output_prefix(self):
        return self._output_prefix

    def match(self, bot, pretrigger):
        args = pretrigger.args
        text = args[-1] if args else ''

        if not self.match_preconditions(bot, pretrigger):
            return []

        # parse text
        return self.parse(text)

    def match_preconditions(self, bot, pretrigger):
        event = pretrigger.event
        intent = pretrigger.tags.get('intent')
        nick = pretrigger.nick
        is_echo_message = (
            nick.lower() == bot.nick.lower() and
            event in ["PRIVMSG", "NOTICE"]
        )

        return (
            self.match_event(event) and
            self.match_intent(intent) and
            (not is_echo_message or self.allow_echo())
        )

    def parse(self, text):
        for regex in self._regexes:
            result = regex.match(text)
            if result:
                yield result

    def match_event(self, event):
        return bool(event and event in self._events)

    def match_intent(self, intent):
        if not self._intents:
            return True

        return bool(intent and any(
            regex.match(intent)
            for regex in self._intents
        ))

    def allow_echo(self):
        return self._allow_echo

    def is_threaded(self):
        return self._threaded

    def is_unblockable(self):
        return self._unblockable

    def is_rate_limited(self, nick):
        metrics = self._metrics_nick.get(nick)
        if metrics is None:
            return False
        last_usage_at, exit_code = metrics

        if exit_code == IGNORE_RATE_LIMIT:
            return False

        now = datetime.datetime.utcnow()
        rate_limit = datetime.timedelta(seconds=self._rate_limit)
        return (now - last_usage_at) <= rate_limit

    def is_channel_rate_limited(self, channel):
        metrics = self._metrics_sender.get(channel)
        if metrics is None:
            return False
        last_usage_at, exit_code = metrics

        if exit_code == IGNORE_RATE_LIMIT:
            return False

        now = datetime.datetime.utcnow()
        rate_limit = datetime.timedelta(seconds=self._channel_rate_limit)
        return (now - last_usage_at) <= rate_limit

    def is_global_rate_limited(self):
        metrics = self._metrics_global
        if metrics is None:
            return False
        last_usage_at, exit_code = metrics

        if exit_code == IGNORE_RATE_LIMIT:
            return False

        now = datetime.datetime.utcnow()
        rate_limit = datetime.timedelta(seconds=self._global_rate_limit)
        return (now - last_usage_at) <= rate_limit

    def execute(self, bot, trigger):
        if not self._handler:
            raise RuntimeError('Improperly configured rule: no handler')

        # execute the handler
        exit_code = self._handler(bot, trigger)

        # register metrics
        now = datetime.datetime.utcnow()
        self._metrics_nick[trigger.nick] = (now, exit_code)
        self._metrics_sender[trigger.sender] = (now, exit_code)
        self._metrics_global = (now, exit_code)

        # return exit code
        return exit_code


class NamedRuleMixin(object):
    """Mixin for named rules.

    A named rule is invoked by using a specific word, and is usually known
    as a "command". For example, the command "hello" is triggered by using
    the word "hello" with some sort of prefix or context.

    A named rule can be invoked by using one of its aliases, also.
    """
    @property
    def name(self):
        return self._name

    @property
    def aliases(self):
        return self._aliases

    def get_rule_label(self):
        """Get the rule's label.

        :rtype: str

        A named rule's label is its name.
        """
        return self._name.replace(' ', '-')

    def has_alias(self, name):
        """Tell when ``name`` is one of the rule's aliases.

        :param str name: potential alias name
        :return: ``True`` when ``name`` is an alias, ``False`` otherwise
        :rtype: bool
        """
        return name in self._aliases

    def escape_name(self, name):
        """Escape the provided name if needed.

        .. note::

            Until now, Sopel has allowed command name to be regex pattern.
            It was mentioned in the documentation without much details, and
            there were no tests for it.

            In order to ensure backward compatibility with previous versions of
            Sopel, we make sure to escape command name only when it's needed.

            **It is not recommended to use a regex pattern for your command
            name. This feature will be removed in Sopel 8.0.**

        """
        if set('.^$*+?{}[]\\|()') & set(name):
            # the name contains a regex pattern special character
            # we assume the user knows what they are doing
            try:
                # make sure it compiles properly
                # (nobody knows what they are doing)
                re.compile(name)
            except re.error as error:
                original_name = name
                name = re.escape(name)
                LOGGER.warning(
                    'Command name "%s" is an invalid regular expression '
                    'and will be replaced by "%s": %s',
                    original_name, name, error)
        else:
            name = re.escape(name)

        return name


class Command(NamedRuleMixin, Rule):
    """Command rule definition.

    A command rule (or simply "a command") is a named rule, i.e. it has a known
    name and must be invoked using that name (or one of its aliases, if any).
    Apart from that, it behaves exactly like a :class:`generic rule <Rule>`.

    Here is an example with the ``dummy`` command:

    .. code-block:: irc

        <user> .dummy
        <Bot> You just invoked the command 'dummy'
        <user> .dummy-alias
        <Bot> You just invoked the command 'dummy' (as 'dummy-alias')

    """
    # This regexp matches equivalently and produces the same
    # groups 1 and 2 as the old regexp: r'^%s(%s)(?: +(.*))?$'
    # The only differences should be handling all whitespace
    # like spaces and the addition of groups 3-6.
    PATTERN_TEMPLATE = r"""
        (?:{prefix})({command}) # Command as group 1.
        (?:\s+              # Whitespace to end command.
        (                   # Rest of the line as group 2.
        (?:(\S+))?          # Parameters 1-4 as groups 3-6.
        (?:\s+(\S+))?
        (?:\s+(\S+))?
        (?:\s+(\S+))?
        .*                  # Accept anything after the parameters.
                            # Leave it up to the plugin to parse the line.
        ))?                 # Group 2 must be None, if there are no parameters.
        $                   # EoL, so there are no partial matches.
    """

    @classmethod
    def from_callable(cls, settings, handler):
        prefix = settings.core.prefix
        help_prefix = settings.core.help_prefix
        commands = getattr(handler, 'commands', [])
        if not commands:
            raise RuntimeError('Invalid command callable: %s' % handler)

        name = commands[0]
        aliases = commands[1:]
        kwargs = cls.kwargs_from_callable(handler)
        kwargs.update({
            'name': name,
            'prefix': prefix,
            'help_prefix': help_prefix,
            'aliases': aliases,
            'handler': handler,
        })

        return cls(**kwargs)

    def __init__(self,
                 name,
                 prefix=COMMAND_DEFAULT_PREFIX,
                 help_prefix=COMMAND_DEFAULT_HELP_PREFIX,
                 aliases=None,
                 **kwargs):
        super(Command, self).__init__([], **kwargs)
        self._name = name
        self._prefix = prefix
        self._help_prefix = help_prefix
        self._aliases = tuple(aliases) if aliases is not None else tuple()
        self._regexes = (self.get_rule_regex(),)

    def __str__(self):
        label = self.get_rule_label()
        plugin = self.get_plugin_name() or '(no-plugin)'
        aliases = '|'.join(self._aliases)

        return '<Command %s.%s [%s]>' % (plugin, label, aliases)

    def get_usages(self):
        usages = []

        for usage in self._usages:
            text = usage.get('example')
            if not text:
                continue

            if text[0] != self._help_prefix:
                text = text.replace(
                    COMMAND_DEFAULT_HELP_PREFIX, self._help_prefix, 1)

            new_usage = {
                'text': text,
                'result': usage.get('result', None),
                'is_pattern': bool(usage.get('is_pattern')),
                'is_admin': bool(usage.get('is_admin')),
                'is_owner': bool(usage.get('is_owner')),
                'is_private_message': bool(usage.get('is_private_message')),
            }
            usages.append(new_usage)

        return tuple(usages)

    def get_rule_regex(self):
        """Make the rule regex for this command.

        :return: a compiled regex for this command and its aliases

        The command regex factors in:

        * the prefix regular expression,
        * the rule's name (escaped for regex if needed),
        * all of its aliases (escaped for regex if needed),

        to create a compiled regex to return.
        """
        name = [self.escape_name(self._name)]
        aliases = [self.escape_name(alias) for alias in self._aliases]
        pattern = r'|'.join(name + aliases)

        # Escape all whitespace with a single backslash.
        # This ensures that regexp in the prefix is treated as it was before
        # the actual regexp was changed to use the verbose syntax.
        prefix = re.sub(r"(\s)", r"\\\1", self._prefix)
        pattern = self.PATTERN_TEMPLATE.format(prefix=prefix, command=pattern)
        return re.compile(pattern, re.IGNORECASE | re.VERBOSE)


class NickCommand(NamedRuleMixin, Rule):
    """Nickname Command rule definition.

    A nickname command rule is a named rule with a twist: instead of a prefix,
    the rule is triggered when the line starts with a registered nickname (or
    one of its aliases). The command's name itself can have aliases too.

    Here is an example with the ``dummy`` nickname command:

    .. code-block:: irc

        <user> BotName: dummy
        <Bot> You just invoked the nick command 'dummy'
        <user> AliasBotName: dummy
        <Bot> You just invoked the nick command 'dummy'
        <user> BotName: dummy-alias
        <Bot> You just invoked the nick command 'dummy' (as 'dummy-alias')
        <user> AliasBotName: dummy-alias
        <Bot> You just invoked the nick command 'dummy' (as 'dummy-alias')

    Apart from that, it behaves exactly like a :class:`generic rule <Rule>`.
    """
    PATTERN_TEMPLATE = r"""
        ^
        $nickname[:,]? # Nickname.
        \s+({command}) # Command as group 1.
        (?:\s+         # Whitespace to end command.
        (              # Rest of the line as group 2.
        (?:(\S+))?     # Parameters 1-4 as groups 3-6.
        (?:\s+(\S+))?
        (?:\s+(\S+))?
        (?:\s+(\S+))?
        .*             # Accept anything after the parameters. Leave it up to
                       # the plugin to parse the line.
        ))?            # Group 1 must be None, if there are no parameters.
        $              # EoL, so there are no partial matches.
    """

    @classmethod
    def from_callable(cls, settings, handler):
        nick = settings.core.nick
        nick_aliases = tuple(settings.core.alias_nicks)
        commands = getattr(handler, 'nickname_commands', [])
        if not commands:
            raise RuntimeError('Invalid nick command callable: %s' % handler)

        name = commands[0]
        aliases = commands[1:]
        kwargs = cls.kwargs_from_callable(handler)
        kwargs.update({
            'nick': nick,
            'name': name,
            'nick_aliases': nick_aliases,
            'aliases': aliases,
            'handler': handler,
        })

        return cls(**kwargs)

    def __init__(self, nick, name, nick_aliases=None, aliases=None, **kwargs):
        super(NickCommand, self).__init__([], **kwargs)
        self._nick = nick
        self._name = name
        self._nick_aliases = (tuple(nick_aliases)
                              if nick_aliases is not None
                              else tuple())
        self._aliases = tuple(aliases) if aliases is not None else tuple()
        self._regexes = (self.get_rule_regex(),)

    def __str__(self):
        label = self.get_rule_label()
        plugin = self.get_plugin_name() or '(no-plugin)'
        aliases = '|'.join(self._aliases)
        nick = self._nick
        nick_aliases = '|'.join(self._nick_aliases)

        return '<NickCommand %s.%s [%s] (%s [%s])>' % (
            plugin, label, aliases, nick, nick_aliases)

    def get_usages(self):
        usages = []

        for usage in self._usages:
            text = usage.get('example')
            if not text:
                continue

            new_usage = {
                'text': text.replace('$nickname', self._nick),
                'result': usage.get('result', None),
                'is_pattern': bool(usage.get('is_pattern')),
                'is_admin': bool(usage.get('is_admin')),
                'is_owner': bool(usage.get('is_owner')),
                'is_private_message': bool(usage.get('is_private_message')),
            }
            usages.append(new_usage)

        return tuple(usages)

    def get_rule_regex(self):
        """Make the rule regex for this nick command.

        :return: a compiled regex for this nick command and its aliases

        The command regex factors in:

        * the nicks to react to,
        * the rule's name (escaped for regex),
        * all of its aliases (escaped for regex),

        to create a compiled regex to return.
        """
        name = [self.escape_name(self._name)]
        aliases = [self.escape_name(alias) for alias in self._aliases]
        pattern = r'|'.join(name + aliases)
        return tools.compile_rule(
            self._nick,
            self.PATTERN_TEMPLATE.format(command=pattern),
            self._nick_aliases)


class ActionCommand(NamedRuleMixin, Rule):
    """Action Command rule definition.

    An action command rule is a named rule that can be triggered only when the
    trigger's intent is an ``ACTION``. Like the :class:`Command` rule, it
    allows command aliases.

    Here is an example with the ``dummy`` action command:

    .. code-block:: irc

        > user dummy
        <Bot> You just invoked the action command 'dummy'
        > user dummy-alias
        <Bot> You just invoked the action command 'dummy' (as 'dummy-alias')

    Apart from that, it behaves exactly like a :class:`generic rule <Rule>`.
    """
    INTENT_REGEX = re.compile(r'ACTION', re.IGNORECASE)
    PATTERN_TEMPLATE = r"""
        ({command})         # Command as group 1.
        (?:\s+              # Whitespace to end command.
        (                   # Rest of the line as group 2.
        (?:(\S+))?          # Parameters 1-4 as groups 3-6.
        (?:\s+(\S+))?
        (?:\s+(\S+))?
        (?:\s+(\S+))?
        .*                  # Accept anything after the parameters.
                            # Leave it up to the plugin to parse
                            # the line.
        ))?                 # Group 2 must be None, if there are no
                            # parameters.
        $                   # EoL, so there are no partial matches.
    """

    @classmethod
    def from_callable(cls, settings, handler):
        commands = getattr(handler, 'action_commands', [])
        if not commands:
            raise RuntimeError('Invalid action command callable: %s' % handler)

        name = commands[0]
        aliases = commands[1:]
        kwargs = cls.kwargs_from_callable(handler)
        kwargs.update({
            'name': name,
            'aliases': aliases,
            'handler': handler,
        })

        return cls(**kwargs)

    def __init__(self, name, aliases=None, **kwargs):
        super(ActionCommand, self).__init__([], **kwargs)
        self._name = name
        self._aliases = tuple(aliases) if aliases is not None else tuple()
        self._regexes = (self.get_rule_regex(),)

    def __str__(self):
        label = self.get_rule_label()
        plugin = self.get_plugin_name() or '(no-plugin)'
        aliases = '|'.join(self._aliases)

        return '<ActionCommand %s.%s [%s]>' % (plugin, label, aliases)

    def get_rule_regex(self):
        """Make the rule regex for this action command.

        :return: a compiled regex for this action command and its aliases

        The command regex factors in:

        * the rule's name (escaped for regex if needed),
        * all of its aliases (escaped for regex if needed),

        to create a compiled regex to return.
        """
        name = [self.escape_name(self._name)]
        aliases = [self.escape_name(alias) for alias in self._aliases]
        pattern = r'|'.join(name + aliases)
        pattern = self.PATTERN_TEMPLATE.format(command=pattern)
        return re.compile(pattern, re.IGNORECASE | re.VERBOSE)

    def match_intent(self, intent):
        """Tell if ``intent`` is an ``ACTION``.

        :param str intent: potential matching intent
        :return: ``True`` when ``intent`` matches ``ACTION``,
                 ``False`` otherwise
        :rtype: bool
        """
        return bool(intent and self.INTENT_REGEX.match(intent))


class FindRule(Rule):
    """Anonymous find rule definition.

    A find rule is like an anonymous rule with a twist: instead of matching
    only once per IRC line, a find rule will execute for each non-overlapping
    match for each of its regular expressions.

    For example, to match for each word starting with the letter ``h`` in a line,
    you can use the pattern ``h\\w+``:

    .. code-block:: irc

        <user> hello here
        <Bot> Found the word "hello"
        <Bot> Found the word "here"
        <user> sopelunker, how are you?
        <Bot> Found the word "how"

    .. seealso::

        This rule uses :func:`re.finditer`. To know more about how it works,
        see the official Python documentation.

    """
    @classmethod
    def from_callable(cls, settings, handler):
        regexes = tuple(handler.find_rules)
        kwargs = cls.kwargs_from_callable(handler)
        kwargs['handler'] = handler

        return cls(regexes, **kwargs)

    def parse(self, text):
        for regex in self._regexes:
            for match in regex.finditer(text):
                yield match


class SearchRule(Rule):
    """Anonymous search rule definition.

    A search rule is like an anonymous rule with a twist: it will execute
    exactly once per regular expression that matches anywhere in a line, not
    just from the start.

    For example, to search if any word starts with the letter ``h`` in a line,
    you can use the pattern ``h\\w+``:

    .. code-block:: irc

        <user> hello here
        <Bot> Found the word "hello"
        <user> sopelunker, how are you?
        <Bot> Found the word "how"

    The match object it returns contains the first element that matches the
    expression in the line.

    .. seealso::

        This rule uses :func:`re.search`. To know more about how it works,
        see the official Python documentation.

    """
    @classmethod
    def from_callable(cls, settings, handler):
        regexes = tuple(handler.search_rules)
        kwargs = cls.kwargs_from_callable(handler)
        kwargs['handler'] = handler

        return cls(regexes, **kwargs)

    def parse(self, text):
        for regex in self._regexes:
            match = regex.search(text)
            if match:
                yield match


class URLCallback(Rule):
    """URL callback rule definition.

    A URL callback rule (or simply "a URL rule") detects URLs in a trigger
    then it uses regular expressions to match at most once per URL per regular
    expression, i.e. you can trigger between 0 and the number of regex the URL
    callback has per URL in the IRC line.

    Here is an example with a URL rule with the pattern
    ``r'https://example\\.com/(.*)'``:

    .. code-block:: irc

        <user> https://example.com/test
        <Bot> You triggered a URL callback, with the "/test" path
        <user> and this URL is https://example.com/other can you get it?
        <Bot> You triggered a URL callback, with the "/other" path

    Like generic rules, URL callback rules are not triggered by any specific
    name and they don't have aliases.

    .. note::

        Unlike generic rules and commands, the :func:`~sopel.plugin.url`
        decorator expects its decorated function to have the bot and the
        trigger with a third parameter: the ``match`` parameter.

        To use this class with an existing URL callback handler, the
        :meth:`from_callable` classmethod **must** be used: it will wrap the
        handler to work as intended. In that case, the ``trigger`` and the
        ``match`` arguments will be the same when the rule executes.

        This behavior makes the ``match`` parameter obsolete, which will be
        removed in Sopel 9.

    """
    @classmethod
    def from_callable(cls, settings, handler):
        execute_handler = handler
        url_regexes = getattr(handler, 'url_regex', []) or []
        if not url_regexes:
            raise RuntimeError(
                'Invalid URL callback: %s' % handler)

        kwargs = cls.kwargs_from_callable(handler)

        # do we need to handle the match parameter?
        # old style URL callback: callable(bot, trigger, match)
        # new style: callable(bot, trigger)
        match_count = 3
        if inspect.ismethod(handler):
            # account for the 'self' parameter when the handler is a method
            match_count = 4

        argspec = inspect_getargspec(handler)

        if len(argspec.args) >= match_count:
            @functools.wraps(handler)
            def execute_handler(bot, trigger):
                return handler(bot, trigger, match=trigger)

        kwargs.update({
            'handler': execute_handler,
            'schemes': settings.core.auto_url_schemes,
        })

        return cls(url_regexes, **kwargs)

    @classmethod
    def from_callable_lazy(cls, settings, handler):
        """Instantiate a rule object from a handler with lazy-loaded regexes.

        :param settings: Sopel's settings
        :type settings: :class:`sopel.config.Config`
        :param callable handler: a function-based rule handler with a
                                 lazy-loader for the regexes
        :return: an instance of this class created from the ``handler``
        :rtype: :class:`AbstractRule`

        Similar to the :meth:`from_callable` classmethod, it requires a rule
        handlers decorated with :mod:`sopel.plugin`'s decorators.

        Unlike the :meth:`from_callable` classmethod, the regexes are not
        already attached to the handler: its loader functions will be used to
        get the rule's regexes. See the :func:`sopel.plugin.url_lazy` decorator
        for more information about the handler and the loaders' signatures.

        .. seealso::

            The handler can have more than one loader attached. In that case,
            these loaders are chained with :func:`sopel.tools.chain_loaders`.

        """
        url_lazy_loaders = getattr(handler, 'url_lazy_loaders', [])
        if not url_lazy_loaders:
            raise RuntimeError(
                'Invalid lazy loader URL callback: %s' % handler)

        loader = tools.chain_loaders(*url_lazy_loaders)
        regexes = loader(settings)

        if not regexes:
            raise RuntimeError(
                'Invalid lazy loader URL callback: %s' % handler)

        kwargs = cls.kwargs_from_callable(handler)
        kwargs.update({
            'handler': handler,
            'schemes': settings.core.auto_url_schemes,
        })

        return cls(regexes, **kwargs)

    def __init__(self,
                 regexes,
                 schemes=None,
                 **kwargs):
        super(URLCallback, self).__init__(regexes, **kwargs)
        # prevent mutability of registered schemes
        self._schemes = tuple(schemes or URL_DEFAULT_SCHEMES)

    def match(self, bot, pretrigger):
        """Match URL(s) in a pretrigger according to the rule.

        :param bot: Sopel instance
        :type bot: :class:`sopel.bot.Sopel`
        :param pretrigger: Line to match
        :type pretrigger: :class:`sopel.trigger.PreTrigger`

        This method looks for :attr:`URLs in the IRC line
        <sopel.trigger.PreTrigger.urls>`, and for each it yields
        :ref:`match objects <match-objects>` using its regexes.

        .. seealso::

            To detect URLs, this method uses the
            :attr:`core.auto_url_schemes
            <sopel.config.core_section.CoreSection.auto_url_schemes>` option.

        """
        if not self.match_preconditions(bot, pretrigger):
            return

        urls = (
            url
            for url in pretrigger.urls
            if urlparse(url).scheme in self._schemes
        )

        # Parse URL for each found
        for url in urls:
            # TODO: convert to 'yield from' when dropping Python 2.7
            for result in self.parse(url):
                yield result

    def parse(self, text):
        for regex in self._regexes:
            result = regex.search(text)
            if result:
                yield result
