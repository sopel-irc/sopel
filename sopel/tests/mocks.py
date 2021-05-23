# coding=utf-8
"""Test mocks: they fake objects for testing.

.. versionadded:: 7.0
"""
from __future__ import absolute_import, division, print_function, unicode_literals


from sopel.irc.abstract_backends import AbstractIRCBackend


class MockIRCBackend(AbstractIRCBackend):
    """Fake IRC connection backend for testing purpose.

    :param bot: a Sopel instance
    :type bot: :class:`sopel.bot.Sopel`

    This backend doesn't require an actual connection. Instead, it stores every
    message sent in the :attr:`message_sent` list.

    You can use the :func:`~sopel.tests.rawlist` function to compare the
    messages easily, and the :meth:`clear_message_sent` method to clear
    previous messages::

        >>> from sopel.tests import rawlist, mocks
        >>> backend = mocks.MockIRCBackend(bot=None)
        >>> backend.irc_send(b'PRIVMSG #channel :Hi!\\r\\n')
        >>> backend.message_sent == rawlist('PRIVMSG #channel :Hi!')
        True
        >>> backend.clear_message_sent()
        [b'PRIVMSG #channel :Hi!\\r\\n']
        >>> backend.message_sent
        []

    .. seealso::

        The
        :class:`parent class <sopel.irc.abstract_backends.AbstractIRCBackend>`
        contains all the methods that can be used on this test backend.

    """
    def __init__(self, *args, **kwargs):
        super(MockIRCBackend, self).__init__(*args, **kwargs)
        self.message_sent = []
        """List of raw messages sent by the bot.

        This list will be populated each time the :meth:`irc_send` method is
        used: it will contain the raw IRC lines the bot wanted to send.

        You can clear this list with the :meth:`clear_message_sent` method, or
        use the :func:`~sopel.tests.rawlist` function to compare it.
        """
        self.connected = False
        """Convenient status flag.

        Set to ``True`` to make the bot think it is connected.
        """

    def is_connected(self):
        return self.connected

    def irc_send(self, data):
        """Store ``data`` into :attr:`message_sent`."""
        self.message_sent.append(data)

    def clear_message_sent(self):
        """Clear and return previous messages sent.

        :return: a copy of the cleared messages sent
        :rtype: :class:`list`

        .. versionadded:: 7.1
        """
        # make a copy
        sent = list(self.message_sent)
        # clear the message sent
        self.message_sent = []
        return sent


