# -*- coding: utf-8 -*-
"""This module is meant to be imported from willie modules.

It defines the following decorators for defining willie callables:
willie.module.rule
willie.module.thread
willie.module.name (deprecated)
willie.module.commands
willie.module.priority
willie.module.event
willie.module.rate
"""
"""
willie/module.py - Willie IRC Bot (http://willie.dftba.net/)
Copyright 2013, Ari Koivula, <ari@koivu.la>

Licensed under the Eiffel Forum License 2.
"""


def rule(value):
    """Decorator rule(value). Equivalent to func.rule = value.

    Args:
        value: A regular expression which will trigger the function.

    If the Willie instance is in a channel, or sent a PRIVMSG, where a string
    matching this expression is said, the function will execute. Note that
    captured groups here will be retrievable through the Trigger object later.

    Inside the regular expression, some special directives can be used. $nick
    will be replaced with the nick of the bot and , or :, and $nickname will be
    replaced with the nick of the bot.

    Prior to 3.1, rules could also be made one of three formats of tuple. The
    values would be joined together to form a singular regular expression.
    However, these kinds of rules add no functionality over simple regular
    expressions, and are considered deprecated in 3.1.
    """
    def add_attribute(function):
        function.rule = value
        return function

    if isinstance(value, tuple):
        raise DeprecationWarning("Tuple-form .rule is deprecated in 3.1."
                                 " Replace tuple-form .rule with a regexp.")

    return add_attribute


def thread(value):
    """Decorator thread(value). Equivalent to func.thread = value.

    Args:
        value: Either True or False. If True the function is called in
            a separate thread. If False from the main thread.
    """
    def add_attribute(function):
        function.thread = value
        return function
    return add_attribute


def name(value):
    """Decorator name(value). Equivalent to func.name = value.

    This attribute is considered deprecated in 3.1.
    """
    raise DeprecationWarning("This attribute is considered deprecated in 3.1."
                             " Replace tuple-form .rule with a regexp.")


def commands(value):
    """Decorator commands(value). Equivalent to func.commands = value.

    Args:
        value: A list of commands which will trigger the function.

    If the Willie instance is in a channel, or sent a PRIVMSG, where one of
    these strings is said, preceded only by the configured prefix (a period, by
    default), the function will execute.
    """
    def add_attribute(function):
        function.commands = value
        return function
    return add_attribute


def priority(value):
    """Decorator priority(value). Equivalent to func.priority = value.

    Args:
        value: Priority can be one of "high", "medium", "low". Defaults to
            medium.

    Priority allows you to control the order of callable execution, if your
    module needs it.
    """
    def add_attribute(function):
        function.priority = value
        return function
    return add_attribute


def event(value):
    """Decorator event(value). Equivalent to func.event = value.

    This is one of a number of events, such as 'JOIN', 'PART', 'QUIT', etc.
    (More details can be found in RFC 1459.) When the Willie bot is sent one of
    these events, the function will execute. Note that functions with an event
    must also be given a rule to match (though it may be '.*', which will
    always match) or they will not be triggered.
    """
    def add_attribute(function):
        function.event = value
        return function
    return add_attribute


def rate(value):
    """Decorator rate(value). Equivalent to func.rate = value.

    Availability: 2+

    This limits the frequency with which a single user may use the function. If
    a function is given a rate of 20, a single user may only use that function
    once every 20 seconds. This limit applies to each user individually. Users
    on the admin list in Willie’s configuration are exempted from rate limits.
    """
    def add_attribute(function):
        function.rate = value
        return function
    return add_attribute
