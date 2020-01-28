# coding=utf-8
"""This contains decorators and other tools for creating Sopel plugins."""
# Copyright 2013, Ari Koivula, <ari@koivu.la>
# Copyright © 2013, Elad Alfassa <elad@fedoraproject.org>
# Copyright 2013, Lior Ramati <firerogue517@gmail.com>
# Copyright 2019, deathbybandaid, deathbybandaid.net
# Copyright 2019, dgw, technobabbl.es
# Copyright 2019, Florian Strzelecki <florian.strzelecki@gmail.com>
# Licensed under the Eiffel Forum License 2.

from __future__ import unicode_literals, absolute_import, print_function, division

import functools
import re

__all__ = [
    # constants
    'NOLIMIT', 'VOICE', 'HALFOP', 'OP', 'ADMIN', 'OWNER', 'OPER',
    # decorators
    'action_commands',
    'commands',
    'echo',
    'event',
    'example',
    'intent',
    'interval',
    'nickname_commands',
    'output_prefix',
    'priority',
    'rate',
    'require_account',
    'require_admin',
    'require_chanmsg',
    'require_owner',
    'require_privilege',
    'require_privmsg',
    'rule',
    'thread',
    'unblockable',
    'url',
]


NOLIMIT = 1
"""Return value for ``callable``\\s, which suppresses rate limiting.

Returning this value means the triggering user will not be prevented from
triggering the same callable again within the rate limit. This can be used,
for example, to allow a user to retry a failed command immediately.

.. versionadded:: 4.0
"""

VOICE = 1
"""Privilege level for the +v channel permission

.. versionadded:: 4.1
"""

HALFOP = 2
"""Privilege level for the +h channel permission

.. versionadded:: 4.1
"""

OP = 4
"""Privilege level for the +o channel permission

.. versionadded:: 4.1
"""

ADMIN = 8
"""Privilege level for the +a channel permission

.. versionadded:: 4.1
"""

OWNER = 16
"""Privilege level for the +q channel permission

.. versionadded:: 4.1
"""

OPER = 32
"""Privilege level for the +y/+Y channel permissions

Note: Except for these (non-standard) channel modes, Sopel does not monitor or
store any user's OPER status.

.. versionadded:: 7.0.0
"""


def unblockable(function):
    """Decorate a function to exempt it from the ignore/blocks system.

    For example, this can be used to ensure that important events such as
    ``JOIN`` are always recorded::

        from sopel import module

        @module.event('JOIN')
        @module.unblockable
        def on_join_callable(bot, trigger):
            # do something when a user JOIN a channel
            # a blocked nickname or hostname *will* trigger this
            pass

    .. seealso::

        Sopel's :meth:`~sopel.bot.Sopel.dispatch` and
        :meth:`~sopel.bot.Sopel.get_triggered_callables` methods.

    """
    function.unblockable = True
    return function


def interval(*intervals):
    """Decorate a function to be called by the bot every *n* seconds.

    :param int intervals: one or more duration(s), in seconds

    This decorator can be used multiple times for multiple intervals, or
    multiple intervals can be given in multiple arguments. The first time the
    function will be called is *n* seconds after the bot was started.

    Plugin functions decorated by ``interval`` must only take
    :class:`bot <sopel.bot.Sopel>` as their argument; they do not get a ``trigger``.
    The ``bot`` argument will not have a context, so functions like
    ``bot.say()`` will not have a default destination.

    There is no guarantee that the bot is connected to a server or in any
    channels when the function is called, so care must be taken.

    Example::

        from sopel import module

        @module.interval(5)
        def spam_every_5s(bot):
            if "#here" in bot.channels:
                bot.say("It has been five seconds!", "#here")

    """
    def add_attribute(function):
        if not hasattr(function, "interval"):
            function.interval = []
        for arg in intervals:
            if arg not in function.interval:
                function.interval.append(arg)
        return function

    return add_attribute


