"""Management of IRC server capabilities."""
from __future__ import annotations

from typing import (
    Dict,
    FrozenSet,
    NamedTuple,
    Optional,
    Set,
    Tuple,
    TYPE_CHECKING,
)


if TYPE_CHECKING:
    from sopel.bot import SopelWrapper
    from sopel.trigger import Trigger


class CapabilityInfo(NamedTuple):
    """Capability metadata."""
    name: str
    params: Optional[str]
    available: bool
    enabled: bool


class Capabilities:
    """Capabilities negotiated with the server."""
    def __init__(self) -> None:
        self._available: Dict[str, Optional[str]] = {}
        self._enabled: Set[str] = set()

    def get_capability_info(self, name: str) -> CapabilityInfo:
        """Retrieve metadata about a capability."""
        params = self._available.get(name)
        return CapabilityInfo(
            name,
            params,
            name in self._available,
            name in self._enabled,
        )

    @property
    def available(self) -> Dict[str, Optional[str]]:
        """Dict of available server capabilities."""
        return dict(self._available.items())  # return a copy

    @property
    def enabled(self) -> FrozenSet[str]:
        """Set of enabled server capabilities."""
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
    ) -> Tuple[str, ...]:
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
    ) -> Tuple[str, ...]:
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
    ) -> Tuple[str, ...]:
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
        cap_new: Set[str] = set()
        for available_capability in trigger.split():
            name, *params = available_capability.split('=', maxsplit=1)
            self._available[name] = params[0] if params else None
            cap_new.add(name)

        return tuple(sorted(cap_new))

    def handle_del(
        self,
        bot: SopelWrapper,
        trigger: Trigger,
    ) -> Tuple[str, ...]:
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
        cap_del: Set[str] = set()
        for name in trigger.split():
            if name in self._available:
                del self._available[name]
            if name in self._enabled:
                self._enabled.remove(name)

            cap_del.add(name)

        return tuple(sorted(cap_del))
