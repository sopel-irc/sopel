"""Capability Requests management for plugins.

.. versionadded:: 8.0

.. important::

    This is all relatively new. Its usage and documentation is for Sopel core
    development and advanced developers. It is subject to rapid changes
    between versions without much (or any) warning.

    Do **not** build your plugin based on what is here, you do **not** need to.

"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from collections.abc import Generator, Iterable

    from sopel.bot import Sopel, SopelWrapper
    from sopel.plugins.callables import Capability, CapabilityNegotiation


LOGGER = logging.getLogger(__name__)


class Manager:
    """Manager of plugins' capability requests.

    Whenever a plugin declares a capability request (through
    :class:`sopel.plugin.capability`), the bot will register the request with
    this manager.

    The bot is responsible to call the manager at the appropriate time, and the
    manager will store requests' state and handle acknowledgement, by following
    this workflow:

    1. the bot will register plugins' requests with the :meth:`register` method
    2. the bot will request the list of available capabilities with the
       ``CAP LS`` subcommand
    3. upon receiving the list, it'll use the :meth:`request_available` method
       to let the manager send the required ``CAP REQ`` messages.
    4. when the server ``ACK`` a request, the bot will call the
       :meth:`acknowledge` method; when the server ``NAK`` a request, the bot
       will call the :meth:`deny` method
    5. once all requests are handled (either directly or after calling the
       :meth:`resume` method), the bot will send the ``CAP END`` message to end
       capability negotiation
    """
    def __init__(self):
        self._registered: dict[
            # CAP REQ :<text>
            tuple[str, ...],
            # mapping (plugin, request + status)
            dict[str, tuple[Capability, bool]],
        ] = {}
        self._requested: set[tuple[str, ...]] = set()
        self._acknowledged: set[tuple[str, ...]] = set()
        self._denied: set[tuple[str, ...]] = set()

    # properties

    @property
    def registered(self) -> frozenset[tuple[str, ...]]:
        """Set of registered capability requests.

        Each element is a capability request as a tuple of capability names::

            >>> manager.registered
            {('cap1',), ('cap2', 'cap3')}

        A registered request is a request wanted by a plugin. The request may
        or may not be requested, acknowledged, or denied.
        """
        return frozenset(self._registered.keys())

    @property
    def requested(self) -> frozenset[tuple[str, ...]]:
        """Set of requested capability requests.

        Each element is a capability request as a tuple of capability names::

            >>> manager.requested
            {('cap1',), ('cap2', 'cap3')}

        A requested request is a registered request for which the bot sent
        a ``CAP REQ`` message to the server. The request may or may not be
        acknowledged or denied.

        Only registered requests can be requested.
        """
        return frozenset(self._requested)

    @property
    def acknowledged(self) -> frozenset[tuple[str, ...]]:
        """Set of acknowledged capability requests.

        Each element is a capability request as a tuple of capability names::

            >>> manager.acknowledged
            {('cap1',), ('cap2', 'cap3')}

        An acknowledged request is a registered and requested request for which
        the bot received a ``CAP ACK`` message.

        Only requested requests can be acknowledged.
        """
        return frozenset(self._acknowledged)

    @property
    def denied(self) -> frozenset[tuple[str, ...]]:
        """Set of denied capability requests.

        Each element is a capability request as a tuple of capability names::

            >>> manager.denied
            {('cap1',), ('cap2', 'cap3')}

        A denied request is a registered and requested request for which the
        bot received a ``CAP NAK`` message.

        Only requested requests can be denied.
        """
        return frozenset(self._denied)

    @property
    def is_complete(self) -> bool:
        """Tell if the capability negotiation is complete.

        When capability negotiation is complete, the bot can send ``CAP END``
        to notify the server that negotiation is complete.

        The capability negotiation is complete when all capability requests
        have been either acknowledged or denied successfuly (directly or by
        calling the :meth:`resume` method).
        """
        return all(
            status
            for cap_req, values in self._registered.items()
            for _plugin_capability, status in values.values()
            if cap_req in self._requested
        )

    # tell if registered, requested, acknowledged, or denied

    def is_registered(self, request: Iterable[str]) -> bool:
        """Tell if a capability request is registered.

        :param request: a set of capabilities that form a capability request
                        together; this can be any iterable
        """
        return tuple(sorted(request)) in self._registered

    def is_requested(self, request: Iterable[str]) -> bool:
        """Tell if a capability request is requested.

        :param request: a set of capabilities that form a capability request
                        together; this can be any iterable
        """
        return tuple(sorted(request)) in self._requested

    def is_acknowledged(self, request: Iterable[str]) -> bool:
        """Tell if a capability request is acknowledged.

        :param request: a set of capabilities that form a capability request
                        together; this can be any iterable
        """
        return tuple(sorted(request)) in self._acknowledged

    def is_denied(self, request: Iterable[str]) -> bool:
        """Tell if a capability request is denied.

        :param request: a set of capabilities that form a capability request
                        together; this can be any iterable
        """
        return tuple(sorted(request)) in self._denied

    # register, request, resume, acknowledge, deny, etc.

    def register(self, plugin_name: str, request: Capability) -> None:
        """Register a capability ``request`` for ``plugin_name``.

        :param request: the capability request to register for later
        :raise RuntimeError: when the capability request is too long for a
                             single ``CAP REQ`` and ``CAP * ACK``

        Once registered, the capability request can be requested by the bot. A
        registered request appears in :attr:`registered`::

            >>> from sopel import plugin
            >>> request = plugin.capability('cap1')
            >>> manager.register('coretasks', request)
            >>> ('cap1',) in manager.registered
            True
            >>> manager.is_registered(('cap1',))
            True

        It is not, however, directly requested::

            >>> manager.is_requested(('cap1',))
            False

        See :meth:`request_available` to automatically request capabilities
        advertised by the server.

        .. warning::

            Sopel cannot accept a request that is too long, because it does not
            know how to handle a multi-line ACK, and it would not know how to
            call back the appropriate
            :class:`~sopel.plugins.callables.Capability` handler.

        """
        cap_req = ' '.join(request.cap_req)
        if len(cap_req.encode('utf-8')) > 500:
            # "CAP * ACK " is 10 bytes, leaving 500 bytes for the capabilities.
            # Sopel cannot allow multi-line requests, as it won't know how to
            # deal properly with multi-line ACK.
            # The spec says a client SHOULD send multiple requests; however
            # the spec also says that a server will ACK or NAK a whole request
            # at once. So technically, multiple REQs are not the same as a
            # single REQ.
            raise RuntimeError('Capability request too long: %s' % cap_req)

        plugin_caps = self._registered.setdefault(request.cap_req, {})
        plugin_caps[plugin_name] = (
            request, False,
        )
        LOGGER.debug('Capability Request registered: %s', request)

    def request_available(
        self,
        bot: Sopel,
        available_capabilities: Iterable[str],
    ) -> None:
        """Request available capabilities.

        :param bot: the bot instance used to send capability requests
        :param available_capabilities: available capabilities

        This sends ``CAP REQ`` commands for requests that can be made, i.e.
        all the requested capabilities (with or without prefix) must be
        available for Sopel to send the request.

        Requests made are stored as requested; others are ignored::

            >>> manager.register('example', 'cap1')
            >>> manager.register('example', 'cap2')
            >>> manager.request_available(bot, ('cap1', 'cap3'))
            >>> manager.is_requested(('cap1',))
            True
            >>> manager.is_requested(('cap2',))
            False
            >>> manager.is_requested(('cap3',))
            False

        .. important::

            The capability request ``('cap1', '-cap2')`` means "enable cap1 and
            disable cap2", and the request will be acknowledged or denied at
            once. If the server doesn't advertise any of these capabilities,
            the client **should not** send a request.

            As a result, Sopel will send a request to enable or disable
            a capability only if it is advertised first. If a request is
            never made, its callback will never be called, because there
            won't be any related ACK/NAK message from the server.

            Plugin authors should not use the request's callback to activate or
            deactivate features, and instead check the bot's capabilities every
            time they need to.

            The only exception to that is when the plugin needs to perform an
            operation while negotiating the capabilities (such as SASL auth).

        """
        # Requesting capabilities when they are available
        capabilities = set(available_capabilities)
        for cap_req, plugin_requests in self._registered.items():
            # request only if all are available
            cap_req_enables = {
                cap.lstrip('-')
                for cap in cap_req
            }
            text = ' '.join(cap_req)
            if cap_req_enables <= capabilities:
                self._registered[cap_req] = {
                    plugin_name: (handler_info[0], False)
                    for plugin_name, handler_info in plugin_requests.items()
                }
                self._requested.add(cap_req)
                LOGGER.debug('Capability negotiation request: "%s".', text)
                bot.write(('CAP', 'REQ'), text=text)
            else:
                LOGGER.debug(
                    'Unable to negotiate capability request: "%s".', text,
                )

    def resume(
        self,
        request: Iterable[str],
        plugin_name: str,
    ) -> tuple[bool, bool]:
        """Resume the registered plugin capability request.

        :return: a 2-value tuple with (was completed, is completed)

        The capability request, for that plugin, will be marked as done,
        and the result will be about the capability negotiation process:

        * was it already completed before the resume?
        * is it completed now?

        If the capability request cannot be found for that plugin, the result
        value remains the same (it stays incomplete or complete)

        .. important::

            When a request's callback returns
            :attr:`~sopel.plugins.callables.CapabilityNegotiation.CONTINUE`,
            this method must be called later (once the plugin has finished
            its job) or the bot will never send the ``CAP END`` command and
            hang forever.

        .. seealso::

            Plugins can use the method
            :meth:`~sopel.bot.Sopel.resume_capability_negotiation` from the bot
            to resume and automatically send ``CAP END`` when necessary.

        """
        cap_req = tuple(sorted(request))
        was_completed = self.is_complete
        if cap_req not in self._requested:
            return was_completed, was_completed

        handler_info: tuple[Capability, bool] | None = self._registered.get(
            cap_req, {},
        ).get(
            plugin_name, None,
        )

        if not handler_info:
            return was_completed, was_completed

        self._registered[cap_req][plugin_name] = (handler_info[0], True)
        return was_completed, self.is_complete

    def acknowledge(
        self,
        bot: SopelWrapper,
        cap_req: tuple[str, ...],
    ) -> list[tuple[bool, CapabilityNegotiation | None]] | None:
        """Acknowledge a capability request and execute handlers.

        :param bot: bot instance to manage the capabilities for
        :param cap_req: the capability request from ``CAP ACK :<cap_req>``
        :return: a list of results and statuses if the capability was requested

        This acknowledges a capability request and executes its callbacks from
        plugins. It returns the result, as a list of 2-value tuples: the first
        value tells if the callback is done with the processing, and the second
        is the returned value.

        If the capability request was denied before, it is now considered
        acknowledged instead.

        If the capability wasn't requested, the result will be ``None``.
        """
        # nothing to acknowledge
        if cap_req not in self._requested:
            LOGGER.debug('Received CAP ACK for an unknown CAP REQ.')
            return None

        # update acknowledged: callbacks may fail, server ACK nonetheless
        self._acknowledged.add(cap_req)

        if cap_req in self._denied:
            self._denied.remove(cap_req)

        # execute callbacks
        return self._callbacks(bot, cap_req, True)

    def deny(
        self,
        bot: SopelWrapper,
        cap_req: tuple[str, ...],
    ) -> list[tuple[bool, CapabilityNegotiation | None]] | None:
        """Deny a capability request and execute handlers.

        :param bot: bot instance to manage the capabilities for
        :param cap_req: the capability request from ``CAP NAK :<cap_req>``

        This denies a capability request and executes its callbacks from
        plugins. It returns the result, as a list of 2-value tuples: the first
        value tells if the callback is done with the processing, and the second
        is the returned value.

        If the capability request was acknowledged before, it is now considered
        denied instead.

        If the capability wasn't requested, the result will be ``None``.
        """
        # nothing to deny
        if cap_req not in self._requested:
            LOGGER.debug('Received CAP NAK for an unknwon CAP REQ.')
            return None

        # update denied: callbacks may fail, server NAK nonetheless
        self._denied.add(cap_req)

        if cap_req in self._acknowledged:
            self._acknowledged.remove(cap_req)

        # execute callbacks
        return self._callbacks(bot, cap_req, False)

    def _callbacks(
        self,
        bot: SopelWrapper,
        cap_req: tuple[str, ...],
        acknowledged: bool,
    ) -> list[tuple[bool, CapabilityNegotiation | None]]:
        # call back request handlers
        plugin_requests: dict[str, tuple[Capability, bool]] = self._registered.get(
            cap_req, {},
        )
        return [
            self._callback(plugin_name, handler_info, bot, acknowledged)
            for plugin_name, handler_info in plugin_requests.items()
        ]

    def _callback(
        self,
        plugin_name: str,
        handler_info: tuple[Capability, bool],
        bot: SopelWrapper,
        acknowledged: bool,
    ) -> tuple[bool, CapabilityNegotiation | None]:
        handler = handler_info[0]
        is_done, result = handler.callback(bot, acknowledged)
        # update done status in registered
        self._registered[handler.cap_req][plugin_name] = (handler, is_done)
        return (is_done, result)

    def get(
        self,
        cap_req: tuple[str, ...],
        *,
        plugins: list[str] | tuple[str, ...] | set[str] = (),
    ) -> Generator[tuple[str, Capability], None, None]:
        """Retrieve the registered request handlers for a capability request.

        :param cap_req: the capability request to retrieve handlers for
        :return: yield 2-value tuples with (plugin name, capability)
        """
        plugin_requests = self._registered.get(cap_req, {})
        if plugins:
            yield from (
                (plugin_name, plugin_requests[plugin_name][0])
                for plugin_name in plugins
                if plugin_name in plugin_requests
            )
        else:
            for plugin_name, handler_info in plugin_requests.items():
                yield (plugin_name, handler_info[0])
