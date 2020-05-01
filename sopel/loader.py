# coding=utf-8
from __future__ import unicode_literals, absolute_import, print_function, division

import re
import sys

from sopel.tools import (compile_rule, itervalues, get_command_regexp,
                         get_nickname_command_regexp, get_action_command_regexp)
from sopel.config import core_section

default_prefix = core_section.CoreSection.help_prefix.default
del core_section

if sys.version_info.major >= 3:
    basestring = (str, bytes)


def trim_docstring(doc):
    """Get the docstring as a series of lines that can be sent"""
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
    """Compiles the regexes, moves commands into func.rule, fixes up docs and
    puts them in func._docs, and sets defaults"""
    nick = config.core.nick
    alias_nicks = config.core.alias_nicks
    prefix = config.core.prefix
    help_prefix = config.core.help_prefix
    func._docs = {}
    doc = trim_docstring(func.__doc__)
    examples = []

    func.thread = getattr(func, 'thread', True)

    if is_limitable(func):
        # These attributes are a waste of memory on callables that don't pass
        # through Sopel's rate-limiting machinery
        func.rate = getattr(func, 'rate', 0)
        func.channel_rate = getattr(func, 'channel_rate', 0)
        func.global_rate = getattr(func, 'global_rate', 0)
        func.unblockable = getattr(func, 'unblockable', False)

    if not is_triggerable(func):
        # Adding the remaining default attributes below is potentially confusing
        # to other code (and a waste of memory) for non-triggerable functions.
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

    if hasattr(func, 'rule'):
        if isinstance(func.rule, basestring):
            func.rule = [func.rule]
        func.rule = [compile_rule(nick, rule, alias_nicks) for rule in func.rule]

    if any(hasattr(func, attr) for attr in ['commands', 'nickname_commands', 'action_commands']):
        func.rule = getattr(func, 'rule', [])
        for command in getattr(func, 'commands', []):
            regexp = get_command_regexp(prefix, command)
            if regexp not in func.rule:
                func.rule.append(regexp)
        for command in getattr(func, 'nickname_commands', []):
            regexp = get_nickname_command_regexp(nick, command, alias_nicks)
            if regexp not in func.rule:
                func.rule.append(regexp)
        for command in getattr(func, 'action_commands', []):
            regexp = get_action_command_regexp(command)
            if regexp not in func.rule:
                func.rule.append(regexp)
        if hasattr(func, 'example'):
            # If no examples are flagged as user-facing, just show the first one like Sopel<7.0 did
            examples = [rec["example"] for rec in func.example if rec["help"]] or [func.example[0]["example"]]
            for i, example in enumerate(examples):
                example = example.replace('$nickname', nick)
                if example[0] != help_prefix and not example.startswith(nick):
                    example = example.replace(default_prefix, help_prefix, 1)
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
        'event',
        'intents',
        'commands',
        'nickname_commands',
        'action_commands',
        'url_regex',
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

        Many of the decorators defined in :mod:`sopel.module` make the
        decorated function a triggerable object.
    """
    forbidden_attrs = (
        'interval',
        'url_regex',
    )
    forbidden = any(hasattr(obj, attr) for attr in forbidden_attrs)

    allowed_attrs = (
        'rule',
        'event',
        'intents',
        'commands',
        'nickname_commands',
        'action_commands',
    )
    allowed = any(hasattr(obj, attr) for attr in allowed_attrs)

    return allowed and not forbidden


def clean_module(module, config):
    callables = []
    shutdowns = []
    jobs = []
    urls = []
    for obj in itervalues(vars(module)):
        if callable(obj):
            if getattr(obj, '__name__', None) == 'shutdown':
                shutdowns.append(obj)
            elif is_triggerable(obj):
                clean_callable(obj, config)
                callables.append(obj)
            elif hasattr(obj, 'interval'):
                clean_callable(obj, config)
                jobs.append(obj)
            elif hasattr(obj, 'url_regex'):
                clean_callable(obj, config)
                urls.append(obj)
    return callables, jobs, shutdowns, urls