def rule(*patterns):
    """Decorate a function to be called when a line matches the given pattern.

    :param str patterns: one or more regular expression(s)

    Each argument is a regular expression which will trigger the function.

    This decorator can be used multiple times to add more rules.

    If the Sopel instance is in a channel, or sent a PRIVMSG, where a string
    matching this expression is said, the function will execute. Note that
    captured groups here will be retrievable through the Trigger object later.

    Inside the regular expression, some special directives can be used. $nick
    will be replaced with the nick of the bot and , or :, and $nickname will be
    replaced with the nick of the bot.

    .. versionchanged:: 7.0

        The :func:`rule` decorator can be called with multiple positional
        arguments, each used to add a rule. This is equivalent to decorating
        the same function multiple times with this decorator.

    .. note::

        A regex rule can match only once per line. A future version of Sopel
        will (hopefully) remove this limitation.

    .. note::

        The regex match must start at the beginning of the line. To match
        anywhere in a line, surround the actual pattern with ``.*``. A future
        version of Sopel may remove this requirement.

    """
    def add_attribute(function):
        if not hasattr(function, "rule"):
            function.rule = []
        for value in patterns:
            if value not in function.rule:
                function.rule.append(value)
        return function

    return add_attribute


def thread(value):
    """Decorate a function to specify if it should be run in a separate thread.

    :param bool value: if ``True``, the function is called in a separate thread;
                       otherwise, from the bot's main thread

    Functions run in a separate thread (as is the default) will not prevent the
    bot from executing other functions at the same time. Functions not run in a
    separate thread may be started while other functions are still running, but
    additional functions will not start until it is completed.
    """
    threaded = bool(value)

    def add_attribute(function):
        function.thread = threaded
        return function

    return add_attribute


def echo(function=None):
    """Decorate a function to specify that it should receive echo messages.

    This decorator can be used to listen in on the messages that Sopel is
    sending and react accordingly.
    """
    def add_attribute(function):
        function.echo = True
        return function

    # hack to allow both @echo and @echo() to work
    if callable(function):
        return add_attribute(function)
    return add_attribute


def commands(*command_list):
    """Decorate a function to set one or more commands that should trigger it.

    :param str command_list: one or more command name(s) to match
                             (can be regular expressions)

    This decorator can be used to add multiple commands to one callable in a
    single line. The resulting match object will have the command as the first
    group; the rest of the line, excluding leading whitespace, as the second
    group; and parameters 1 through 4, separated by whitespace, as groups 3-6.

    Example::

        @commands("hello")
            # If the command prefix is "\\.", this would trigger on lines
            # starting with ".hello".

        @commands('j', 'join')
            # If the command prefix is "\\.", this would trigger on lines
            # starting with either ".j" or ".join".

    """
    def add_attribute(function):
        if not hasattr(function, "commands"):
            function.commands = []
        for command in command_list:
            if command not in function.commands:
                function.commands.append(command)
        return function
    return add_attribute


def nickname_commands(*command_list):
    """Decorate a function to trigger on lines starting with "$nickname: command".

    :param str command_list: one or more command name(s) to match
                             (can be regular expressions)

    This decorator can be used to add multiple commands to one callable in a
    single line. The resulting match object will have the command as the first
    group; the rest of the line, excluding leading whitespace, as the second
    group; and parameters 1 through 4, separated by whitespace, as groups 3-6.

    Example::

        @nickname_commands("hello!")
            # Would trigger on "$nickname: hello!", "$nickname,   hello!",
            # "$nickname hello!", "$nickname hello! parameter1" and
            # "$nickname hello! p1 p2 p3 p4 p5 p6 p7 p8 p9".

        @nickname_commands(".*")
            # Would trigger on anything starting with "$nickname[:,]? ",
            # and would never have any additional parameters, as the
            # command would match the rest of the line.

    """
    def add_attribute(function):
        if not hasattr(function, 'nickname_commands'):
            function.nickname_commands = []
        for cmd in command_list:
            if cmd not in function.nickname_commands:
                function.nickname_commands.append(cmd)
        return function
    return add_attribute


