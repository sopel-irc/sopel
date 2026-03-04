"""Management of IRC capability negotiation.

.. versionadded:: 8.0

This module contains the :class:`Capabilities` class which tracks the state of
the capability negotiation with the IRC server: it can store and update the
state of available and enabled capabilities.

.. important::

    Plugin authors should not instantiate this class directly, as the bot
    exposes an instance through its :attr:`~sopel.irc.AbstractBot.capabilities`
    attribute.

    All state handling methods (such as :meth:`Capabilities.handle_ls`) are
    used by the ``coretasks`` plugin, and should not be used outside.

"""
from __future__ import annotations

from typing import (
    NamedTuple,
    TYPE_CHECKING,
)


if TYPE_CHECKING:
    from sopel.bot import SopelWrapper
    from sopel.trigger import Trigger


class CapabilityInfo(NamedTuple):
    """Capability metadata.

    This contains the details of a capability: if :attr:`available`,
    :attr:`enabled`, and its :attr:`params` (if advertised).

    .. note::

        You can get a capability's info through
        :meth:`Capabilities.get_capability_info`.

    """
    name: str
    """Name of the capability.

    The name of a capability is the name as it appears in the ``CAP LS``
    subcommand, such as ``multi-prefix`` or ``sasl``.
    """
    params: str | None
    """Advertised parameters for this capability.

    When a server supports ``CAP`` version 302, capabilities can have
    parameters. The format and the meaning of the parameters depend on the
    capability itself.

    For example, the ``sasl`` capability can provide the list of SASL
    mechanisms the server supports, such as ``PLAIN,EXTERNAL``.
    """
    available: bool
    """Flag to tell if the server advertises this capability or not.

    This is ``True`` if the ``CAP LS`` subcommand contains the capability.
    """
    enabled: bool
    """Flag to tell if the capability is enabled on the server."""


