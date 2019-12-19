# coding=utf-8
""":mod:`sopel.irc` is the core IRC module for Sopel.

This sub-package contains everything that is related to the IRC protocol
(connection, commands, abstract client, etc.) and that can be used to implement
the Sopel bot.

In particular, it defines the interface for the
:class:`IRC backend<sopel.irc.abstract_backends.AbstractIRCBackend>`, and the
interface for the :class:`bot itself<sopel.irc.AbstractBot>`. This is all
internal code that isn't supposed to be used directly by a plugin developer,
who should worry about :class:`sopel.bot.Sopel` only.

.. important::

    When working on core IRC protocol related features, consult protocol
    documentation at https://www.irchelp.org/protocol/rfc/

"""
# Copyright 2008, Sean B. Palmer, inamidst.com
# Copyright 2012, Elsie Powell, http://embolalia.com
# Copyright © 2012, Elad Alfassa <elad@fedoraproject.org>
# Copyright 2019, Florian Strzelecki <florian.strzelecki@gmail.com>
#
# Licensed under the Eiffel Forum License 2.
from __future__ import unicode_literals, absolute_import, print_function, division

import sys
import time
import os
import logging

try:
    import ssl
    if not hasattr(ssl, 'match_hostname'):
        # Attempt to import ssl_match_hostname from python-backports
        # TODO: Remove when dropping Python 2 support
        import backports.ssl_match_hostname
        ssl.match_hostname = backports.ssl_match_hostname.match_hostname
        ssl.CertificateError = backports.ssl_match_hostname.CertificateError
    has_ssl = True
except ImportError:
    # no SSL support
    has_ssl = False

import threading
from datetime import datetime

from sopel import tools
from sopel.trigger import PreTrigger

from .backends import AsynchatBackend, SSLAsynchatBackend
from .isupport import ISupport
from .utils import safe, CapReq

if sys.version_info.major >= 3:
    unicode = str

__all__ = ['abstract_backends', 'backends', 'utils']

LOGGER = logging.getLogger(__name__)