def action_commands(*command_list):
    """Decorate a function to trigger on CTCP ACTION lines.

    :param str command_list: one or more command name(s) to match
                             (can be regular expressions)

    This decorator can be used to add multiple commands to one callable in a
    single line. The resulting match object will have the command as the first
    group; the rest of the line, excluding leading whitespace, as the second
    group; and parameters 1 through 4, separated by whitespace, as groups 3-6.

    Example::

        @action_commands("hello!")
            # Would trigger on "/me hello!"

    .. versionadded:: 7.0

    .. important::

        This decorator will prevent the other command types from working on
        the same callable. Normally only one command type is used per
        function, but if you need to trigger the same command with e.g. both
        action and nickname commands, use a main function called from
        decorated wrappers.

        Hopefully, a future version of Sopel will remove this limitation.

    """
    def add_attribute(function):
        function.intents = ['ACTION']
        if not hasattr(function, 'action_commands'):
            function.action_commands = []
        for cmd in command_list:
            if cmd not in function.action_commands:
                function.action_commands.append(cmd)
        return function
    return add_attribute


def priority(value):
    """Decorate a function to be executed with higher or lower priority.

    :param str value: one of ``high``, ``medium``, or ``low``;
                      defaults to ``medium``

    The priority allows you to control the order of callable execution, if your
    plugin needs it.
    """
    def add_attribute(function):
        function.priority = value
        return function
    return add_attribute


def event(*event_list):
    """Decorate a function to be triggered on specific IRC events.

    :param str event_list: one or more event name(s) on which to trigger

    This is one of a number of events, such as 'JOIN', 'PART', 'QUIT', etc.
    (More details can be found in RFC 1459.) When the Sopel bot is sent one of
    these events, the function will execute. Note that the default
    :meth:`rule` (``.*``) will match *any* line of the correct event type(s).
    If any rule is explicitly specified, it overrides the default.

    .. seealso::

        :class:`sopel.tools.events` provides human-readable names for many of the
        numeric events, which may help your code be clearer.

    """
    def add_attribute(function):
        if not hasattr(function, "event"):
            function.event = []
        for name in event_list:
            if name not in function.event:
                function.event.append(name)
        return function
    return add_attribute


def intent(*intent_list):
    """Decorate a callable to trigger on a message with any of the given intents.

    :param str intent_list: one or more intent(s) on which to trigger (really,
                            the only useful value is ``action``)

    .. versionadded:: 5.2.0

    .. note::

        This system will be replaced and marked deprecated in or before Sopel
        8.0, then removed in Sopel 9.0, as the IRCv3 spec for intents is dead.

    """
    def add_attribute(function):
        if not hasattr(function, "intents"):
            function.intents = []
        for name in intent_list:
            if name not in function.intents:
                function.intents.append(name)
        return function
    return add_attribute


def rate(user=0, channel=0, server=0):
    """Decorate a function to be rate-limited.

    :param int user: seconds between permitted calls of this function by the
                     same user
    :param int channel: seconds between permitted calls of this function in
                        the same channel, regardless of triggering user
    :param int server: seconds between permitted calls of this function no
                       matter who triggered it or where

    How often a function can be triggered on a per-user basis, in a channel,
    or across the server (bot) can be controlled with this decorator. A value
    of ``0`` means no limit. If a function is given a rate of 20, that
    function may only be used once every 20 seconds in the scope corresponding
    to the parameter. Users on the admin list in Sopel’s configuration are
    exempted from rate limits.

    Rate-limited functions that use scheduled future commands should import
    :class:`threading.Timer` instead of :mod:`sched`, or rate limiting will
    not work properly.
    """
    def add_attribute(function):
        function.rate = user
        function.channel_rate = channel
        function.global_rate = server
        return function
    return add_attribute


def require_privmsg(message=None, reply=False):
    """Decorate a function to only be triggerable from a private message.

    :param str message: optional message said if triggered in a channel
    :param bool reply: use :meth:`~sopel.bot.Sopel.reply` instead of
                       :meth:`~sopel.bot.Sopel.say` when ``True``; defaults to
                       ``False``

    If the decorated function is triggered by a channel message, ``message``
    will be said if given. By default, it uses :meth:`bot.say()
    <.bot.Sopel.say>`, but when ``reply`` is true, then it uses
    :meth:`bot.reply() <.bot.Sopel.reply>` instead.

    .. versionchanged:: 7.0
        Added the ``reply`` parameter.
    """
    def actual_decorator(function):
        @functools.wraps(function)
        def guarded(bot, trigger, *args, **kwargs):
            if trigger.is_privmsg:
                return function(bot, trigger, *args, **kwargs)
            else:
                if message and not callable(message):
                    if reply:
                        bot.reply(message)
                    else:
                        bot.say(message)
        return guarded

    # Hack to allow decorator without parens
    if callable(message):
        return actual_decorator(message)
    return actual_decorator


