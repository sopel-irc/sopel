.. Willie IRC Bot documentation master file, created by
   sphinx-quickstart on Sat Jun 16 00:18:40 2012.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Introduction
============

This package contains a framework for an easily set-up, multi-purpose IRC bot.
The intent with this package is not that it be included with other packages,
but rather be run as a standalone program. However, it is intended (and
encouraged) that users write new "modules" for it. This documentation is
intended to serve that goal.

Due to the high level of customization encouraged by this bot, there are a few
different versions of it floating around. This documentation focuses on Willie,
but some parts may be applicable to older versions. The original "phenny" is,
for the purpose of this documentation, called version *1.x*, and the "jenni"
fork thereof considered version *2.x*. Willie versions start at *3.0* and
follow `semantic versioning <http://semver.org>`_.

.. contents:: :depth: 2

Getting started: Your functions, ``willie``, and ``trigger``
============================================================

At its most basic, writing a Willie module involves creating a Python file with
some number of functions in it. Each of these functions will be passed a 
``Willie`` object (``Phenny`` in *1.x* and ``Jenni`` in *2.x*) and a ``Trigger``
object (``CommandInput`` in *1.x* and *2.x*). By convention, these are named
``phenny`` and ``input`` in *1.x*, ``jenni`` and ``input`` in *2.x*, 
``willie`` and ``trigger`` in *3.x*, and ``bot`` and ``trigger`` from version
*4.0* onward. For the purposes of this guide, the *4.0* names will be used.

Your modules
------------

A Willie module contains one or more ``callable``\s. It may optionally contain
``configure``, ``setup``, and ``shutdown`` functions. ``callable``\s are given
a number of attributes, which determine when they will be executed. This is
done with decorators, imported from :py:mod:`willie.module`. It may also be
done by adding the attributes directly, at the same indentation level as the
function's ``def`` line, following the last line of the function; this is the
only option in versions prior to *4.0*.

.. py:method:: callable(bot, trigger)

    This is the general function format, called by Willie when a command is
    used, a rule is matched, or an event is seen, as determined by the
    attributes of the function. The details of what this function does are
    entirely up to the module writer - the only hard requirement from the bot
    is that it be callable with a ``Willie`` object and a ``Trigger`` object,
    as noted above. Usually, methods of the Willie object will be used in reply
    to the trigger, but this isn't a requirement.

    The return value of a callable will usually be ``None``. This doesn't need
    to be explicit; if the function has no ``return`` statement (or simply uses
    ``return`` with no arguments), ``None`` will be returned. In *3.2+*, the
    return value can be a constant; in prior versions return values were
    ignored. Returning a constant instructs the bot to perform some action
    after the ``callable``'s execution. For example, returning ``NOLIMIT`` will
    suspend rate limiting on that call. These constants are defined in
    :py:mod:`willie.module`, except in version *3.2* in which they are defined
    as attributes of the ``Willie`` class.

    Note that the name can, and should, be anything - it doesn't need to be
    called callable.

    .. py:attribute:: commands

        *See also:* :py:func:`willie.module.commands`

        A list of commands which will trigger the function. If the Willie instance
        is in a channel, or sent a PRIVMSG, where one of these strings is said,
        preceeded only by the configured prefix (a period, by default), the
        function will execute.

    .. py:attribute:: rule
    
        *See also:* :py:func:`willie.module.rule`

        A regular expression which will trigger the function. If the Willie
        instance is in a channel, or sent a PRIVMSG, where a string matching
        this expression is said, the function will execute. Note that captured
        groups here will be retrievable through the ``Trigger`` object later.
        
        Inside the regular expression, some special directives can be used.
        ``$nick`` will be replaced with the nick of the bot and ``,`` or ``:``,
        and ``$nickname`` will be replaced with the nick of the bot.

        Prior to *3.1*, rules could also be made one of three formats of tuple.
        The values would be joined together to form a singular regular
        expression.  However, these kinds of rules add no functionality over
        simple regular expressions, and are considered deprecated in *3.1*.

    .. py:attribute:: event
    
        *See also:* :py:func:`willie.module.event`

        This is one of a number of events, such as ``'JOIN'``, ``'PART'``,
        ``'QUIT'``, etc. (More details can be found in `RFC 1459`_.) When the
        Willie bot is sent one of these events, the function will execute. Note
        that functions with an event must also be given a ``rule`` to match
        (though it may be ``'.*'``, which will always match) or they will not
        be triggered.
        
        .. _RFC 1459: http://www.irchelp.org/irchelp/rfc/rfc.html

    .. py:attribute:: rate
    
        *Availability: 2+*
        
        *See also:* :py:func:`willie.module.rate`

        This limits the frequency with which a single user may use the
        function.  If a function is given a ``rate`` of ``20``, a single user
        may only use that function once every 20 seconds. This limit applies to
        each user individually. Users on the ``admin`` list in Willie's
        configuration are exempted from rate limits.
        
    .. py:attribute:: priority
    
        *See also:* :py:func:`willie.module.priority`

        Priority can be one of ``high``, ``medium``, ``low``. It allows you to
        control the order of callable execution, if your module needs it.
        Defaults to ``medium``