class AbstractBot(object):
    """Abstract definition of Sopel's interface."""
    def __init__(self, settings):
        # private properties: access as read-only properties
        self._nick = tools.Identifier(settings.core.nick)
        self._user = settings.core.user
        self._name = settings.core.name
        self._isupport = ISupport()
        self._myinfo = None

        self.backend = None
        """IRC Connection Backend."""
        self.connection_registered = False
        """Is the IRC Connection registered yet?"""
        self.settings = settings
        """Bot settings."""
        self.enabled_capabilities = set()
        """A set containing the IRCv3 capabilities that the bot has enabled."""
        self._cap_reqs = dict()
        """A dictionary of capability names to a list of requests."""

        # internal machinery
        self.sending = threading.RLock()
        self.last_error_timestamp = None
        self.error_count = 0
        self.stack = {}
        self.hasquit = False
        self.last_raw_line = ''  # last raw line received

    @property
    def nick(self):
        """Sopel's current ``Identifier``."""
        return self._nick

    @property
    def user(self):
        """Sopel's user/ident."""
        return self._user

    @property
    def name(self):
        """Sopel's "real name", to be displayed in WHOIS responses."""
        return self._name

    @property
    def config(self):
        """The :class:`sopel.config.Config` for the current Sopel instance."""
        # TODO: Deprecate config, replaced by settings
        return self.settings

    @property
    def isupport(self):
        """Features advertised by the server.

        :type: :class:`~.isupport.ISupport` instance
        """
        return self._isupport

    @property
    def myinfo(self):
        """Server/network information.

        :type: :class:`~.utils.MyInfo` instance

        .. versionadded:: 7.0
        """
        if self._myinfo is None:
            raise AttributeError('myinfo')
        return self._myinfo

    # Connection

    def get_irc_backend(self):
        """Set up the IRC backend based on the bot's settings.

        :return: the initialized IRC backend object
        :rtype: an object implementing the interface of
                :class:`~sopel.irc.abstract_backends.AbstractIRCBackend`
        """
        timeout = int(self.settings.core.timeout)
        ping_timeout = timeout / 2
        backend_class = AsynchatBackend
        backend_args = [self]
        backend_kwargs = {
            'server_timeout': timeout,
            'ping_timeout': ping_timeout,
        }

        if self.settings.core.use_ssl:
            if has_ssl:
                backend_class = SSLAsynchatBackend
                backend_kwargs.update({
                    'verify_ssl': self.settings.core.verify_ssl,
                    'ca_certs': self.settings.core.ca_certs,
                })
            else:
                LOGGER.warning(
                    'SSL is not available on your system; '
                    'attempting connection without it')

        return backend_class(*backend_args, **backend_kwargs)

    def run(self, host, port=6667):
        """Connect to IRC server and run the bot forever.

        :param str host: the IRC server hostname
        :param int port: the IRC server port
        """
        source_address = ((self.settings.core.bind_host, 0)
                          if self.settings.core.bind_host else None)

        self.backend = self.get_irc_backend()
        self.backend.initiate_connect(host, port, source_address)
        try:
            self.backend.run_forever()
        except KeyboardInterrupt:
            LOGGER.warning('Keyboard Interrupt')
            self.quit('KeyboardInterrupt')

    # Connection Events

    def on_connect(self):
        """Handle successful establishment of IRC connection."""
        # Request list of server capabilities. IRCv3 servers will respond with
        # CAP * LS (which we handle in coretasks). v2 servers will respond with
        # 421 Unknown command, which we'll ignore
        self.backend.send_command('CAP', 'LS', '302')

        # authenticate account if needed
        if self.settings.core.auth_method == 'server':
            self.backend.send_pass(self.settings.core.auth_password)
        elif self.settings.core.server_auth_method == 'server':
            self.backend.send_pass(self.settings.core.server_auth_password)

        self.backend.send_nick(self.nick)
        self.backend.send_user(self.user, '+iw', self.nick, self.name)

        LOGGER.info('Connected.')

    def on_message(self, message):
        """Handle an incoming IRC message.

        :param str message: the received raw IRC message
        """
        self.last_raw_line = message

        pretrigger = PreTrigger(self.nick, message)
        if all(cap not in self.enabled_capabilities for cap in ['account-tag', 'extended-join']):
            pretrigger.tags.pop('account', None)

        if pretrigger.event == 'PING':
            self.backend.send_pong(pretrigger.args[-1])
        elif pretrigger.event == 'ERROR':
            LOGGER.error("ERROR received from server: %s", pretrigger.args[-1])
            if self.hasquit:
                # TODO: refactor direct interface with asynchat
                self.backend.close_when_done()
        elif pretrigger.event == '433':
            LOGGER.error('Nickname already in use!')
            # TODO: refactor direct interface with asynchat
            self.backend.handle_close()

        self.dispatch(pretrigger)

    def on_message_sent(self, raw):
        """Handle any message sent through the connection.

        :param str raw: raw text message sent through the connection

        When a message is sent through the IRC connection, the bot will log
        the raw message. If necessary, it will also simulate the
        `echo-message`_ feature of IRCv3.

        .. _echo-message: https://ircv3.net/irc/#echo-message
        """
        # Log raw message
        self.log_raw(raw, '>>')

        # Simulate echo-message
        no_echo = 'echo-message' not in self.enabled_capabilities
        echoed = ['PRIVMSG', 'NOTICE']
        if no_echo and any(raw.upper().startswith(cmd) for cmd in echoed):
            # Use the hostmask we think the IRC server is using for us,
            # or something reasonable if that's not available
            host = 'localhost'
            if self.settings.core.bind_host:
                host = self.settings.core.bind_host
            else:
                try:
                    host = self.hostmask
                except KeyError:
                    pass  # we tried, and that's good enough

            pretrigger = PreTrigger(
                self.nick,
                ":{0}!{1}@{2} {3}".format(self.nick, self.user, host, raw)
            )
            self.dispatch(pretrigger)

    def on_error(self):
        """Handle any uncaptured error in the bot itself.

        This method is an override of :meth:`asyncore.dispatcher.handle_error`,
        the :class:`asynchat.async_chat` being a subclass of
        :class:`asyncore.dispatcher`.
        """
        LOGGER.error('Fatal error in core, please review exceptions log.')

        err_log = logging.getLogger('sopel.exceptions')
        err_log.error(
            'Fatal error in core, handle_error() was called.\n'
            'Buffer:\n%s\n'
            'Last Line:\n%s',
            self.backend.buffer,  # TODO: refactor without self.backend
            self.last_raw_line,
        )
        err_log.exception('Fatal error traceback')
        err_log.error('----------------------------------------')

        if self.error_count > 10:
            # quit if too many errors
            if (datetime.now() - self.last_error_timestamp).seconds < 5:
                LOGGER.error('Too many errors, can\'t continue')
                os._exit(1)
            # TODO: should we reset error_count?

        self.last_error_timestamp = datetime.now()
        self.error_count = self.error_count + 1

    def on_close(self):
        """Call shutdown methods."""
        self._shutdown()

    def _shutdown(self):
        """Handle shutdown tasks.

        Must be overridden by subclasses to do anything useful.
        """
        pass

    # Features

    def dispatch(self, pretrigger):
        """Handle running the appropriate callables for an incoming message.

        :param pretrigger: Sopel PreTrigger object
        :type pretrigger: :class:`sopel.trigger.PreTrigger`
        :raise NotImplementedError: if the subclass does not implement this
                                    required method

        .. important::
            This method **MUST** be implemented by concrete subclasses.
        """
        raise NotImplementedError

    def log_raw(self, line, prefix):
        """Log raw line to the raw log.

        :param str line: the raw line
        :param str prefix: additional information to prepend to the log line
        """
        if not self.settings.core.log_raw:
            return
        logger = logging.getLogger('sopel.raw')
        logger.info('\t'.join([prefix, line.strip()]))

    def cap_req(self, module_name, capability, arg=None, failure_callback=None,
                success_callback=None):
        """Tell Sopel to request a capability when it starts.

        :param str module_name: the module requesting the capability
        :param str capability: the capability requested, optionally prefixed
                               with ``-`` or ``=``
        :param str arg: arguments for the capability request
        :param failure_callback: a function that will be called if the
                                 capability request fails
        :type failure_callback: :term:`function`
        :param success_callback: a function that will be called if the
                                 capability is successfully requested
        :type success_callback: :term:`function`

        By prefixing the capability with ``-``, it will be ensured that the
        capability is not enabled. Similarly, by prefixing the capability with
        ``=``, it will be ensured that the capability is enabled. Requiring and
        disabling is "first come, first served"; if one module requires a
        capability, and another prohibits it, this function will raise an
        exception in whichever module loads second. An exception will also be
        raised if the module is being loaded after the bot has already started,
        and the request would change the set of enabled capabilities.

        If the capability is not prefixed, and no other module prohibits it, it
        will be requested. Otherwise, it will not be requested. Since
        capability requests that are not mandatory may be rejected by the
        server, as well as by other modules, a module which makes such a
        request should account for that possibility.

        The actual capability request to the server is handled after the
        completion of this function. In the event that the server denies a
        request, the ``failure_callback`` function will be called, if provided.
        The arguments will be a :class:`~sopel.bot.Sopel` object, and the
        capability which was rejected. This can be used to disable callables
        which rely on the capability. It will be be called either if the server
        NAKs the request, or if the server enabled it and later DELs it.

        The ``success_callback`` function will be called upon acknowledgment
        of the capability from the server, whether during the initial
        capability negotiation, or later.

        If ``arg`` is given, and does not exactly match what the server
        provides or what other modules have requested for that capability, it is
        considered a conflict.
        """
        # TODO raise better exceptions
        cap = capability[1:]
        prefix = capability[0]

        entry = self._cap_reqs.get(cap, [])
        if any((ent.arg != arg for ent in entry)):
            raise Exception('Capability conflict')

        if prefix == '-':
            if self.connection_registered and cap in self.enabled_capabilities:
                raise Exception('Can not change capabilities after server '
                                'connection has been completed.')
            if any((ent.prefix != '-' for ent in entry)):
                raise Exception('Capability conflict')
            entry.append(CapReq(prefix, module_name, failure_callback, arg,
                                success_callback))
            self._cap_reqs[cap] = entry
        else:
            if prefix != '=':
                cap = capability
                prefix = ''
            if self.connection_registered and (cap not in
                                               self.enabled_capabilities):
                raise Exception('Can not change capabilities after server '
                                'connection has been completed.')
            # Non-mandatory will callback at the same time as if the server
            # rejected it.
            if any((ent.prefix == '-' for ent in entry)) and prefix == '=':
                raise Exception('Capability conflict')
            entry.append(CapReq(prefix, module_name, failure_callback, arg,
                                success_callback))
            self._cap_reqs[cap] = entry

    def write(self, args, text=None):
        """Send a command to the server.

        :param args: an iterable of strings, which will be joined by spaces
        :type args: :term:`iterable`
        :param str text: a string that will be prepended with a ``:`` and added
                         to the end of the command

        ``args`` is an iterable of strings, which are joined by spaces.
        ``text`` is treated as though it were the final item in ``args``, but
        is preceded by a ``:``. This is a special case which means that
        ``text``, unlike the items in ``args``, may contain spaces (though this
        constraint is not checked by ``write``).

        In other words, both ``sopel.write(('PRIVMSG',), 'Hello, world!')``
        and ``sopel.write(('PRIVMSG', ':Hello, world!'))`` will send
        ``PRIVMSG :Hello, world!`` to the server.

        Newlines and carriage returns (``'\\n'`` and ``'\\r'``) are removed
        before sending. Additionally, if the message (after joining) is longer
        than than 510 characters, any remaining characters will not be sent.

        .. seealso::

            The connection backend is responsible for formatting and sending
            the message through the IRC connection. See the
            :meth:`sopel.irc.abstract_backends.AbstractIRCBackend.send_command`
            method for more information.

        """
        args = [safe(arg) for arg in args]
        self.backend.send_command(*args, text=text)

    # IRC Commands

    def action(self, text, dest):
        """Send a CTCP ACTION PRIVMSG to a user or channel.

        :param str text: the text to send in the CTCP ACTION
        :param str dest: the destination of the CTCP ACTION

        The same loop detection and length restrictions apply as with
        :func:`say`, though automatic message splitting is not available.
        """
        self.say('\001ACTION {}\001'.format(text), dest)

    def join(self, channel, password=None):
        """Join a ``channel``.

        :param str channel: the channel to join
        :param str password: an optional channel password

        If ``channel`` contains a space, and no ``password`` is given, the
        space is assumed to split the argument into the channel to join and its
        password. ``channel`` should not contain a space if ``password``
        is given.
        """
        self.backend.send_join(channel, password=password)

    def kick(self, nick, channel, text=None):
        """Kick a ``nick`` from a ``channel``.

        :param str nick: nick to kick out of the ``channel``
        :param str channel: channel to kick ``nick`` from
        :param str text: optional text for the kick

        The bot must be operator in the specified channel for this to work.

        .. versionadded:: 7.0
        """
        self.backend.send_kick(channel, nick, reason=text)

    def notice(self, text, dest):
        """Send an IRC NOTICE to a user or channel (``dest``).

        :param str text: the text to send in the NOTICE
        :param str dest: the destination of the NOTICE
        """
        self.backend.send_notice(dest, text)

    def part(self, channel, msg=None):
        """Leave a channel.

        :param str channel: the channel to leave
        :param str msg: the message to display when leaving a channel
        """
        self.backend.send_part(channel, reason=msg)

    def quit(self, message):
        """Disconnect from IRC and close the bot."""
        self.backend.send_quit(reason=message)
        self.hasquit = True
        # Wait for acknowledgment from the server. Per RFC 2812 it should be
        # an ERROR message, but many servers just close the connection.
        # Either way is fine by us. Closing the connection now would mean that
        # stuff in the buffers that has not yet been processed would never be
        # processed. It would also release the main thread, which is
        # problematic because whomever called quit might still want to do
        # something before the main thread quits.

    def reply(self, text, dest, reply_to, notice=False):
        """Send a PRIVMSG to a user or channel, prepended with ``reply_to``.

        :param str text: the text of the reply
        :param str dest: the destination of the reply
        :param str reply_to: the nickname that the reply will be prepended with
        :param bool notice: whether to send the reply as a NOTICE or not,
                            defaults to ``False``

        If ``notice`` is ``True``, send a NOTICE rather than a PRIVMSG.

        The same loop detection and length restrictions apply as with
        :meth:`say`, though automatic message splitting is not available.
        """
        text = '%s: %s' % (reply_to, text)
        if notice:
            self.notice(text, dest)
        else:
            self.say(text, dest)

    def say(self, text, recipient, max_messages=1):
        """Send a PRIVMSG to a user or channel.

        :param str text: the text to send
        :param str recipient: the message recipient
        :param int max_messages: split ``text`` into at most this many messages
                                 if it is too long to fit in one (optional)

        By default, this will attempt to send the entire ``text`` in one
        message. If the text is too long for the server, it may be truncated.

        If ``max_messages`` is given, the ``text`` will be split into at most
        that many messages, each no more than 400 bytes. The split is made at
        the last space character before the 400th byte, or at the 400th byte
        if no such space exists.

        If the ``text`` is too long to fit into the specified number of
        messages using the above splitting, the final message will contain the
        entire remainder, which may be truncated by the server.
        """
        excess = ''
        if not isinstance(text, unicode):
            # Make sure we are dealing with a Unicode string
            text = text.decode('utf-8')

        if max_messages > 1:
            # Manage multi-line only when needed
            text, excess = tools.get_sendable_message(text)

        with self.sending:
            recipient_id = tools.Identifier(recipient)
            recipient_stack = self.stack.setdefault(recipient_id, {
                'messages': [],
                'flood_left': self.config.core.flood_burst_lines,
            })

            if recipient_stack['messages']:
                elapsed = time.time() - recipient_stack['messages'][-1][0]
            else:
                # Default to a high enough value that we won't care.
                # Five minutes should be enough not to matter anywhere below.
                elapsed = 300

            # If flood bucket is empty, refill the appropriate number of lines
            # based on how long it's been since our last message to recipient
            if not recipient_stack['flood_left']:
                recipient_stack['flood_left'] = min(
                    self.config.core.flood_burst_lines,
                    int(elapsed) * self.config.core.flood_refill_rate)

            # If it's too soon to send another message, wait
            if not recipient_stack['flood_left']:
                penalty = float(max(0, len(text) - 50)) / 70
                wait = min(self.config.core.flood_empty_wait + penalty, 2)  # Maximum wait time is 2 sec
                if elapsed < wait:
                    time.sleep(wait - elapsed)

            # Loop detection
            messages = [m[1] for m in recipient_stack['messages'][-8:]]

            # If what we're about to send repeated at least 5 times in the last
            # two minutes, replace it with '...'
            if messages.count(text) >= 5 and elapsed < 120:
                text = '...'
                if messages.count('...') >= 3:
                    # If we've already said '...' 3 times, discard message
                    return

            self.backend.send_privmsg(recipient, text)
            recipient_stack['flood_left'] = max(0, recipient_stack['flood_left'] - 1)
            recipient_stack['messages'].append((time.time(), safe(text)))
            recipient_stack['messages'] = recipient_stack['messages'][-10:]

        # Now that we've sent the first part, we need to send the rest. Doing
        # this recursively seems easier to me than iteratively
        if excess:
            self.say(excess, recipient, max_messages - 1)