def require_chanmsg(message=None, reply=False):
    """Decorate a function to only be triggerable from a channel message.

    :param str message: optional message said if triggered in private message
    :param bool reply: use :meth:`~.bot.Sopel.reply` instead of
                       :meth:`~.bot.Sopel.say` when ``True``; defaults to
                       ``False``

    If the decorated function is triggered by a private message, ``message``
    will be said if given. By default, it uses :meth:`bot.say()
    <.bot.Sopel.say>`, but when ``reply`` is true, then it uses
    :meth:`bot.reply() <.bot.Sopel.reply>` instead.

    .. versionchanged:: 7.0
        Added the ``reply`` parameter.
    """
    def actual_decorator(function):
        @functools.wraps(function)
        def guarded(bot, trigger, *args, **kwargs):
            if not trigger.is_privmsg:
                return function(bot, trigger, *args, **kwargs)
            else:
                if message and not callable(message):
                    if reply:
                        bot.reply(message)
                    else:
                        bot.say(message)
        return guarded

    # Hack to allow decorator without parens
    if callable(message):
        return actual_decorator(message)
    return actual_decorator


def require_account(message=None, reply=False):  # lgtm [py/similar-function]
    """Decorate a function to require services/NickServ authentication.

    :param str message: optional message to say if a user without
                        authentication tries to trigger this function
    :param bool reply: use :meth:`~.bot.Sopel.reply` instead of
                       :meth:`~.bot.Sopel.say` when ``True``; defaults to
                       ``False``

    .. versionadded:: 7.0
    .. note::

        Only some networks support services authentication, and not all of
        those implement the standards required for clients like Sopel to
        determine authentication status. This decorator will block *all* use
        of functions it decorates on networks that lack the relevant features.

    .. seealso::

        The value of the :class:`trigger<.trigger.Trigger>`'s
        :attr:`account <.trigger.Trigger.account>` property determines whether
        this requirement is satisfied, and the property's documentation
        includes up-to-date details on what features a network must
        support to allow Sopel to fetch account information.

    """
    def actual_decorator(function):
        @functools.wraps(function)
        def guarded(bot, trigger, *args, **kwargs):
            if not trigger.account:
                if message and not callable(message):
                    if reply:
                        bot.reply(message)
                    else:
                        bot.say(message)
            else:
                return function(bot, trigger, *args, **kwargs)
        return guarded

    # Hack to allow decorator without parens
    if callable(message):
        return actual_decorator(message)

    return actual_decorator


def require_privilege(level, message=None, reply=False):
    """Decorate a function to require at least the given channel permission.

    :param int level: required privilege level to use this command
    :param str message: optional message said to insufficiently privileged user
    :param bool reply: use :meth:`~.bot.Sopel.reply` instead of
                       :meth:`~.bot.Sopel.say` when ``True``; defaults to
                       ``False``

    ``level`` can be one of the privilege level constants defined in this
    module. If the user does not have the privilege, the bot will say
    ``message`` if given. By default, it uses :meth:`bot.say()
    <.bot.Sopel.say>`, but when ``reply`` is true, then it uses
    :meth:`bot.reply() <.bot.Sopel.reply>` instead.

    Privilege requirements are ignored in private messages.

    .. versionchanged:: 7.0
        Added the ``reply`` parameter.
    """
    def actual_decorator(function):
        @functools.wraps(function)
        def guarded(bot, trigger, *args, **kwargs):
            # If this is a privmsg, ignore privilege requirements
            if trigger.is_privmsg:
                return function(bot, trigger, *args, **kwargs)
            channel_privs = bot.channels[trigger.sender].privileges
            allowed = channel_privs.get(trigger.nick, 0) >= level
            if not trigger.is_privmsg and not allowed:
                if message and not callable(message):
                    if reply:
                        bot.reply(message)
                    else:
                        bot.say(message)
            else:
                return function(bot, trigger, *args, **kwargs)
        return guarded
    return actual_decorator


