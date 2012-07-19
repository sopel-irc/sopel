.. Phenny/Jenni/Willie IRC Bot documentation master file, created by
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
different versions of it floating around. For this documentation, we will cover
three: the original "phenny" by Sean B. Palmer the "jenni" fork by Michael
Yanovich, and the "Willie" fork by Edward Powell et al. While all recieve
periodic updates, the above lists them in a generally ascending order of
recentness.

For clarity's sake, this documentation will refer to these forks as different
"API levels" or "API versions". The version numbers will approach the square
root of 2 (1.41421...), the mathematical constant *e* (2.71828...), and pi 
(3.14159...) respectively. When a fork adds a new feature, and this guide
documents it, the current API level of that fork will be given one more
decimal.

.. contents:: :depth: 2

Getting started: Your functions, ``jenni``, and ``line``
========================================================

At its most basic, writing a jenni module involves creating a Python file with
some number of functions in it. Each of these functions will be passed a "Jenni"
object ("Phenny" in *1.x*) and a "Trigger" object (CommandInput in *1.x* and
*2.x*). By convention, these are named ``phenny`` and ``input`` in *1.x*,
``jenni`` and ``input`` in *2.x*, and ``jenni`` and ``trigger`` in *3.x*. For
the purposes of this guide, the *3.x* names will be used.

Your modules
------------

A jenni module contains one or more ``callables``. It may optionally contain a
``configure`` or ``setup`` function. ``callable``s are given a number of
attributes, which determine when they will be executed. Syntactically, this is
done at the same indentation level as the function's ``def`` line, following the
last line of the function.

.. py:method:: callable(jenni, trigger)

    This is the general function format, called by jenni when a command is used,
    a rule is matched, or an event is seen, as determined by the attributes of
    the function. The details of what this function does are entirely up to the
    module writer - the only hard requirement from the bot is that it be callable
    with a ``Jenni`` object and a ``Trigger`` object , as noted above. Usually,
    methods of the Jenni object will be used in reply to the trigger, but this
    isn't a requirement.
    
    Note that the name can, and should, be anything - it doesn't need to be called
    callable.

    .. py:attribute:: commands
    
        A list of commands which will trigger the function. If the jenni instance
        is in a channel, or sent a PRIVMSG, where one of these strings is said,
        preceeded only by the configured prefix (a period, by default), the
        function will execute.
    
    .. py:attribute:: rule
    
        A regular expression which will trigger the function. If the jenni
        instance is in a channel, or sent a PRIVMSG, where a string matching this
        expression is said, the function will execute. Note that captured groups
        here will be retrievable through the ``Trigger`` object later.

    .. py:attribute:: event
    
        This is one of a number of events, such as ``'JOIN'``, ``'PART'``,
        ``'QUIT'``, etc. (More details can be found in RFC 1459.) When the jenni
        bot is sent one of these events, the function will execute. Note that
        functions with an event must also be given a ``rule`` to match (though
        it may be ``'.*'``, which will always match) or they will not be triggered.
    
    .. py:attribute:: rate
    
        *Availability: 2+*
        
        This limits the frequency with which a single user may use the function.
        If a function is given a ``rate`` of ``20``, a single user may only use
        that function once every 20 seconds. This limit applies to each user
        individually. Users on the ``admin`` list in jenni's configuration are
        exempted from rate limits.

.. py:method:: setup(jenni)

    This is an optional function of a module, which will be called while the
    module is being loaded. Note that this normally occurs prior to connection
    to the server, so the behavior of the Jenni object's messaging functions is
    undefined. The purpose of this function is to perform whatever actions are
    needed to allow a module to function properly (e.g, ensuring that the
    appropriate configuration variables are set and exist).
    
    The bot will not continue loading modules or connecting during the execution
    of this function. As such, an infinite loop (such as an unthreaded polling
    loop) will cause the bot to hang.

.. py:method:: configure(config)

    *Availability: 3+*
    This is an optional function of a module, which will be called during the
    user's setup of the bot. It's intended purpose is to use the method of the
    passed ``Config`` object in order to create the configuration variables it
    needs to function properly. It is expected to return a string, beginning and
    ending with a newline character (``'\n'``), which is to be written to the
    configuration file.

The ``Jenni`` class
-------------------

