"""Mode management for IRC channels.

The :class:`ModeParser` class is used internally by the bot to parse ``MODE``
messages for channels. User modes are not parsed (yet), as the bot doesn't
manage them.

The goal of the parser is to return a :class:`ModeMessage` containing the
actions represented by the raw message:

* channel modes added/removed (including their parameters, if any)
* privileges added/removed for user(s) in a channel

Errors (ignored modes and unused parameters) are also included, mostly for
detecting when an IRC server is not conforming to specifications.

.. important::

    This is mostly for internal use only as plugin developers should be more
    interested in :attr:`privileges<sopel.tools.target.Channel.privileges>`
    rather than how Sopel knows about them.

    The interface of this module is subject to change between Sopel releases
    without advance notice, even in patch versions.

.. seealso::

    https://modern.ircdocs.horse/#mode-message

.. versionadded:: 8.0
"""
from __future__ import annotations

import enum
import logging
from typing import (
    NamedTuple,
    Tuple,
    TYPE_CHECKING,
    Union,
)


if TYPE_CHECKING:
    from collections.abc import Iterator


ModeTuple = Tuple[str, bool]
"""Tuple of mode information: ``(mode, is_added)``.

Where ``mode`` is the mode or privilege letter and ``is_added`` tells if
the mode or privilege wants to be added or removed.

This type alias represents the basic information for each mode found when
parsing a modestring like ``+abc-efg``. In that example mode ``a`` and mode
``f`` would be represented as these tuples: ``('a', True)`` and
``('f', False)``.
"""

# TODO: replace Union by | when dropping support for Python 3.9
# Type aliases are evaluated at import time unlike type annotation
# Python 3.8 and 3.9 don't support the | operator.
ModeDetails = Tuple[str, str, bool, Union[str, None]]
"""Tuple of mode details as ``(letter, mode, is_added, param)``.

Where ``type`` is the mode type (such as A, B, C, D); ``mode`` is the mode
letter; ``is_added`` tells if the mode should be added or removed; and
``param`` is an optional parameter value for that mode only when necessary.
"""
PrivilegeDetails = Tuple[str, bool, str]
"""Tuple of privilege details as ``(mode, is_added, param)``

Where ``privilege`` is the privilege letter; ``is_added`` tells if the
privilege should be added or removed; and ``target`` is the target for that
privilege.
"""


LOGGER = logging.getLogger(__name__)


class ParamRequired(enum.Enum):
    """Enum of param requirement for mode types."""
    ALWAYS = 'always'
    """The mode type always requires a parameter."""
    ADDED = 'added'
    """The mode type requires a parameter only when the mode is added."""
    REMOVED = 'removed'
    """The mode type requires a parameter only when the mode is removed."""
    NEVER = 'never'
    """The mode type never requires a parameter."""


DEFAULT_MODETYPE_PARAM_CONFIG = {
    'A': ParamRequired.ALWAYS,
    'B': ParamRequired.ALWAYS,
    'C': ParamRequired.ADDED,
    'D': ParamRequired.NEVER,
}
"""Default parameter requirements for mode types."""


class ModeException(Exception):
    """Base exception class for mode management."""


class ModeTypeUnknown(ModeException):
    """Exception when a mode's type is unknown or cannot be determined."""
    def __init__(self, mode: str) -> None:
        super().__init__('Unknown type for mode %s' % mode)


class ModeTypeImproperlyConfigured(ModeException):
    """Exception when the mode's type management is not configured properly."""
    def __init__(self, mode: str, letter: str) -> None:
        message = 'Type {mode} for mode {letter} is not properly configured.'
        super().__init__(message.format(mode=mode, letter=letter))


def parse_modestring(modestring: str) -> Iterator[ModeTuple]:
    """Parse a modestring like ``+abc-def`` and yield :class:`ModeTuple`."""
    is_added = True
    for char in modestring:
        if char in '+-':
            is_added = char == '+'
            continue
        yield (char, is_added)