def require_admin(message=None, reply=False):  # lgtm [py/similar-function]
    """Decorate a function to require the triggering user to be a bot admin.

    :param str message: optional message said to non-admin user
    :param bool reply: use :meth:`~.bot.Sopel.reply` instead of
                       :meth:`~.bot.Sopel.say` when ``True``; defaults to
                       ``False``

    When the triggering user is not an admin, the command is not run, and the
    bot will say the ``message`` if given. By default, it uses
    :meth:`bot.say() <.bot.Sopel.say>`, but when ``reply`` is true, then it
    uses :meth:`bot.reply() <.bot.Sopel.reply>` instead.

    .. versionchanged:: 7.0
        Added the ``reply`` parameter.
    """
    def actual_decorator(function):
        @functools.wraps(function)
        def guarded(bot, trigger, *args, **kwargs):
            if not trigger.admin:
                if message and not callable(message):
                    if reply:
                        bot.reply(message)
                    else:
                        bot.say(message)
            else:
                return function(bot, trigger, *args, **kwargs)
        return guarded

    # Hack to allow decorator without parens
    if callable(message):
        return actual_decorator(message)

    return actual_decorator


def require_owner(message=None, reply=False):  # lgtm [py/similar-function]
    """Decorate a function to require the triggering user to be the bot owner.

    :param str message: optional message said to non-owner user
    :param bool reply: use :meth:`~.bot.Sopel.reply` instead of
                       :meth:`~.bot.Sopel.say` when ``True``; defaults to
                       ``False``

    When the triggering user is not the bot's owner, the command is not run,
    and the bot will say ``message`` if given. By default, it uses
    :meth:`bot.say() <.bot.Sopel.say>`, but when ``reply`` is true, then it
    uses :meth:`bot.reply() <.bot.Sopel.reply>` instead.

    .. versionchanged:: 7.0
        Added the ``reply`` parameter.
    """
    def actual_decorator(function):
        @functools.wraps(function)
        def guarded(bot, trigger, *args, **kwargs):
            if not trigger.owner:
                if message and not callable(message):
                    if reply:
                        bot.reply(message)
                    else:
                        bot.say(message)
            else:
                return function(bot, trigger, *args, **kwargs)
        return guarded

    # Hack to allow decorator without parens
    if callable(message):
        return actual_decorator(message)
    return actual_decorator


def url(*url_rules):
    """Decorate a function to handle URLs.

    :param str url_rules: one or more regex pattern(s) to match URLs

    This decorator takes a regex string that will be matched against URLs in a
    message. The function it decorates, in addition to the bot and trigger,
    must take a third argument ``match``, which is the regular expression match
    of the URL::

        from sopel import module

        @module.url(r'https://example.com/bugs/([a-z0-9]+)')
        @module.url(r'https://short.com/([a-z0-9]+)')
        def handle_example_bugs(bot, trigger, match):
            bot.reply('Found bug ID #%s' % match.group(1))

    This should be used rather than the matching in ``trigger``, in order to
    support e.g. the ``.title`` command.

    Under the hood, when Sopel collects the decorated handler it uses
    :meth:`sopel.bot.Sopel.register_url_callback` to register the handler.

    .. versionchanged:: 7.0

        The same function can be decorated multiple times with :func:`url`
        to register different URL patterns.

    .. versionchanged:: 7.0

        More than one pattern can be provided as positional argument at once.

    .. seealso::

        To detect URLs, Sopel uses a matching pattern built from a list of URL
        schemes, configured by
        :attr:`~sopel.config.core_section.CoreSection.auto_url_schemes`.

    """
    def actual_decorator(function):
        if not hasattr(function, 'url_regex'):
            function.url_regex = []
        for url_rule in url_rules:
            url_regex = re.compile(url_rule)
            if url_regex not in function.url_regex:
                function.url_regex.append(url_regex)
        return function
    return actual_decorator


