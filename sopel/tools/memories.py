"""Thread-safe memory data-structures for Sopel.

Sopel uses lots of threads to manage rules and jobs and other features, and it
needs to store shared information safely. This class contains various memory
classes that are thread-safe, with some convenience features.
"""
from __future__ import annotations

from collections import defaultdict
import threading
from typing import Any, TYPE_CHECKING, Union

from typing_extensions import override

from .identifiers import Identifier, IdentifierFactory


if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping
    from typing import Tuple

    # TODO: replace Union by | when dropping support for Python 3.9
    # Type aliases are evaluated at import time so unlike type annotation
    # Python 3.8 and 3.9 don't support the | operator.
    MemoryConstructorInput = Union[
        Mapping[str, Any],
        Iterable[Tuple[str, Any]],
    ]


class _NO_DEFAULT:
    """Private class to help with overriding C methods like ``dict.pop()``.

    Some Python standard library features are implemented in pure C, and can
    have a ``null`` default value for certain parameters that is impossible to
    emulate at the Python layer. This class is our workaround for that.

    .. warning::

        Plugin authors **SHOULD NOT** use this class. It is not part of Sopel's
        public API.

    """


class SopelMemory(dict):
    """A simple thread-safe ``dict`` implementation.

    In order to prevent exceptions when iterating over the values and changing
    them at the same time from different threads, we use a blocking lock in
    ``__setitem__`` and ``__contains__``.

    .. note::

        Unlike the :class:`dict` on which they are based, ``SopelMemory`` and
        its derivative types do not accept key-value pairs as keyword arguments
        at construction time.

    .. versionadded:: 3.1
        As ``Willie.WillieMemory``
    .. versionchanged:: 4.0
        Moved to ``tools.WillieMemory``
    .. versionchanged:: 6.0
        Renamed from ``WillieMemory`` to ``SopelMemory``
    .. versionchanged:: 8.0
        Moved from ``tools`` to ``tools.memories``
    """
    def __init__(self, *args):
        dict.__init__(self, *args)
        self.lock = threading.Lock()

    def __setitem__(self, key, value):
        """Set a key equal to a value.

        The dict is locked for other writes while doing so.
        """
        self.lock.acquire()
        result = dict.__setitem__(self, key, value)
        self.lock.release()
        return result

    def __contains__(self, key):
        """Check if a key is in the dict.

        The dict is locked for writes while doing so.
        """
        self.lock.acquire()
        result = dict.__contains__(self, key)
        self.lock.release()
        return result


class SopelMemoryWithDefault(defaultdict):
    """Same as SopelMemory, but subclasses from collections.defaultdict.

    .. note::

        Unlike the :class:`~collections.defaultdict` on which it is based,
        ``SopelMemoryWithDefault`` does not accept key-value pairs as keyword
        arguments at construction time.

    .. versionadded:: 4.3
        As ``WillieMemoryWithDefault``
    .. versionchanged:: 6.0
        Renamed to ``SopelMemoryWithDefault``
    .. versionchanged:: 8.0
        Moved from ``tools`` to ``tools.memories``
    """
    def __init__(self, *args):
        defaultdict.__init__(self, *args)
        self.lock = threading.Lock()

    def __setitem__(self, key, value):
        """Set a key equal to a value.

        The dict is locked for other writes while doing so.
        """
        self.lock.acquire()
        result = defaultdict.__setitem__(self, key, value)
        self.lock.release()
        return result

    def __contains__(self, key):
        """Check if a key is in the dict.

        The dict is locked for writes while doing so.
        """
        self.lock.acquire()
        result = defaultdict.__contains__(self, key)
        self.lock.release()
        return result


