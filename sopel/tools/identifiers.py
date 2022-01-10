"""Identifier tools to represent IRC names (nick or channel).

Nick and channel are defined by their names, which are "identifiers": their
names are used to differentiate users from each others, channels from each
others. To ensure that two channels or two users are the same, their
identifiers must be processed to be compared properly. This process depends on
which RFC and how that RFC is implemented by the server: IRC being an old
protocol, different RFCs have differents version of that process:

* :rfc:`RFC 1459 § 2.2<1459#section-2.2>`: ASCII characters, and ``[]\\`` are
  mapped to ``{}|``
* :rfc:`RFC 2812 § 2.2<2812#section-2.2>`: same as in the previous RFC, adding
  ``~`` mapped to ``^``

Then when ISUPPORT was added, the `CASEMAPPING parameter`__ was defined so the
server can say which process to apply:

* ``ascii``: only ``[A-Z]`` must be mapped to ``[a-z]`` (implemented by
  :func:`ascii_lower`)
* ``rfc1459``: follow :rfc:`2812`; because of how it was implemented in most
  server (implemented by :func:`rfc1459_lower`)
* A strict version of :rfc:`1459` also exist but it is not recommended
  (implemented by :func:`rfc1459_strict_lower`)

As a result, the :class:`Identifier` class requires a casemapping function,
which should be provided by the :class:`bot<sopel.bot.Sopel>`.

.. seealso::

    The bot's :class:`make_identifier<sopel.bot.Sopel.make_identifier>` method
    should be used to instantiate an :class:`Identifier` to honor the
    ``CASEMAPPING`` parameter.

.. __: https://modern.ircdocs.horse/index.html#casemapping-parameter
"""
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
DEFAULT_CHANTYPES = ('#', '&', '+', '!')


def ascii_lower(text: str) -> str:
    """Lower ``text`` according to the ``ascii`` value of ``CASEMAPPING``.

    In that version, only ``[A-Z]`` are to be mapped to their lowercase
    equivalent (``[a-z]``). Non-ASCII characters are kept unmodified.
    """
    return text.translate(ASCII_TABLE)


def rfc1459_lower(text: str) -> str:
    """Lower ``text`` according to :rfc:`2812`.

    Similar to :func:`rfc1459_strict_lower`, but also maps ``~`` to ``^``, as
    per :rfc:`RFC 2812 § 2.2<2812#section-2.2>`:

        Because of IRC's Scandinavian origin, the characters ``{}|^`` are
        considered to be the lower case equivalents of the characters
        ``[]\\~``, respectively.

    .. note::

        This is an implementation of the `CASEMAPPING parameter`__ for the
        value ``rfc1459``, which doesn't use :rfc:`1459` but its updated version
        :rfc:`2812`.

    .. __: https://modern.ircdocs.horse/index.html#casemapping-parameter
    """
    return text.translate(RFC1459_TABLE)


def rfc1459_strict_lower(text: str) -> str:
    """Lower ``text`` according to :rfc:`1459` (strict version).

    As per :rfc:`RFC 1459 § 2.2<1459#section-2.2>`:

        Because of IRC's scandanavian origin, the characters ``{}|`` are
        considered to be the lower case equivalents of the characters ``[]\\``.

    """
    return text.translate(RFC1459_STRICT_TABLE)


class Identifier(str):
    """A ``str`` subclass which acts appropriately for IRC identifiers.

    :param str identifier: IRC identifier
    :param casemapping: a casemapping function (optional keyword argument)
    :type casemapping: Callable[[:class:`str`], :class:`str`]

    When used as normal ``str`` objects, case will be preserved.
    However, when comparing two Identifier objects, or comparing an Identifier
    object with a ``str`` object, the comparison will be case insensitive.

    This case insensitivity uses the provided ``casemapping`` function,
    following the rules for the `CASEMAPPING parameter`__ from ISUPPORT. By
    default, it uses :func:`rfc1459_lower`, following
    :rfc:`RFC 2812 § 2.2<2812#section-2.2>`.

    .. note::

        To instantiate an ``Identifier`` with the appropriate ``casemapping``
        function, it is best to rely on
        :meth:`bot.make_identifier<sopel.irc.AbstractBot.make_identifier>`.

    .. versionchanged:: 8.0

        The ``casemapping`` and ``chantypes`` parameters have been added.

    .. __: https://modern.ircdocs.horse/index.html#casemapping-parameter
    """
    def __new__(
        cls,
        identifier: str,
        *,
        casemapping: Casemapping = rfc1459_lower,
        chantypes: tuple = DEFAULT_CHANTYPES,
    ) -> 'Identifier':
        return str.__new__(cls, identifier)

    def __init__(
        self,
        identifier: str,
        *,
        casemapping: Casemapping = rfc1459_lower,
        chantypes: tuple = DEFAULT_CHANTYPES,
    ) -> None:
        super().__init__()
        self.casemapping: Casemapping = casemapping
        """Casemapping function to lower the identifier."""
        self.chantypes = chantypes
        """Tuple of prefixes used for channels."""
        self._lowered = self.casemapping(identifier)

    def lower(self) -> str:
        """Get the IRC-compliant lowercase version of this identifier.

        :return: IRC-compliant lowercase version used for case-insensitive
                 comparisons

        The behavior of this method depends on the identifier's casemapping
        function, which should be selected based on the ``CASEMAPPING``
        parameter from ``ISUPPORT``.

        .. versionchanged:: 8.0

            Now uses the :attr:`casemapping` function to lower the identifier.

        """
        return self.casemapping(self)

    @staticmethod
    def _lower(identifier: str):
        """Convert an identifier to lowercase per :rfc:`2812`.

        :param str identifier: the identifier (nickname or channel) to convert
        :return: RFC 2812-compliant lowercase version of ``identifier``
        :rtype: str

        :meta public:

        .. versionchanged:: 8.0

            Previously, this would lower all non-ASCII characters. It now uses
            a strict implementation of the ``CASEMAPPING`` parameter. This is
            now equivalent to call :func:`rfc1459_lower`.

            If the ``identifier`` is an instance of :class:`Identifier`, this
            will call that identifier's :meth:`lower` method instead.

        """
        if isinstance(identifier, Identifier):
            return identifier.lower()
        return rfc1459_lower(identifier)

    @staticmethod
    def _lower_swapped(identifier: str):
        """Backward-compatible version of :meth:`_lower`.

        :param identifier: the identifier (nickname or channel) to convert
        :return: RFC 2812-non-compliant lowercase version of ``identifier``
        :rtype: str

        This is what the old :meth:`_lower` function did before Sopel 7.0. It
        maps ``{}``, ``[]``, ``|``, ``\\``, ``^``, and ``~`` incorrectly.

        You shouldn't use this unless you need to migrate stored values from
        the previous, incorrect "lowercase" representation to the correct one.

        :meta public:

        .. versionadded: 7.0

            This method was added to ensure migration of improperly lowercased
            data: it reverts the data back to the previous lowercase rules.

        """
        # The tilde replacement isn't needed for identifiers, but is for
        # channels, which may be useful at some point in the future.
        # Always convert to str, to prevent using custom casemapping
        low = str(identifier).lower().replace('{', '[').replace('}', ']')
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

        To detect channels, :attr:`chantypes` is used::

            >>> from sopel import tools
            >>> ident = tools.Identifier('!sopel', chantypes=('#', '&'))
            >>> ident.is_nick()
            True
            >>> ident.chantypes = ('#', '&', '!')
            >>> ident.is_nick()
            False

        """
        return bool(self) and not self.startswith(self.chantypes)