class MockIRCServer(object):
    """Fake IRC Server that can send messages to a test bot.

    :param bot: test bot instance to send messages to
    :type bot: :class:`sopel.bot.Sopel`
    :param bool join_threads: whether message functions should join running
                              threads before returning (default: ``True``)

    This mock object helps developers when they want to simulate an IRC server
    sending messages to the bot.

    The default ``join_threads`` behavior is suitable for testing most common
    plugin callables, and ensures that all callables dispatched by the ``bot``
    in response to messages sent via this ``MockIRCServer`` are finished
    running before execution can continue. If set to ``False``, the mock
    server will not wait for the bot to finish processing threaded
    :term:`callables <Plugin callable>` before returning.

    .. note::

        You can override ``join_threads`` on a per-method-call basis with the
        ``blocking`` arguments to the instance methods below.

    The :class:`~sopel.tests.factories.IRCFactory` factory can be used to
    create such mock object, either directly or by using ``py.test`` and the
    :func:`~sopel.tests.pytest_plugin.ircfactory` fixture.

    .. versionadded:: 7.1

        The ``join_threads`` parameter.
    """
    def __init__(self, bot, join_threads=True):
        self.bot = bot
        self.join_threads = join_threads
        # TODO: `blocking` method args below should be made kwarg-ONLY in py3

    @property
    def chanserv(self):
        """ChanServ's message prefix."""
        return 'ChanServ!ChanServ@services.'

    def channel_joined(self, channel, users=None, blocking=None):
        """Send events as if the bot just joined a channel.

        :param str channel: channel to send message for
        :param list users: list (or tuple) of nicknames that will be present
                           in the ``RPL_NAMREPLY`` event
        :param bool blocking: whether to block until all triggered threads
                              have finished (optional)

        This will send 2 messages to the bot:

        * a ``RPL_NAMREPLY`` event (353), giving information about ``users``
          present in ``channel``
        * a ``RPL_ENDOFNAMES`` event (366) for completion

        Use this to emulate when the bot joins a channel, and the server
        replies with the list of connected users::

            factory.channel_joined('#test', ['Owner', '@ChanServ'])

        In this example, the bot will know that there are 2 other users present
        in ``#test``: "Owner" (a regular user) and "ChanServ" (which is a
        channel operator). Note that the bot itself will be added to the list
        of users automatically, and you **should not** pass it in the ``users``
        parameter.

        This is particularly useful to populate the bot's memory of who is in
        a channel.

        If ``blocking`` is ``True``, this method will wait to join all running
        triggers' threads before returning. Setting it to ``False`` will skip
        this step. If not specified, this :class:`MockIRCServer` instance's
        ``join_threads`` argument will be obeyed.

        .. versionadded:: 7.1

            The ``blocking`` parameter.

        .. seealso::

            The ``join_threads`` argument to :class:`MockIRCServer`.

        .. note::

            To add a user to a channel after using this method, you should
            use the :meth:`join` method.
        """
        # automatically add the bot's nick to the list
        users = set(users or [])
        users.add(self.bot.nick)
        message = ':irc.example.com 353 {bot} = {channel} :{users}'.format(
            bot=self.bot.nick,
            users=' '.join(list(users)),
            channel=channel,
        )
        self.bot.on_message(message)

        message = (
            ':irc.example.com 366 {bot} = {channel} '
            ':End of /NAMES list.'
        ).format(
            bot=self.bot.nick,
            channel=channel,
        )
        self.bot.on_message(message)

        if (blocking is None and self.join_threads) or blocking:
            for t in self.bot.running_triggers:
                t.join()

    def mode_set(self, channel, flags, users, blocking=None):
        """Send a MODE event for a ``channel``

        :param str channel: channel receiving the MODE event
        :param str flags: MODE flags set
        :param list users: users getting the MODE flags
        :param bool blocking: whether to block until all triggered threads
                              have finished (optional)

        This will send a MODE message as if ``ChanServ`` added/removed channel
        modes for a set of ``users``. This method assumes the ``flags``
        parameter follows the `IRC specification for MODE`__::

            factory.mode_set('#test', '+vo-v', ['UserV', UserOP', 'UserAnon'])

        If ``blocking`` is ``True``, this method will wait to join all running
        triggers' threads before returning. Setting it to ``False`` will skip
        this step. If not specified, this :class:`MockIRCServer` instance's
        ``join_threads`` argument will be obeyed.

        .. versionadded:: 7.1

            The ``blocking`` parameter.

        .. seealso::

            The ``join_threads`` argument to :class:`MockIRCServer`.

        .. __: https://tools.ietf.org/html/rfc1459#section-4.2.3
        """
        message = ':{chanserv} MODE {channel} {flags} {users}'.format(
            chanserv=self.chanserv,
            channel=channel,
            flags=flags,
            users=' '.join(users),
        )
        self.bot.on_message(message)

        if (blocking is None and self.join_threads) or blocking:
            for t in self.bot.running_triggers:
                t.join()

    def join(self, user, channel, blocking=None):
        """Send a ``channel`` JOIN event from ``user``.

        :param user: factory for the user who joins the ``channel``
        :type user: :class:`MockUser`
        :param str channel: channel the ``user`` joined
        :param bool blocking: whether to block until all triggered threads
                              have finished (optional)

        This will send a ``JOIN`` message as if ``user`` just joined the
        channel::

            factory.join(MockUser('NewUser'), '#test')

        If ``blocking`` is ``True``, this method will wait to join all running
        triggers' threads before returning. Setting it to ``False`` will skip
        this step. If not specified, this :class:`MockIRCServer` instance's
        ``join_threads`` argument will be obeyed.

        .. versionadded:: 7.1

            The ``blocking`` parameter.

        .. seealso::

            The ``join_threads`` argument to :class:`MockIRCServer`.

        .. seealso::

            This function is a shortcut to call the bot with the result from
            the user factory's :meth:`~MockUser.join` method.
        """
        self.bot.on_message(user.join(channel))

        if (blocking is None and self.join_threads) or blocking:
            for t in self.bot.running_triggers:
                t.join()

    def say(self, user, channel, text, blocking=None):
        """Send a ``PRIVMSG`` to ``channel`` by ``user``.

        :param user: factory for the user who sends a message to ``channel``
        :type user: :class:`MockUser`
        :param str channel: recipient of the ``user``'s ``PRIVMSG``
        :param str text: content of the message sent to the ``channel``
        :param bool blocking: whether to block until all triggered threads
                              have finished (optional)

        This will send a ``PRIVMSG`` message as if ``user`` sent it to the
        ``channel``, and the server forwarded it to its clients::

            factory.say(MockUser('NewUser'), '#test', '.shrug')

        If ``blocking`` is ``True``, this method will wait to join all running
        triggers' threads before returning. Setting it to ``False`` will skip
        this step. If not specified, this :class:`MockIRCServer` instance's
        ``join_threads`` argument will be obeyed.

        .. versionadded:: 7.1

            The ``blocking`` parameter.

        .. seealso::

            The ``join_threads`` argument to :class:`MockIRCServer`.

        .. seealso::

            This function is a shortcut to call the bot with the result from
            the user's :meth:`~MockUser.privmsg` method.
        """
        self.bot.on_message(user.privmsg(channel, text))

        if (blocking is None and self.join_threads) or blocking:
            for t in self.bot.running_triggers:
                t.join()

    def pm(self, user, text, blocking=None):
        """Send a ``PRIVMSG`` to the bot by a ``user``.

        :param user: factory for the user object who sends a message
        :type user: :class:`MockUser`
        :param str text: content of the message sent to the bot
        :param bool blocking: whether to block until all triggered threads
                              have finished (optional)

        This will send a ``PRIVMSG`` message as forwarded by the server for
        a ``user`` sending it to the bot::

            factory.pm(MockUser('NewUser'), 'A private word.')

        If ``blocking`` is ``True``, this method will wait to join all running
        triggers' threads before returning. Setting it to ``False`` will skip
        this step. If not specified, this :class:`MockIRCServer` instance's
        ``join_threads`` argument will be obeyed.

        .. versionadded:: 7.1

            The ``blocking`` parameter.

        .. seealso::

            The ``join_threads`` argument to :class:`MockIRCServer`.

        .. seealso::

            This function is a shortcut to call the bot with the result from
            the user factory's :meth:`~MockUser.privmsg` method, using the
            bot's nick as recipient.
        """
        self.bot.on_message(user.privmsg(self.bot.nick, text))

        if (blocking is None and self.join_threads) or blocking:
            for t in self.bot.running_triggers:
                t.join()


