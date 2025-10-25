"""Deprecation module for Sopel developers and plugin authors.

.. versionadded:: 8.0

    Previously in :mod:`sopel.tools`, the :func:`deprecated` function has been
    moved to this newly created module, as it can be used in every part of the
    Sopel codebase, including :mod:`sopel.tools` itself.

"""
from __future__ import annotations

import functools
import inspect
import logging
import traceback
from typing import Callable

from packaging.version import parse as parse_version

from sopel import __version__


def deprecated(
    reason: str | Callable | None = None,
    version: str | None = None,
    removed_in: str | None = None,
    warning_in: str | None = None,
    stack_frame: int = -1,
    stack_output: bool = True,
    func: Callable | None = None,
) -> Callable:
    """Decorator to mark deprecated functions in Sopel's API

    :param reason: optional text added to the deprecation warning
    :param version: optional version number when the decorated function
                    is deprecated
    :param removed_in: optional version number when the deprecated function
                       will be removed
    :param warning_in: optional version number when the decorated function
                       should start emitting a warning when called
    :param stack_frame: optional stack frame to output; defaults to ``-1``;
                        should almost always be negative
    :param stack_output: outputs the referenced stack frame as part of the
                         deprecation warning if ``True``; defaults to ``True``
    :param func: deprecated function
    :return: a callable that depends on how the decorator is called; either the
             decorated function, or a decorator with the appropriate parameters

    Any time the decorated ``func`` is called, a deprecation warning will be
    logged, with the last frame of the traceback. The optional ``warning_in``
    argument suppresses the warning on Sopel versions older than that, allowing
    for multi-stage deprecation timelines.

    The decorator can be used with or without arguments::

        from sopel.lifecycle import deprecated

        @deprecated
        def func1():
            print('func 1')

        @deprecated()
        def func2():
            print('func 2')

        @deprecated(reason='obsolete', version='7.0', removed_in='8.0')
        def func3():
            print('func 3')

    which will output the following in a console::

        >>> func1()
        Deprecated: func1
        File "<stdin>", line 1, in <module>
        func 1
        >>> func2()
        Deprecated: func2
        File "<stdin>", line 1, in <module>
        func 2
        >>> func3()
        Deprecated since 7.0, will be removed in 8.0: obsolete
        File "<stdin>", line 1, in <module>
        func 3

    The ``stack_frame`` argument can be used to choose which stack frame is used
    to generate hints in the warning text. By default, the most recent stack
    frame (the last entry in the list, ``-1``) is used, corresponding to where
    the decorated function itself was called. However, in certain cases such as
    deprecating conditional behavior within an object constructor, it can be
    useful to show a less recent stack frame instead.

    Setting ``stack_output`` to ``False`` will disable the stack frame output.
    This makes the warning easier to read in cases where the stack trace is not
    useful, such as deprecations not related to a specific function call.

    .. note::

        This decorator can be also used on callables that are not functions,
        such as classes and callable objects.

    .. versionadded:: 7.0
        Parameters ``reason``, ``version``, and ``removed_in``.

    .. versionadded:: 7.1
        The ``warning_in`` and ``stack_frame`` parameters.

    .. versionchanged:: 8.0
        Moved out of :mod:`sopel.tools` to resolve circular dependency issues.

    .. versionchanged:: 8.1
        Added ``None`` as a valid ``stack_frame`` value to disable its output.

    """
    if not any([reason, version, removed_in, warning_in, func]):
        # common usage: @deprecated()
        return deprecated

    if callable(reason):
        # common usage: @deprecated
        return deprecated(func=reason)

    if func is None:
        # common usage: @deprecated(message, version, removed_in)
        def decorator(func):
            return deprecated(
                reason, version, removed_in, warning_in,
                stack_frame, stack_output, func,
            )
        return decorator

    # now, we have everything we need to have:
    # - message is not a callable (could be None)
    # - func is not None
    # - version and removed_in can be None but that's OK
    # so now we can return the actual decorated function

    message = reason or getattr(func, '__name__', '<anonymous-function>')

    template = 'Deprecated: {message}'
    if version and removed_in:
        template = (
            'Deprecated since {version}, '
            'will be removed in {removed_in}: '
            '{message}')
    elif version:
        template = 'Deprecated since {version}: {message}'
    elif removed_in:
        template = 'Deprecated, will be removed in {removed_in}: {message}'

    text = template.format(
        message=message, version=version, removed_in=removed_in)

    @functools.wraps(func)
    def deprecated_func(*args, **kwargs):
        warn_ver = warning_in and parse_version(warning_in).release
        this_ver = parse_version(__version__).release

        if not (warn_ver and warn_ver >= this_ver):
            original_frame = inspect.stack()[-stack_frame]
            mod = inspect.getmodule(original_frame[0])
            module_name = None
            if mod:
                module_name = mod.__name__
            if module_name:
                if module_name.startswith('sopel.'):
                    # core, or core plugin
                    logger = logging.getLogger(module_name)
                else:
                    # probably a plugin; try to handle most cases sanely
                    if module_name.startswith('sopel_modules.'):
                        # namespace package plugins have a prefix, obviously
                        # they will use Sopel's namespace; other won't
                        module_name = module_name.replace(
                            'sopel_modules.',
                            'sopel.externals.',
                            1,
                        )
                    logger = logging.getLogger(module_name)
            else:
                # don't know the module/plugin name, but we want to make sure
                # the log line is still output, so just get *something*
                logger = logging.getLogger(__name__)

            # Format only the desired stack frame, if enabled
            trace_frame = ""
            if stack_output:
                trace = traceback.extract_stack()
                trace_frame = (
                    # include the newline here, so the warning() below won't
                    # print a useless blank line unless trace_frame is wanted
                    "\n" + traceback.format_list(trace[:-1])[stack_frame][:-1]
                )

            # Warn the user
            logger.warning(text + trace_frame)

        return func(*args, **kwargs)

    return deprecated_func
