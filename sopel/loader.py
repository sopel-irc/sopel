# coding=utf-8
from __future__ import unicode_literals, absolute_import, print_function, division

import imp
import os.path
import re
import sys

from sopel.tools import compile_rule, itervalues, get_command_regexp, get_nickname_command_regexp
from sopel.config import core_section

default_prefix = core_section.CoreSection.help_prefix.default
del core_section

if sys.version_info.major >= 3:
    basestring = (str, bytes)


def get_module_description(path):
    good_file = (os.path.isfile(path) and
                 path.endswith('.py') and not path.startswith('_'))
    good_dir = (os.path.isdir(path) and
                os.path.isfile(os.path.join(path, '__init__.py')))
    if good_file:
        name = os.path.basename(path)[:-3]
        return (name, path, imp.PY_SOURCE)
    elif good_dir:
        name = os.path.basename(path)
        return (name, path, imp.PKG_DIRECTORY)
    else:
        return None


def _update_modules_from_dir(modules, directory):
    # Note that this modifies modules in place
    for path in os.listdir(directory):
        path = os.path.join(directory, path)
        result = get_module_description(path)
        if result:
            modules[result[0]] = result[1:]


def enumerate_modules(config, show_all=False):
    """Map the names of modules to the location of their file.

    Return a dict mapping the names of modules to a tuple of the module name,
    the pathname and either `imp.PY_SOURCE` or `imp.PKG_DIRECTORY`. This
    searches the regular modules directory and all directories specified in the
    `core.extra` attribute of the `config` object. If two modules have the same
    name, the last one to be found will be returned and the rest will be
    ignored. Modules are found starting in the regular directory, followed by
    `~/.sopel/modules`, and then through the extra directories in the order
    that the are specified.

    If `show_all` is given as `True`, the `enable` and `exclude`
    configuration options will be ignored, and all modules will be shown
    (though duplicates will still be ignored as above).
    """
    modules = {}

    # First, add modules from the regular modules directory
    main_dir = os.path.dirname(os.path.abspath(__file__))
    modules_dir = os.path.join(main_dir, 'modules')
    _update_modules_from_dir(modules, modules_dir)
    for path in os.listdir(modules_dir):
        break

    # Then, find PyPI installed modules
    # TODO does this work with all possible install mechanisms?
    try:
        import sopel_modules
    except Exception:  # TODO: Be specific
        pass
    else:
        for directory in sopel_modules.__path__:
            _update_modules_from_dir(modules, directory)

    # Next, look in ~/.sopel/modules
    home_modules_dir = os.path.join(config.homedir, 'modules')
    if not os.path.isdir(home_modules_dir):
        os.makedirs(home_modules_dir)
    _update_modules_from_dir(modules, home_modules_dir)

    # Last, look at all the extra directories.
    for directory in config.core.extra:
        _update_modules_from_dir(modules, directory)

    # Coretasks is special. No custom user coretasks.
    ct_path = os.path.join(main_dir, 'coretasks.py')
    modules['coretasks'] = (ct_path, imp.PY_SOURCE)

    # If caller wants all of them, don't apply white and blacklists
    if show_all:
        return modules

    # Apply whitelist, if present
    enable = config.core.enable
    if enable:
        enabled_modules = {'coretasks': modules['coretasks']}
        for module in enable:
            if module in modules:
                enabled_modules[module] = modules[module]
        modules = enabled_modules

    # Apply blacklist, if present
    exclude = config.core.exclude
    for module in exclude:
        if module in modules:
            del modules[module]

    return modules


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
    example = None

    func.unblockable = getattr(func, 'unblockable', False)
    func.priority = getattr(func, 'priority', 'medium')
    func.thread = getattr(func, 'thread', True)
    func.rate = getattr(func, 'rate', 0)
    func.channel_rate = getattr(func, 'channel_rate', 0)
    func.global_rate = getattr(func, 'global_rate', 0)

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

    if hasattr(func, 'commands') or hasattr(func, 'nickname_commands'):
        func.rule = getattr(func, 'rule', [])
        for command in getattr(func, 'commands', []):
            regexp = get_command_regexp(prefix, command)
            func.rule.append(regexp)
        for command in getattr(func, 'nickname_commands', []):
            regexp = get_nickname_command_regexp(nick, command, alias_nicks)
            func.rule.append(regexp)
        if hasattr(func, 'example'):
            example = func.example[0]["example"]
            example = example.replace('$nickname', nick)
            if example[0] != help_prefix and not example.startswith(nick):
                example = example.replace(default_prefix, help_prefix, 1)
        if doc or example:
            cmds = []
            cmds.extend(getattr(func, 'commands', []))
            cmds.extend(getattr(func, 'nickname_commands', []))
            for command in cmds:
                func._docs[command] = (doc, example)

    if hasattr(func, 'intents'):
        func.intents = [re.compile(intent, re.IGNORECASE) for intent in func.intents]


def load_module(name, path, type_):
    """Load a module, and sort out the callables and shutdowns"""
    if type_ == imp.PY_SOURCE:
        with open(path) as mod:
            module = imp.load_module(name, mod, path, ('.py', 'U', type_))
    elif type_ == imp.PKG_DIRECTORY:
        module = imp.load_module(name, None, path, ('', '', type_))
    else:
        raise TypeError('Unsupported module type')
    return module, os.path.getmtime(path)


def is_triggerable(obj):
    return any(hasattr(obj, attr) for attr in ('rule', 'intents', 'commands', 'nickname_commands'))


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
                urls.append(obj)
    return callables, jobs, shutdowns, urls