.. py:method:: setup(willie)

    This is an optional function of a module, which will be called while the
    module is being loaded. The purpose of this function is to perform whatever
    actions are needed to allow a module to function properly (e.g, ensuring
    that the appropriate configuration variables exist and are set). Note that
    this normally occurs prior to connection to the server, so the behavior of
    the Willie object's messaging functions is undefined.

    Throwing an exception from this function (such as a `ConfigurationError
    <#willie.config.ConfigurationError>`_) will prevent any callables in the
    module from being registered, and provide an error message to the user.
    This is useful when requiring the presence of configuration values or
    making other environmental requirements.
    
    The bot will not continue loading modules or connecting during the
    execution of this function. As such, an infinite loop (such as an
    unthreaded polling loop) will cause the bot to hang.

.. py:method:: shutdown(willie)

    *Availability: 4.1+*

    This is an optional function of a module, which will be called while the
    Willie is quitting. Note that this normally occurs after closing connection
    to the server, so the behavior of the Willie object's messaging functions
    is undefined. The purpose of this function is to perform whatever actions
    are needed to allow a module to properly clean up (e.g, ensuring that any
    temporary cache files are deleted).

    The bot will not continue notifying other modules or continue quitting
    during the execution of this function. As such, an infinite loop (such as
    an unthreaded polling loop) will cause the bot to hang.

.. py:method:: configure(config)

    *Availability: 3+*

    This is an optional function of a module, which will be called during the
    user's setup of the bot. It's intended purpose is to use the methods of the
    passed ``Config`` object in order to create the configuration variables it
    needs to function properly.

    In *3.1+*, the docstring of this function can be used to document the
    configuration variables that the module uses. This is not currently used
    by the bot itself; it is merely convention.

The ``Willie`` class
--------------------

.. autoclass:: willie.bot.Willie
   :members:

.. py:function:: reply(text, notice=False)

    In a module function, send ``text`` to the channel in which the function was
    triggered, preceeded by the nick of the user who triggered it.

    If ``notice`` is set to True, this function will send the reply in an 
    IRC ``NOTICE`` instead of a regular IRC ``PRIVMSG``.

    This function is not available outside of module functions. It can not
    be used, for example, in a module's ``setup`` or ``shutdown`` function.
    
    The same behavior regarding loop detection and length restrictions
    apply to ``reply`` as to ``msg``, though ``reply`` does not offer
    automatic message splitting.

.. py:function:: say(text, max_messages=1)

    In a module function, send ``text`` to the channel in which the
    function was triggered.
    
    This function is not available outside of module functions. It can not
    be used, for example, in a module's ``configure`` function.

    The same behavior regarding loop detection and length restrictions, as
    well as message splitting, apply to ``say`` as to ``msg``.
    