class Capabilities:
    """Capabilities negotiated with the server.

    This stores a representation of the capability negotiation state between
    the bot and the server: it stores the list of :attr:`available` and
    :attr:`enabled` capabilities, and can track the state by handling various
    ``CAP`` subcommands:

    * :meth:`handle_ls` for ``CAP LS``
    * :meth:`handle_ack` for ``CAP ACK``
    * :meth:`handle_nak` for ``CAP NAK``
    * :meth:`handle_new` for ``CAP NEW``
    * :meth:`handle_del` for ``CAP ADD``
    """
    def __init__(self) -> None:
        self._available: dict[str, str | None] = {}
        self._enabled: set[str] = set()

    def get_capability_info(self, name: str) -> CapabilityInfo:
        """Retrieve metadata about a capability.

        The returned :class:`CapabilityInfo` will tell if the capability is
        advertised by the server; and if so, its parameters and whether it is
        enabled.

        If the capability is unknown, then its ``available`` attribute will be
        ``False``, and its ``params`` attribute will be ``None``.
        """
        params = self._available.get(name)
        return CapabilityInfo(
            name,
            params,
            name in self._available,
            name in self._enabled,
        )

    @property
    def available(self) -> dict[str, str | None]:
        """Dict of available server capabilities.

        Each key is the name of a capability advertised by the server, and each
        value is the parameters as advertised (if any) for this capability.

        If a capability is not in this ``dict``, it means the server doesn't
        advertise it, and it cannot be requested.
        """
        return dict(self._available.items())  # return a copy

    @property
    def enabled(self) -> frozenset[str]:
        """Set of enabled server capabilities.

        Each element is the name of a capability that is enabled on the server.
        """
        return frozenset(self._enabled)

    def is_available(self, name: str) -> bool:
        """Tell if the capability ``name`` is available on the server."""
        return name in self._available

    def is_enabled(self, name: str) -> bool:
        """Tell if the capability ``name`` is enabled on the server."""
        return name in self._enabled

    def handle_ls(self, bot: SopelWrapper, trigger: Trigger) -> bool:
        """Handle a ``CAP LS`` command.

        This method behaves as a plugin callable with its ``bot`` and
        ``trigger`` arguments, with the precise goals to handle ``CAP LS``
        command only, registering available capabilities.

        Then it returns if there is no more ``LS`` command to handle (in case
        of multi-line ``LS``).
        """
        # dev checking
        assert trigger.event == 'CAP'
        assert trigger.args[1] == 'LS'

        # extracting capabilities
        for available_capability in trigger.split():
            name, *params = available_capability.split('=', maxsplit=1)
            self._available[name] = params[0] if params else None

        # return if multiline or not
        multiline = trigger.args[2] == '*'
        return not multiline

    def handle_ack(
        self,
        bot: SopelWrapper,
        trigger: Trigger,
    ) -> tuple[str, ...]:
        """Handle a ``CAP ACK`` command.

        This method behaves as a plugin callable with its ``bot`` and
        ``trigger`` arguments, with the precise goals to handle ``CAP ACK``
        command only, registering enabled or disabled capabilities and tracking
        acknowledgement.

        Then it returns the list of acknowledged capability requests.
        """
        # dev checking
        assert trigger.event == 'CAP'
        assert trigger.args[1] == 'ACK'

        # extracting capabilities
        ack_capabilities = tuple(sorted(trigger.split()))

        # update enabled capabilities
        for ack_capability in ack_capabilities:
            if ack_capability.startswith('-'):
                # ACK a disable request
                cap_reversed = ack_capability.lstrip('-')
                if cap_reversed in self._enabled:
                    self._enabled.remove(cap_reversed)
            else:
                # ACK an enable request
                self._enabled.add(ack_capability)

        # return set of acknowledged capabilities
        return ack_capabilities

    def handle_nak(
        self,
        bot: SopelWrapper,
        trigger: Trigger,
    ) -> tuple[str, ...]:
        """Handle a ``CAP NAK`` command.

        This method behaves as a plugin callable with its ``bot`` and
        ``trigger`` arguments, with the precise goals to handle ``CAP NAK``
        command only.

        Then it returns the list of denied capability requests.
        """
        # dev checking
        assert trigger.event == 'CAP'
        assert trigger.args[1] == 'NAK'

        # extracting capabilities
        nack_capabilities = tuple(sorted((trigger.split())))

        # return tuple of not acknowledged capabilities
        return nack_capabilities

    def handle_new(
        self,
        bot: SopelWrapper,
        trigger: Trigger,
    ) -> tuple[str, ...]:
        """Handle a ``CAP NEW`` command.

        This method behaves as a plugin callable with its ``bot`` and
        ``trigger`` arguments, with the precise goals to handle ``CAP NEW``
        command only.

        It registers which new capabilities are available, then returns this
        list.
        """
        # dev checking
        assert trigger.event == 'CAP'
        assert trigger.args[1] == 'NEW'

        # extracting capabilities
        cap_new: set[str] = set()
        for available_capability in trigger.split():
            name, *params = available_capability.split('=', maxsplit=1)
            self._available[name] = params[0] if params else None
            cap_new.add(name)

        return tuple(sorted(cap_new))

    def handle_del(
        self,
        bot: SopelWrapper,
        trigger: Trigger,
    ) -> tuple[str, ...]:
        """Handle a ``CAP DEL`` command.

        This method behaves as a plugin callable with its ``bot`` and
        ``trigger`` arguments, with the precise goals to handle ``CAP DEL``
        command only.

        It registers which capabilities are not available and not enabled
        anymore, then returns this list.
        """
        # dev checking
        assert trigger.event == 'CAP'
        assert trigger.args[1] == 'DEL'

        # extracting capabilities
        cap_del: set[str] = set()
        for name in trigger.split():
            if name in self._available:
                del self._available[name]
            if name in self._enabled:
                self._enabled.remove(name)

            cap_del.add(name)

        return tuple(sorted(cap_del))