class SopelIdentifierMemory(SopelMemory):
    """Special Sopel memory that stores ``Identifier`` as key.

    This is a convenient subclass of :class:`SopelMemory` that always casts its
    keys as instances of :class:`~.identifiers.Identifier`::

        >>> from sopel import tools
        >>> memory = tools.SopelIdentifierMemory()
        >>> memory['Exirel'] = 'king'
        >>> list(memory.items())
        [(Identifier('Exirel'), 'king')]
        >>> tools.Identifier('exirel') in memory
        True
        >>> 'exirel' in memory
        True

    As seen in the example above, it is possible to perform various operations
    with both ``Identifier`` and :class:`str` objects, taking advantage of the
    case-insensitive behavior of ``Identifier``.

    As it works with :class:`~.identifiers.Identifier`, it accepts an
    identifier factory. This factory usually comes from a
    :class:`bot instance<sopel.bot.Sopel>`, like in the example of a plugin
    setup function::

        def setup(bot):
            bot.memory['my_plugin_storage'] = SopelIdentifierMemory(
                identifier_factory=bot.make_identifier,
            )

    .. note::

        Internally, it will try to do ``key = self.make_identifier(key)``,
        which will raise an exception if it cannot instantiate the key
        properly::

            >>> memory[1] = 'error'
            AttributeError: 'int' object has no attribute 'translate'

    .. versionadded:: 7.1

    .. versionchanged:: 8.0

        Moved from ``tools`` to ``tools.memories``.

        The parameter ``identifier_factory`` has been added to properly
        transform ``str`` into :class:`~.identifiers.Identifier`. This factory
        is stored and accessible through :attr:`make_identifier`.

    """
    def __init__(
        self,
        *args: MemoryConstructorInput,
        identifier_factory: IdentifierFactory = Identifier,
    ) -> None:
        if len(args) > 1:
            raise TypeError(
                'SopelIdentifierMemory expected at most 1 argument, got {}'
                .format(len(args))
            )

        self.make_identifier = identifier_factory
        """A factory to transform keys into identifiers."""

        if len(args) == 1:
            super().__init__(self._convert_keys(args[0]))
        else:
            super().__init__()

    def _make_key(self, key: str | None) -> Identifier | None:
        if key is None:
            return None
        return self.make_identifier(key)

    def _convert_keys(
        self,
        data: MemoryConstructorInput,
    ) -> Iterable[tuple[Identifier, Any]]:
        """Ensure input keys are converted to ``Identifer``.

        :param data: the data passed to the memory at init or update
        :return: a generator of key-value pairs with the keys converted
                 to :class:`~.identifiers.Identifier`

        This private method takes input of a mapping or an iterable of key-value
        pairs and outputs a generator of key-value pairs ready for use in a new
        or updated :class:`self` instance. It is designed to work with any of the
        possible ways initial data can be passed to a :class:`dict`, except that
        ``kwargs`` must be passed to this method as a dictionary.
        """
        # figure out what to generate from
        if hasattr(data, 'items'):
            data = data.items()

        # return converted input data
        return ((self.make_identifier(k), v) for k, v in data)

    def __getitem__(self, key: str | None) -> Any:
        return super().__getitem__(self._make_key(key))

    def __contains__(self, key: Any) -> Any:
        return super().__contains__(self._make_key(key))

    def __setitem__(self, key: str | None, value: Any) -> None:
        super().__setitem__(self._make_key(key), value)

    def setdefault(self, key: str, default: Any = None) -> Any:
        return super().setdefault(self._make_key(key), default)

    def __delitem__(self, key: str) -> None:
        super().__delitem__(self._make_key(key))

    def copy(self):
        """Get a shallow copy of this ``SopelIdentifierMemory``.

        See :meth:`dict.copy`.
        """
        return type(self)(self, identifier_factory=self.make_identifier)

    def get(self, key: str, default: Any = _NO_DEFAULT) -> Any:
        """Get the value of ``key`` from this ``SopelIdentifierMemory``.

        Takes an optional ``default`` value, just like :meth:`dict.get`.
        """
        if default is _NO_DEFAULT:
            return super().get(self._make_key(key))
        return super().get(self._make_key(key), default)

    def pop(self, key: str, default: Any = _NO_DEFAULT) -> Any:
        """Pop the value of ``key`` from this ``SopelIdentifierMemory``.

        Takes an optional ``default`` value, just like :meth:`dict.pop`.
        """
        if default is _NO_DEFAULT:
            return super().pop(self._make_key(key))
        return super().pop(self._make_key(key), default)

    @override
    def update(self, maybe_mapping=tuple()):
        """Update this ``SopelIdentifierMemory`` with key-value pairs.

        See :meth:`dict.update`.
        """
        super().update(self._convert_keys(maybe_mapping))

    def __or__(self, other):
        if not isinstance(other, dict):
            return NotImplemented

        # self on the left, so other's keys overwrite
        new = self.copy()
        new.update(other)
        return new

    def __ror__(self, other):
        if not isinstance(other, dict):
            return NotImplemented

        # self on the right, so keep only new keys from other
        new = self.copy()
        new.update((k, v) for k, v in other.items() if k not in self)
        return new

    def __ior__(self, other):
        if not isinstance(other, dict):
            return NotImplemented
        self.update(other)
        return self

    def __eq__(self, other):
        if not isinstance(other, dict):
            return NotImplemented
        return super().__eq__(other)

    def __ne__(self, other):
        ret = self.__eq__(other)
        return ret if ret is NotImplemented else not ret