.. py:function:: action(text, recipient=None)

    In a module function, send ``text`` to the channel in which the function
    was triggered preceeded by CTCP ACTION directive (result identical to using
    /me in most clients).

    If ``recipient`` is specified and is not ``None``, this function will send
    the message to ``recipient`` instead of the originating channel.
    ``recipient`` can be either a channel or a user.

    This function is not available outside of module functions. It can not
    be used, for example, in a module's ``configure`` function.

    The same behavior regarding loop detection and length restrictions apply
    to ``action`` as to ``msg`` and ``say``, though like ``reply`` there is
    no facility for message splitting.

.. py:function:: notice(text, recipient=None)

    In a module function, send ``text`` to the channel in which the function
    was triggered as an IRC ``NOTICE``.

    If ``recipient`` is specified and is not ``None``, this function will send
    the message to ``recipient`` instead of the originating channel.
    ``recipient`` can be either a channel or a user.

    This function is not available outside of module functions. It can not
    be used, for example, in a module's ``configure`` function.

    The same behavior regarding loop detection and length restrictions apply
    to ``action`` as to ``msg`` and ``say``, though like ``reply`` there is
    no facility for message splitting.

.. py:function:: quit(message)

    Gracefully quit and shutdown, using ``message`` as the quit message.

    Willie will notify modules that it is quitting should the modules have
    a ``shutdown`` method.
    
.. py:function:: part(channel)

    Part ``channel``

.. py:function:: join(channel, password = None)

    Join a channel named ``channel``.

.. py:attribute:: nick

    Willie's current nick. Changing this while Willie is running is unsupported.

.. py:attribute:: name

    Willie's "real name", as used for whois.

.. py:attribute:: password

    Willie's NickServ password

.. py:attribute:: channels

    A list of Willie's initial channels. This list will initially be the same
    as the one given in the config file, but is not guaranteed to be kept 
    up-to-date.

.. py:attribute:: ops 
.. py:attribute:: halfplus

    *Availability: 3+*
    
    Dictionary mapping channels to a list of their ops, and half-ops and ops
    respectively.

.. py:function:: write(args, text=None)

    Send a command to the server

    ``args`` is an iterable of strings, which are joined by spaces.
    ``text`` is treated as though it were the final item in ``args``, but
    is preceeded by a ``:``. This is a special case which  means that
    ``text``, unlike the items in ``args`` may contain spaces (though this
    constraint is not checked by ``write``).

    In other words, both ``willie.write(('PRIVMSG',), 'Hello, world!')``
    and ``willie.write(('PRIVMSG', ':Hello, world!'))`` will send
    ``PRIVMSG :Hello, world!`` to the server.

    Newlines and carriage returns ('\\n' and '\\r') are removed before
    sending. Additionally, if the message (after joining) is longer than
    than 510 characters, any remaining characters will not be sent.

   .. py:function:: msg(recipient, text, max_messages=1)

    Send a PRIVMSG of ``text`` to ``recipient``. If the same ``text`` was
    the message in 5 or more of the last 8 calls to ``msg``, ``'...'`` will
    be sent instead. If this condition is met, and ``'...'`` is more than 3
    of the last 8 calls, no message will be sent. This is intended to prevent
    Willie from being caught in an infinite loop with another bot, or being
    used to spam.
    
    If ``max_messages`` argument is optional, and defaults to 1. The
    message will be split into that number of segments. Each segment will
    be 400 bytes long or less (bearing in mind that messages are UTF-8
    encoded). The message will be split at the last space before the 400th
    byte, or at the 400th byte if no such space exists. The remainder will
    be split in the same manner until either the given number of segments
    is reached or the remainder is less than 400 bytes.

    If the message is too long to fit into the given number of segments (or
    if no number is given), the bot will send as many bytes to the server
    as it can. The server, due to the structure of the protocol, will
    likely truncate the message further, to a length that is not
    determinable by Willie (though you can generally rely on 400 bytes
    making it through).

    Note that when a message is split not on a space but on a byte number,
    no attention is given to Unicode character boundaries, and no other
    word boundaries besides space will be split upon. This will not cause
    problems in the vast majority of cases.

