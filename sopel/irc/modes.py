"""Mode management for IRC channels.

.. seealso::

    https://modern.ircdocs.horse/#mode-message

.. versionadded:: 8.0
"""
from __future__ import generator_stop

import enum
import logging
from typing import Dict, Generator, List, NamedTuple, Optional, Set, Tuple


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
    pass


class ModeTypeUnknown(ModeException):
    """Exception when a mode's type is unknown or cannot be determined."""
    def __init__(self, mode) -> None:
        super().__init__('Unknown type for mode %s' % mode)


class ModeTypeImproperlyConfigured(ModeException):
    """Exception when the mode's type management is not configured properly."""
    def __init__(self, mode: str, letter: str) -> None:
        message = 'Type {mode} for mode {letter} is not properly configured.'
        super().__init__(message.format(mode=mode, letter=letter))


def _parse_modestring(
    modestring: str,
) -> Generator[Tuple[str, bool], None, None]:
    is_added = True
    for char in modestring:
        if char in '+-':
            is_added = char == '+'
            continue
        yield (char, is_added)


class ModeMessage(NamedTuple):
    """Mode message with modes and privileges."""
    modes: Tuple[Tuple[str, str, bool, Optional[str]], ...]
    """Tuple of added and removed modes.

    Each item follows the same structure::

        (type, mode, is_added, param)

    Where ``type`` is the mode type (such as A, B, C, D); ``mode`` is the mode
    letter; ``is_added`` tells if the mode should be added or removed; and
    ``param`` is an optional parameter value for that mode only when necessary.
    """
    privileges: Tuple[Tuple[str, bool, str], ...]
    """Tuple of added and removed privileges.

    Each item follows the same structure::

        (privilege, is_added, target)

    Where ``privilege`` is the privilege letter; ``is_added`` tells if the
    privilege should be added or removed; and ``target`` is the target for that
    privilege.
    """
    ignored_modes: Tuple[Tuple[str, bool], ...]
    """Ignored modes when they are unknown or there is a missing parameter.

    Each item follows the same structure::

        (mode, is_added)

    Where ``mode`` is the mode or privilege letter and ``is_added`` tells if
    the mode or privilege wants to be added or removed.
    """
    leftover_params: Tuple[str, ...]
    """Parameters not used by any valid mode or privilege."""


class ModeParser:
    """ModeMessage parser for IRC's ``MODE`` messages for channel modes."""
    PRIVILEGES: Set[str] = {
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
        chanmodes: Dict[str, Tuple[str, ...]] = CHANMODES,
        type_params: Dict[str, ParamRequired] = DEFAULT_MODETYPE_PARAM_CONFIG,
        privileges: Set[str] = PRIVILEGES,
    ) -> None:
        self.chanmodes: Dict[str, Tuple[str, ...]] = dict(chanmodes)
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

    def get_mode_info(
        self,
        mode: str,
        is_added: bool,
    ) -> Tuple[Optional[str], bool, bool]:
        """Retrieve ``mode``'s information when added or removed.

        :raise ModeTypeUnknown: when the mode's type is unknown and isn't a
                                user privilege
        :raise ModeTypeImproperlyConfigured: when the mode's type is known but
                                             there is no information for
                                             parameters (if and when they are
                                             required by the mode)
        :return: a tuple with three values: the mode type, if it requires a
                 parameter, and if it's a channel mode or a user privilege

        ::

            >>> chanmodes = {'A': tuple('beI'), 'B': tuple('k')}
            >>> t_params = {
            ...     'A': ParamRequired.ALWAYS,
            ...     'B': ParamRequired.ADDED,
            ... }
            >>> mm = ModeParser(chanmodes, t_params)
            >>> mm.get_mode_info('e', False)
            ('A', True, False)
            >>> mm.get_mode_info('k', False)
            ('B', False, False)
            >>> mm.get_mode_info('v', True)
            (None, True, True)

        .. note::

            A user privilege ``mode`` doesn't have a type so the first value
            returned will be ``None`` in that case.
        """
        try:
            letter = self.get_mode_type(mode)
        except ModeTypeUnknown:
            if mode in self.privileges:
                # a user privilege doesn't have a type
                return None, True, True
            # not a user privilege: re-raise error
            raise

        if letter not in self.type_params:
            # we don't know how to handle this type of mode
            raise ModeTypeImproperlyConfigured(mode, letter)

        type_param = self.type_params[letter]
        return letter, not type_param == ParamRequired.NEVER and (
            type_param == ParamRequired.ALWAYS
            or type_param == ParamRequired.ADDED and is_added
            or type_param == ParamRequired.REMOVED and not is_added
        ), False

    def parse_modestring(
        self,
        modestring: str,
        params: Tuple[str, ...]
    ) -> ModeMessage:
        """Parse a ``modestring`` for a channel with its ``params``.

        :return: the parsed and validated information for that ``modestring``
        """
        imodes = iter(_parse_modestring(modestring))
        iparams = iter(params)
        modes: List = []
        privileges: List = []
        for mode, is_added in imodes:
            param = None
            try:
                letter, required, is_priv = self.get_mode_info(mode, is_added)
                if required:
                    try:
                        param = next(iparams)
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

            if is_priv:
                privileges.append((mode, is_added, param))
            else:
                modes.append((letter, mode, is_added, param))

        return ModeMessage(
            tuple(modes),
            tuple(privileges),
            tuple(imodes),
            tuple(iparams),
        )