class ModeMessage(NamedTuple):
    """Mode message with channel's modes and channel's privileges."""
    modes: tuple[ModeDetails, ...]
    """Tuple of added and removed modes.

    Each item is a :class:`ModeDetails`.
    """
    privileges: tuple[PrivilegeDetails, ...]
    """Tuple of added and removed privileges.

    Each item is a :class:`PrivilegeDetails`.
    """
    ignored_modes: tuple[ModeTuple, ...]
    """Ignored modes when they are unknown or there is a missing parameter.

    Each item is a :class:`ModeTuple`.
    """
    leftover_params: tuple[str, ...]
    """Parameters not used by any valid mode or privilege."""


class ModeParser:
    """ModeMessage parser for IRC's ``MODE`` messages for channel modes."""
    PRIVILEGES: set[str] = {
        "v",  # VOICE
        "h",  # HALFOP
        "o",  # OP
        "a",  # ADMIN
        "q",  # OWNER
        "y",  # OPER
        "Y",  # OPER
    }
    """Set of user privileges used by default."""

    CHANMODES = {
        'A': tuple('beI'),
        'B': tuple('k'),
        'C': tuple('l'),
        'D': tuple('Oimnpsrt'),
    }
    """Default CHANMODES per :rfc:`2811`.

    .. note::

        Mode ``a`` has been removed from the default list, as it appears
        to be a relic of the past and is more commonly used as a privilege.

        Mode ``q`` has been removed too, as it is commonly used as a privilege.

        If a server is unhappy with these defaults, they should advertise
        ``CHANMODES`` and ``PREFIX`` properly.

    """

    def __init__(
        self,
        chanmodes: dict[str, tuple[str, ...]] = CHANMODES,
        type_params: dict[str, ParamRequired] = DEFAULT_MODETYPE_PARAM_CONFIG,
        privileges: set[str] = PRIVILEGES,
    ) -> None:
        self.chanmodes: dict[str, tuple[str, ...]] = dict(chanmodes)
        """Map of mode types (``str``) to their lists of modes (``tuple``).

        This map should come from ``ISUPPORT``, usually through
        :attr:`bot.isupport.CHANMODES <sopel.irc.isupport.ISupport.CHANMODES>`.
        """
        self.type_params = dict(type_params)
        """Map of mode types (``str``) with their param requirements.

        This map defaults to :data:`DEFAULT_MODETYPE_PARAM_CONFIG`.
        """
        self.privileges = set(privileges)
        """Set of valid user privileges.

        This set should come from ``ISUPPORT``, usually through
        :attr:`bot.isupport.PREFIX <sopel.irc.isupport.ISupport.PREFIX>`.

        If a server doesn't advertise its prefixes for user privileges,
        :attr:`PRIVILEGES` will be used as a default value.
        """

    def get_mode_type(self, mode: str) -> str:
        """Retrieve the type of ``mode``.

        :raise ModeTypeUnknown: if the mode's type cannot be determined
        :return: the mode's type as defined by :attr:`chanmodes`

        ::

            >>> mm = ModeParser({'A': tuple('beI'), 'B': tuple('k')}, {})
            >>> mm.get_mode_type('b')
            'A'
            >>> mm.get_mode_type('k')
            'B'

        This method will raise a :exc:`ModeTypeUnknown` if the mode is unknown,
        including the case where ``mode`` is actually a user privilege such as
        ``v``.
        """
        for letter, modes in self.chanmodes.items():
            if mode in modes:
                return letter
        raise ModeTypeUnknown(mode)

    def get_mode_info(self, mode: str, is_added: bool) -> tuple[str, bool]:
        """Retrieve ``mode``'s information when added or removed.

        :raise ModeTypeUnknown: when the mode's type is unknown
        :raise ModeTypeImproperlyConfigured: when the mode's type is known but
                                             there is no information for
                                             parameters (if and when they are
                                             required by the mode)
        :return: a tuple with two values: the mode type and if it requires
                 a parameter

        ::

            >>> chanmodes = {'A': tuple('beI'), 'B': tuple('k')}
            >>> t_params = {
            ...     'A': ParamRequired.ALWAYS,
            ...     'B': ParamRequired.ADDED,
            ... }
            >>> mm = ModeParser(chanmodes, t_params)
            >>> mm.get_mode_info('e', False)
            ('A', True)
            >>> mm.get_mode_info('k', False)
            ('B', False)
            >>> mm.get_mode_info('e', True)
            ('A', True)
            >>> mm.get_mode_info('k', True)
            ('B', True)

        .. note::

            A user privilege ``mode`` doesn't have a type and will trigger
            a :exc:`ModeTypeUnknown` exception.
        """
        letter = self.get_mode_type(mode)

        if letter not in self.type_params:
            # we don't know how to handle this type of mode
            raise ModeTypeImproperlyConfigured(mode, letter)

        type_param = self.type_params[letter]
        return letter, not type_param == ParamRequired.NEVER and (
            type_param == ParamRequired.ALWAYS
            or type_param == ParamRequired.ADDED and is_added
            or type_param == ParamRequired.REMOVED and not is_added
        )

    def parse(self, modestring: str, params: tuple[str, ...]) -> ModeMessage:
        """Parse a ``modestring`` for a channel with its ``params``.

        :param modestring: suite of modes with +/- sign, such as ``+b-v``
        :param params: tuple of parameters as given by the MODE message
        :return: the parsed and validated information for that ``modestring``

        This method parses a modestring, i.e. a suite of modes and privileges
        with + and - signs. The result is a :class:`ModeMessage` with:

        * parsed modes, with their parameters when required
        * parsed privileges, with their parameters
        * ignore modes (unknown and invalid modes)
        * leftover parameters (parameter unused)

        For example this message:

        .. code-block:: irc

            :irc.example.com MODE #foobar -o+vi mario luigi bowser

        Should be parsed like this::

            >>> modestring = '-o+vi'
            >>> params = ('mario', 'luigi', 'bowser')
            >>> modes = modeparser.parse(modestring, params)
            >>> modes.modes
            (('D', 'i', True, None),)
            >>> modes.privileges
            (('o', False, 'mario'), ('v', True, 'luigi'))
            >>> modes.leftover_params
            ('bowser',)

        The modestring ``-o+vi`` means::

        * remove ``o`` privileges to user ``mario``
        * add ``v`` privileges to user ``luigi``
        * set ``i`` mode on channel ``#foobar`` (no parameter required)

        Which means that ``bowser`` shouldn't be here, and can be retrieved
        through the ``leftover_params`` attribute.
        """
        imodes = iter(parse_modestring(modestring))
        iparams = iter(params)
        modes: list[ModeDetails] = []
        privileges: list[PrivilegeDetails] = []

        for mode, is_added in imodes:
            required = False

            try:
                if mode in self.privileges:
                    priv_param: str = next(iparams)
                    privileges.append((mode, is_added, priv_param))
                else:
                    mode_param: str | None = None
                    letter, required = self.get_mode_info(mode, is_added)
                    if required:
                        mode_param = next(iparams)
                    modes.append((letter, mode, is_added, mode_param))
            except StopIteration:
                # Not enough parameters: we have to stop here
                return ModeMessage(
                    tuple(modes),
                    tuple(privileges),
                    ((mode, is_added),) + tuple(imodes),
                    tuple(),
                )
            except ModeException as modeerror:
                LOGGER.debug(
                    'Invalid modestring: %r; error: %s',
                    modestring,
                    modeerror,
                )
                return ModeMessage(
                    tuple(modes),
                    tuple(privileges),
                    ((mode, is_added),) + tuple(imodes),
                    tuple(iparams),
                )

        return ModeMessage(
            tuple(modes),
            tuple(privileges),
            tuple(imodes),
            tuple(iparams),
        )