.. py:function:: debug(tag, text, level)

    *Availability: 3+*
    
    Send ``text`` to Willie's configured ``debug_target``. This can be either
    an IRC channel (starting with ``#``) or ``stdio``. Suppress the message
    if the given ``level`` is lower than Willie's configured ``verbose``
    setting. Acceptable values for ``level`` are ``'verbose'`` (only send if
    Willie is in verbose mode), ``'warning'`` (send if Willie is in verbose
    or warning mode), ``always`` (send debug message regardless of the configured debug level).
    Returns True if the message is sent or printed, and False if it
    is not.
    
    If ``debug_target`` is a channel, the same behavior regarding loop
    detection and length restrictions apply to ``debug`` as to ``msg``.

.. py:function:: add_op(channel, name)
.. py:function:: add_halfop(channel, name)

    *Availability: 3+, deprecated in 4.1.0*

    Add ``name`` to ``channel``'s entry in the ``ops`` or ``halfplus``
    dictionaries, respectively.

.. py:function:: del_op(channel, name)
.. py:function:: del_halfop(channel, name)

    *Availability: 3+, deprecated in 4.1.0*
    
    Remove ``name`` from ``channel``'s entry in the ``ops`` or ``halfplus``
    dictionaries, respectively.

.. py:function:: flush_ops(channel)
    
    *Availability: 3+, deprecated in 4.1.0*
    
    Re-initialize  and empty the ``ops`` and ``halfops`` entry for
    ``channel``.

.. py:function:: init_ops_list(self, channel)

    *Availability: 3+, deprecated in 4.1.0*
    
    Create an empty entry in ``ops`` and ``halfops`` for ``channel``. This
    will not damage existing entries, but must be done before users can be
    added to either dictionary.

The ``Trigger`` class
---------------------

.. py:class:: Trigger
 
    .. py:attribute:: sender
    
        The channel (or nick, in a private message) from which the message was
        sent.
    
    .. py:attribute:: nick
    
        The nick of the person who sent the message.
    
    .. py:attribute:: event
    
        The event which triggered the message.
    
    .. py:attribute:: bytes
    
        The line which triggered the message.
    
    .. py:attribute:: match
    
        The regular expression `MatchObject`_ for the triggering line.

        .. _MatchObject: http://docs.python.org/library/re.html#match-objects
        .. _re: http://docs.python.org/library/re.html
    
    .. py:attribute:: group
    
        The ``group`` function of the ``match`` attribute.
                
        See Python `re`_ documentation for details.
    
    .. py:attribute:: groups
    
        The ``groups`` function of the ``match`` attribute.
                
        See Python `re`_ documentation for details.
    
    .. py:attribute:: args
    
        The arguments given to a command.
    
    .. py:attribute:: admin
    
        True if the nick which triggered the command is in Willie's admin list as
        defined in the config file.
    
    .. py:attribute:: owner
    
        True if the nick which triggered the command is the owner stated in the
        config file.
    
    .. py:attribute:: host
    
        The host which sent the triggering message.

    .. py:attribute:: isop
    
        *Availability: 3+, deprecated in 4.1.0*
        
        True if the nick which triggered the command is an op on the channel it was triggered in.
        Will always be False if the command was triggered by a private message

    .. py:attribute:: isvoice
    
        *Availability: 3+, deprecated in 4.1.0*

        True if the nick which triggered the command is voiced on the channel it was triggered in.
        Will always be False if the command was triggered by a private message
        Will be True if user is an op or half-op, even if they don't have +v

More advanced: ``db`` and ``config``
====================================

The ``willie`` object has, among others, the attributes ``db`` and
``config``. These can be used for a number of functions and features.

The ``WillieDB`` class
----------------------

.. automodule:: willie.db
   :members:

The ``Config`` class
--------------------

.. automodule:: willie.config
   :members:
   :undoc-members:

Miscellaneous: ``web``, ``tools``, ``module``, ``formatting``
=============================================================

These provide a number of useful shortcuts for common tasks.

willie.web
----------

.. automodule:: willie.web
   :members:

willie.tools
------------

.. automodule:: willie.tools
   :members:

willie.module
-------------
.. automodule:: willie.module
   :members:

willie.formatting
-----------------
.. automodule:: willie.formatting
   :members:
   :undoc-members:

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