class example(object):
    """Decorate a function with an example, and optionally test output.

    :param str msg: the example command (required; see below)
    :param str result: the command's expected output (optional; see below)
    :param bool privmsg: if ``True``, the example will be tested as if it was
                         received in a private message to the bot; otherwise,
                         in a channel (optional; default ``False``)
    :param bool admin: whether to treat the test message as having come from a
                       bot admin (optional; default ``False``)
    :param bool owner: whether to treat the test message as having come from
                       the bot's owner (optional; default ``False``)
    :param int repeat: how many times to repeat the test; useful for commands
                       that return random results (optional; default ``1``)
    :param bool re: if ``True``, the ``result`` is interpreted as a regular
                    expression and used to match the command's output
                    (optional; see below)
    :param list ignore: :class:`list` of regular expression patterns to match
                        ignored output (optional; see below)
    :param bool user_help: whether this example should be included in
                           user-facing help output such as `.help command`
                           (optional; default ``False``; see below)
    :param bool online: if ``True``, |pytest|_ will mark this
                        example as "online" (optional; default ``False``; see
                        below)

    .. |pytest| replace:: ``pytest``
    .. _pytest: https://pypi.org/project/pytest/

    For compatibility with the built-in help plugin, ``msg`` must use the
    default :attr:`~sopel.config.core_section.CoreSection.help_prefix` if it
    is a prefixed command. Other command types should give example invocations
    that work with Sopel's default settings, especially if using the "example
    test" functionality to automatically generate a test(s) for the function.

    The presence of a ``result`` will generate tests automatically when Sopel's
    test suite is run, using ``msg`` as input. The exact behavior of the tests
    depends on the remaining optional ``example`` arguments.

    Passing ``re=True``, in particular, is useful for matching ``result``\\s
    that are random and/or dependent on an external API. This way, an example
    test can check the format of the result without caring about the exact data.

    Giving a list of ``ignore``d patterns is helpful for commands that may
    return intermittent errors (mostly calls to an external API that isn't
    necessarily stable), especially when coupled with the ``repeat`` parameter.

    By default, Sopel's help plugin will display only one example (the one
    closest to the function's `def` statement, due to how decorators work). You
    can override this choice or include multiple examples by passing
    ``user_help=True`` to one or more ``example`` decorator(s).

    Finally, passing ``online=True`` makes that particular example skippable if
    Sopel's test suite is run in offline mode, which is mostly useful to make
    life easier for other developers working on Sopel without Internet access.
    """
    def __init__(self, msg, result=None, privmsg=False, admin=False,
                 owner=False, repeat=1, re=False, ignore=None,
                 user_help=False, online=False):
        # Wrap result into a list for get_example_test
        if isinstance(result, list):
            self.result = result
        elif result is not None:
            self.result = [result]
        else:
            self.result = None
        self.use_re = re
        self.msg = msg
        self.privmsg = privmsg
        self.admin = admin
        self.owner = owner
        self.repeat = repeat
        self.online = online

        if isinstance(ignore, list):
            self.ignore = ignore
        elif ignore is not None:
            self.ignore = [ignore]
        else:
            self.ignore = []

        self.user_help = user_help

    def __call__(self, func):
        if not hasattr(func, "example"):
            func.example = []

        import sys

        import sopel.test_tools  # TODO: fix circular import with sopel.bot and sopel.test_tools

        # only inject test-related stuff if we're running tests
        # see https://stackoverflow.com/a/44595269/5991
        if 'pytest' in sys.modules and self.result:
            # avoids doing `import pytest` and causing errors when
            # dev-dependencies aren't installed
            pytest = sys.modules['pytest']

            test = sopel.test_tools.get_example_test(
                func, self.msg, self.result, self.privmsg, self.admin,
                self.owner, self.repeat, self.use_re, self.ignore
            )

            if self.online:
                test = pytest.mark.online(test)

            sopel.test_tools.insert_into_module(
                test, func.__module__, func.__name__, 'test_example'
            )
            sopel.test_tools.insert_into_module(
                sopel.test_tools.get_disable_setup(), func.__module__, func.__name__, 'disable_setup'
            )

        record = {
            "example": self.msg,
            "result": self.result,
            "privmsg": self.privmsg,
            "admin": self.admin,
            "help": self.user_help,
        }
        func.example.append(record)
        return func


def output_prefix(prefix):
    """Decorate a function to add a prefix on its output.

    :param str prefix: the prefix to add (must include trailing whitespace if
                       desired; Sopel does not assume it should add anything)

    Prefix will be added to text sent through:

    * :meth:`bot.say <sopel.bot.SopelWrapper.say>`
    * :meth:`bot.notice <sopel.bot.SopelWrapper.notice>`

    """
    def add_attribute(function):
        function.output_prefix = prefix
        return function
    return add_attribute
