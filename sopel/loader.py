# coding=utf-8
"""Utility functions to manage plugin callables from a Python module.

.. important::

    Its usage and documentation is for Sopel core development and advanced
    developers. It is subject to rapid changes between versions without much
    (or any) warning.

    Do **not** build your plugin based on what is here, you do **not** need to.

"""
from __future__ import absolute_import, division, print_function, unicode_literals

import inspect
import logging
import re
import sys

from sopel.config.core_section import COMMAND_DEFAULT_HELP_PREFIX
from sopel.tools import deprecated, itervalues


if sys.version_info.major >= 3:
    basestring = (str, bytes)


LOGGER = logging.getLogger(__name__)


@deprecated(
    reason="Replaced by simple logic using inspect.getdoc()",
    version='7.1',
    removed_in='8.0',
)
def trim_docstring(doc):
    """Get the docstring as a series of lines that can be sent.

    :param str doc: a callable's docstring to trim
    :return: a list of trimmed lines
    :rtype: list

    This function acts like :func:`inspect.cleandoc` but doesn't replace tabs,
    and instead of a :class:`str` it returns a :class:`list`.
    """
    if not doc:
        return []
    lines = doc.expandtabs().splitlines()
    indent = sys.maxsize
    for line in lines[1:]:
        stripped = line.lstrip()
        if stripped:
            indent = min(indent, len(line) - len(stripped))
    trimmed = [lines[0].strip()]
    if indent < sys.maxsize:
        for line in lines[1:]:
            trimmed.append(line[:].rstrip())
    while trimmed and not trimmed[-1]:
        trimmed.pop()
    while trimmed and not trimmed[0]:
        trimmed.pop(0)
    return trimmed


def clean_callable(func, config):
    """Clean the callable. (compile regexes, fix docs, set defaults)

    :param func: the callable to clean
    :type func: callable
    :param config: Sopel's settings
    :type config: :class:`sopel.config.Config`

    This function will set all the default attributes expected for a Sopel
    callable, i.e. properties related to threading, docs, examples, rate
    limiting, commands, rules, and other features.
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
        func.rate = getattr(func, 'rate', 0)
        func.channel_rate = getattr(func, 'channel_rate', 0)
        func.global_rate = getattr(func, 'global_rate', 0)
        func.unblockable = getattr(func, 'unblockable', False)

    if not is_triggerable(func) and not is_url_callback(func):
        # Adding the remaining default attributes below is potentially
        # confusing to other code (and a waste of memory) for jobs.
        return

    func.echo = getattr(func, 'echo', False)
    func.priority = getattr(func, 'priority', 'medium')
    func.output_prefix = getattr(func, 'output_prefix', '')

    if not hasattr(func, 'event'):
        func.event = ['PRIVMSG']
    else:
        if isinstance(func.event, basestring):
            func.event = [func.event.upper()]
        else:
            func.event = [event.upper() for event in func.event]

    # TODO: remove in Sopel 8
    # Stay compatible with old Phenny/Jenni "modules" (plugins)
    # that set the attribute directly
    if hasattr(func, 'rule') and isinstance(func.rule, basestring):
        LOGGER.warning(
            'The `rule` attribute of %s.%s should be a list, not a string; '
            'this behavior is deprecated in Sopel 7.1 '
            'and will be removed in Sopel 8. '
            'To prevent this problem always use `sopel.plugin.rule(%r)`.',
            func.__module__, func.__name__, func.rule)
        func.rule = [func.rule]

    if any(hasattr(func, attr) for attr in ['commands', 'nickname_commands', 'action_commands']):
        if hasattr(func, 'example'):
            # If no examples are flagged as user-facing, just show the first one like Sopel<7.0 did
            examples = [rec["example"] for rec in func.example if rec["help"]] or [func.example[0]["example"]]
            for i, example in enumerate(examples):
                example = example.replace('$nickname', nick)
                if example[0] != help_prefix and not example.startswith(nick):
                    example = example.replace(
                        COMMAND_DEFAULT_HELP_PREFIX, help_prefix, 1)
                examples[i] = example
        if doc or examples:
            cmds = []
            cmds.extend(getattr(func, 'commands', []))
            cmds.extend(getattr(func, 'nickname_commands', []))
            for command in cmds:
                func._docs[command] = (doc, examples)

    if hasattr(func, 'intents'):
        # Can be implementation-dependent
        _regex_type = type(re.compile(''))
        func.intents = [
            (intent
                if isinstance(intent, _regex_type)
                else re.compile(intent, re.IGNORECASE))
            for intent in func.intents
        ]


def is_limitable(obj):
    """Check if ``obj`` needs to carry attributes related to limits.

    :param obj: any :term:`function` to check
    :return: ``True`` if ``obj`` must have limit-related attributes

    Limitable callables aren't necessarily triggerable directly, but they all
    must pass through Sopel's rate-limiting machinery during dispatching.
    Therefore, they must have the attributes checked by that machinery.
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
        'intents',
        'commands',
        'nickname_commands',
        'action_commands',
        'url_regex',
        'url_lazy_loaders',
    )
    allowed = any(hasattr(obj, attr) for attr in allowed_attrs)

    return allowed and not forbidden


def is_triggerable(obj):
    """Check if ``obj`` can handle the bot's triggers.

    :param obj: any :term:`function` to check
    :return: ``True`` if ``obj`` can handle the bot's triggers

    A triggerable is a callable that will be used by the bot to handle a
    particular trigger (i.e. an IRC message): it can be a regex rule, an
    event, an intent, a command, a nickname command, or an action command.
    However, it must not be a job or a URL callback.

    .. seealso::

        Many of the decorators defined in :mod:`sopel.plugin` make the
        decorated function a triggerable object.

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
        'intents',
        'commands',
        'nickname_commands',
        'action_commands',
    )
    allowed = any(hasattr(obj, attr) for attr in allowed_attrs)

    return allowed and not forbidden


def is_url_callback(obj):
    """Check if ``obj`` can handle a URL callback.

    :param obj: any :term:`function` to check
    :return: ``True`` if ``obj`` can handle a URL callback

    A URL callback handler is a callable that will be used by the bot to
    handle a particular URL in an IRC message.

    .. seealso::

        Both :func:`sopel.plugin.url` :func:`sopel.plugin.url_lazy` make the
        decorated function a URL callback handler.

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


def clean_module(module, config):
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
    """
    callables = []
    shutdowns = []
    jobs = []
    urls = []
    for obj in itervalues(vars(module)):
        if callable(obj):
            is_sopel_callable = getattr(obj, '_sopel_callable', False) is True
            if getattr(obj, '__name__', None) == 'shutdown':
                shutdowns.append(obj)
            elif not is_sopel_callable:
                continue
            elif is_triggerable(obj):
                clean_callable(obj, config)
                callables.append(obj)
            elif hasattr(obj, 'interval'):
                clean_callable(obj, config)
                jobs.append(obj)
            elif is_url_callback(obj):
                clean_callable(obj, config)
                urls.append(obj)
    return callables, jobs, shutdowns, urls
