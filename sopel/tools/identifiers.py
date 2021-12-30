"""Identifier tools to represent IRC names (nick or channel)."""
from __future__ import annotations

import string
from typing import Callable

Casemapping = Callable[[str], str]

ASCII_TABLE = str.maketrans(string.ascii_uppercase, string.ascii_lowercase)
RFC1459_TABLE = str.maketrans(
    string.ascii_uppercase + '[]\\~',
    string.ascii_lowercase + '{}|^',
)
RFC1459_STRICT_TABLE = str.maketrans(
    string.ascii_uppercase + '[]\\',
    string.ascii_lowercase + '{}|',
)


def ascii_lower(text: str) -> str:
    """Lower ``text`` according to the ASCII CASEMAPPING"""
    return text.translate(ASCII_TABLE)


def rfc1459_lower(text: str) -> str:
    """Lower ``text`` according to :rfc:`1459` (with ``~`` mapped to ``^``).

    Similar to :func:`rfc1459_strict_lower`, but also maps ``~`` to
    ``^`` as defined for the ``rfc1459`` value of the
    `CASEMAPPING parameter`__.

    .. __: https://modern.ircdocs.horse/index.html#casemapping-parameter
    """
    return text.translate(RFC1459_TABLE)


def rfc1459_strict_lower(text: str) -> str:
    """Lower ``text`` according to :rfc:`1459` (strict version).

    As per `section 2.2`__:

        Because of IRC's scandanavian origin, the characters ``{}|`` are
        considered to be the lower case equivalents of the characters ``[]\\``.

    .. __: https://datatracker.ietf.org/doc/html/rfc1459#section-2.2
    """
    return text.translate(RFC1459_STRICT_TABLE)


_channel_prefixes = ('#', '&', '+', '!')


class Identifier(str):
    """A ``str`` subclass which acts appropriately for IRC identifiers.

    When used as normal ``str`` objects, case will be preserved.
    However, when comparing two Identifier objects, or comparing an Identifier
    object with a ``str`` object, the comparison will be case insensitive.
    This case insensitivity includes the case convention conventions regarding
    ``[]``, ``{}``, ``|``, ``\\``, ``^`` and ``~`` described in RFC 2812.
    """
    def __new__(cls, *args, **kwargs) -> 'Identifier':
        return str.__new__(cls, *args)

    def __init__(
        self,
        identifier: str,
        *,
        casemapping: Casemapping = rfc1459_lower,
    ) -> None:
        super().__init__()
        self.casemapping: Casemapping = casemapping
        """Casemapping function to lower the identifier."""
        self._lowered = self.casemapping(identifier)

    def lower(self):
        """Get the RFC 2812-compliant lowercase version of this identifier.

        :return: RFC 2812-compliant lowercase version of the
                 :py:class:`Identifier` instance
        :rtype: str
        """
        return self.casemapping(self)

    @staticmethod
    def _lower(identifier: str):
        """Convert an identifier to lowercase per RFC 2812.

        :param str identifier: the identifier (nickname or channel) to convert
        :return: RFC 2812-compliant lowercase version of ``identifier``
        :rtype: str
        """
        if isinstance(identifier, Identifier):
            return identifier.lower()
        return rfc1459_lower(identifier)

    @staticmethod
    def _lower_swapped(identifier: str):
        """Backward-compatible version of :meth:`_lower`.

        :param str identifier: the identifier (nickname or channel) to convert
        :return: RFC 2812-non-compliant lowercase version of ``identifier``
        :rtype: str

        This is what the old :meth:`_lower` function did before Sopel 7.0. It maps
        ``{}``, ``[]``, ``|``, ``\\``, ``^``, and ``~`` incorrectly.

        You shouldn't use this unless you need to migrate stored values from the
        previous, incorrect "lowercase" representation to the correct one.
        """
        # The tilde replacement isn't needed for identifiers, but is for
        # channels, which may be useful at some point in the future.
        low = identifier.lower().replace('{', '[').replace('}', ']')
        low = low.replace('|', '\\').replace('^', '~')
        return low

    def __repr__(self):
        return "%s(%r)" % (
            self.__class__.__name__,
            self.__str__()
        )

    def __hash__(self):
        return self._lowered.__hash__()

    def __lt__(self, other):
        if isinstance(other, str):
            other = self.casemapping(other)
        return str.__lt__(self._lowered, other)

    def __le__(self, other):
        if isinstance(other, str):
            other = self.casemapping(other)
        return str.__le__(self._lowered, other)

    def __gt__(self, other):
        if isinstance(other, str):
            other = self.casemapping(other)
        return str.__gt__(self._lowered, other)

    def __ge__(self, other):
        if isinstance(other, str):
            other = self.casemapping(other)
        return str.__ge__(self._lowered, other)

    def __eq__(self, other):
        if isinstance(other, str):
            other = self.casemapping(other)
        return str.__eq__(self._lowered, other)

    def __ne__(self, other):
        return not (self == other)

    def is_nick(self) -> bool:
        """Check if the Identifier is a nickname (i.e. not a channel)

        :return: ``True`` if this :py:class:`Identifier` is a nickname;
                 ``False`` if it appears to be a channel

        ::

            >>> from sopel import tools
            >>> ident = tools.Identifier('Sopel')
            >>> ident.is_nick()
            True
            >>> ident = tools.Identifier('#sopel')
            >>> ident.is_nick()
            False

        """
        return bool(self) and not self.startswith(_channel_prefixes)