.. autoclass:: bot.Jenni
    :members:
    
    .. py:function:: reply(text)
    
        In a module function, send ``text`` to the channel in which the function
        was triggered, preceeded by the nick of the user who triggered it.
        
        This function is not available outside of module functions. It can not
        be used, for example, in a module's ``configure`` function.
        
        The same behavior regarding loop detection and length restrictions apply
        to ``reply`` as to ``msg``.
    
    .. py:function:: say(text)
    
        In a module function, send ``text`` to the channel in which the function
        was triggered.
        
        This function is not available outside of module functions. It can not
        be used, for example, in a module's ``configure`` function.

        The same behavior regarding loop detection and length restrictions apply
        to ``say`` as to ``msg``.
    
    .. py:attribute:: nick
    
        jenni's current nick. Changing this while jenni is running is untested.
    
    .. py:attribute:: name
    
        jenni's "real name", as used for whois.
    
    .. py:attribute:: password
    
        jenni's NickServ password
    
    .. py:attribute:: channels
    
        A list of jenni's initial channels. This list will initially be the same
        as the one given in the config file, but is not guaranteed to be kept 
        up-to-date.
    
    .. py:attribute:: ops 
    .. py:attribute:: halfplus
    
        Dictionary mapping channels to a list of their ops, and half-ops and ops
        respectively.
    
    .. py:function:: write(args, text=None)
    
        Send a command to the server. In the simplest case, ``args`` is a list
        containing just the command you wish to send, and ``text`` the argument
        to that command {e.g. write(['JOIN'], '#channel')}
        
        More specifically, ``args`` will be joined together, separated by a
        space. If text is given, it will be added preceeded by a space and a 
        colon (' :').
        
        Newlines and carriage returns ('\\n' and '\\r') are removed before
        sending. Additionally, if the joined ``args`` and ``text`` are more than
        510 characters, any remaining characters will not be sent.
    
    .. py:function:: msg(recipient, text)
    
        Send a PRIVMSG of ``text`` to ``recipient``. If the same ``text`` was
        the message in 5 or more of the last 8 calls to ``msg``, ``'...'`` will
        be sent instead. If this condition is met, and ``'...'`` is more than 3
        of the last 8 calls, no message will be sent. This is intended to prevent
        jenni from being caught in an infinite loop with another bot, or being
        used to spam.
        
        After loop detection, the message is checked for length. If the sum of
        the lengths of ``text`` and ``recipient`` are greater than 500, ``text``
        will be truncated to fit this limit.
    
    .. py:function:: debug(tag, text, level)
    
        Send ``text`` to jenni's configured ``debug_target``. This can be either
        an IRC channel (starting with ``#``) or ``stdio``. Suppress the message
        if the given ``level`` is lower than jenni's configured ``verbose``
        setting. Acceptable values for ``level`` are ``'verbose'`` (only send if
        jenni is in verbose mode) and ``'warning'`` (send if jenni is in verbose
        or warning mode). Return True if the message is sent or printed, and False if it
        is not.
        
        If ``debug_target`` is a channel, the same behavior regarding loop
        detection and length restrictions apply to ``debug`` as to ``msg``.
    
    .. py:function:: addOp(channel, name)
    .. py:function:: addHalfOp(channel, name)
    
        Add ``name`` to ``channel``'s entry in the ``ops`` or ``halfplus``
        dictionaries, respectively.
    
    .. py:function:: delOp(channel, name)
    .. py:function:: delHalfOp(channel, name)
    
        Remove ``name`` from ``channel``'s entry in the ``ops`` or ``halfplus``
        dictionaries, respectively.
    
    .. py:function:: flushOps(channel)
    
        Re-initialize  and empty the ``ops`` and ``halfops`` entry for
        ``channel``.
    
    .. py:function:: startOpsList(self, channel)
    
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
    
        The regular expression ``MatchObject_`` for the triggering line.
        .. _MatchObject: http://docs.python.org/library/re.html#match-objects
    
    .. py:attribute:: group
    
        The ``group`` function of the ``match`` attribute.
                
        See Python ``re_`` documentation for details.
    
    .. py:attribute:: groups
    
        The ``groups`` function of the ``match`` attribute.
                
        See Python ``re_`` documentation for details.
    
    .. py:attribute:: args
    
        The arguments given to a command.
    
    .. py:attribute:: admin
    
        True if the nick which triggered the command is in jenni's admin list as
        defined in the config file.
    
    .. py:attribute:: owner
    
        True if the nick which triggered the command is the owner stated in the
        config file.
    
    .. py:attribute:: host
    
        The host which sent the triggering message.
    

More advanced: ``settings`` and ``config``
==========================================

The ``jenni`` object has, among others, the attributes ``settings`` and
``config``. These can be used for a number of functions and features.

The ``SettingsDB`` class
------------------------

.. automodule:: settings
   :members:

The ``Config`` class
--------------------

.. automodule:: config
   :members:
   :undoc-members:

Miscellaneous: ``web``
======================

.. automodule:: web
    :members:

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