class MockUser(object):
    """Fake user that can generate messages to send to a bot.

    :param str nick: nickname
    :param str user: IRC username
    :param str host: user's host

    The :class:`~sopel.tests.factories.UserFactory` factory can be used to
    create such mock object, either directly or by using ``py.test`` and the
    :func:`~sopel.tests.pytest_plugin.userfactory` fixture.
    """
    def __init__(self, nick=None, user=None, host=None):
        self.nick = nick or 'Test'
        self.user = user or self.nick.lower()
        self.host = host or 'example.com'

    @property
    def prefix(self):
        """User's hostmask as seen by other users on the server.

        When the server forwards a User's command, it uses this prefix.
        """
        return '{nick}!{user}@{host}'.format(
            nick=self.nick, user=self.user, host=self.host)

    def privmsg(self, recipient, text):
        """Generate a ``PRIVMSG`` command forwarded by a server for the user.

        :param str recipient: a channel name or the bot's nick
        :param str text: content of the message
        :return: a ``PRIVMSG`` command forwarded by the server as if it
                 originated from the user's hostmask
        :rtype: str
        """
        message = ':{prefix} PRIVMSG {recipient} :{text}\r\n'.format(
            prefix=self.prefix,
            recipient=recipient,
            text=text,
        )

        assert len(message.encode('utf-8')) <= 512, (
            'PRIVMSG command must NOT exceed the 512 bytes limit '
            '(\\r\\n included). Trying to send this command:\n`%r`' % message
        )

        return message

    def join(self, channel):
        """Generate a ``JOIN`` command forwarded by the server for the user.

        :param str channel: channel the user joined
        :return: the ``JOIN`` command the server sends to its clients present
                 in the same ``channel`` when the user joins it.
        :rtype: str
        """
        return ':{prefix} JOIN {channel}\r\n'.format(
            prefix=self.prefix,
            channel=channel)
