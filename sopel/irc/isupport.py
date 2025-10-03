"""IRC Tools for ISUPPORT management.

When a server wants to advertise its features and settings, it can use the
``RPL_ISUPPORT`` command (``005`` numeric) with a list of arguments.

.. seealso::

    https://modern.ircdocs.horse/#rplisupport-005

"""
# Copyright 2019, Florian Strzelecki <florian.strzelecki@gmail.com>
#
# Licensed under the Eiffel Forum License 2.
from __future__ import annotations

import functools
import itertools
import re


def _optional(parser, default=None):
    # set a parser as optional: will always return the default value provided
    # if there is no value (empty or None)
    @functools.wraps(parser)
    def wrapped(value):
        if not value:
            return default
        return parser(value)
    return wrapped


def _no_value(value):
    # always ignore the value
    return None


def _single_character(value):
    if len(value) > 1:
        raise ValueError('Too many characters: %r.' % value)

    return value


def _map_items(parser=str, map_separator=',', item_separator=':'):
    @functools.wraps(parser)
    def wrapped(value):
        items = sorted(
            item.split(item_separator)
            for item in value.split(map_separator))

        return tuple(
            (k, parser(v) if v else None)
            for k, v in items
        )
    return wrapped


def _parse_chanmodes(value):
    items = value.split(',')

    if len(items) < 4:
        raise ValueError('Not enough channel types to unpack from %r.' % value)

    # add extra channel mode types to their own tuple
    # result in (A, B, C, D, (E, F, G, H, ..., Z))
    # where A, B, C, D = result[:4]
    # and extras = result[4]
    return tuple(items[:4]) + (tuple(items[4:]),)


def _parse_elist(value):
    # letters are case-insensitives
    return tuple(sorted(set(letter.upper() for letter in value)))


def _parse_extban(value):
    args = value.split(',')

    if len(args) < 2:
        raise ValueError('Invalid value for EXTBAN: %r.' % value)

    prefix = args[0] or None
    items = tuple(sorted(set(args[1])))

    return (prefix, items)


def _parse_prefix(value):
    result = re.match(r'\((?P<modes>\S+)\)(?P<prefixes>\S+)', value)

    if not result:
        raise ValueError('Invalid value for PREFIX: %r' % value)

    modes = result.group('modes')
    prefixes = result.group('prefixes')

    if len(modes) != len(prefixes):
        raise ValueError('Mode list does not match for PREFIX: %r' % value)

    return tuple(zip(modes, prefixes))


class ClientTagDeny:
    """Storage for CLIENTTAGDENY ISUPPORT parameter values.

    This class behaves more or less like a set, but is case-insensitive when
    checking membership and stores all elements in lowercase.

    If the special wildcard ``*`` is present, the :meth:`is_denied` method will
    return ``True`` for any tag name, except if the explicit negation of that
    tag name (``-tagname``) is also present.
    """
    def __init__(self, iterable=None):
        self._data = set(x.lower() for x in iterable) if iterable else set()

    def __contains__(self, element: str) -> bool:
        return element.lower() in self._data

    def __eq__(self, other):
        if not isinstance(other, ClientTagDeny):
            return NotImplemented
        return self._data == other._data

    def __or__(self, other):
        result = self.__class__(self)
        result.update(other)
        return result

    def __ior__(self, other):
        self.update(other)
        return self

    def add(self, element: str) -> None:
        self._data.add(element.lower())

    def remove(self, element: str) -> None:
        self._data.remove(element.lower())

    def discard(self, element: str) -> None:
        self._data.discard(element.lower())

    def clear(self):
        self._data.clear()

    def update(self, *others):
        for other in others:
            self._data.update(x.lower() for x in other)

    def __iter__(self):
        return iter(self._data)

    def __len__(self):
        return len(self._data)

    def __repr__(self):
        return f"{self.__class__.__name__}({list(self._data)!r})"

    def is_denied(self, tagname: str) -> bool:
        """Check if the given ``tagname`` is denied.

        :param tagname: the tag name to check
        :return: ``True`` if the tag name is denied, ``False`` otherwise

        Supports wildcard and explicit logic; checks are case-insensitive.
        """
        tagname = tagname.lower()
        if "*" in self._data and f"-{tagname}" not in self._data:
            return True
        elif tagname in self._data:
            return True
        return False


def _parse_clienttagdeny(value: str) -> ClientTagDeny:
    return ClientTagDeny(value.split(','))


ISUPPORT_PARSERS = {
    'AWAYLEN': int,
    'CASEMAPPING': str,
    'CHANLIMIT': _map_items(int),
    'CHANMODES': _parse_chanmodes,
    'CHANNELLEN': int,
    'CHANTYPES': _optional(tuple),
    'CLIENTTAGDENY': _optional(_parse_clienttagdeny, default=ClientTagDeny()),
    'ELIST': _parse_elist,
    'EXCEPTS': _optional(_single_character, default='e'),
    'EXTBAN': _parse_extban,
    'HOSTLEN': int,
    'INVEX': _optional(_single_character, default='I'),
    'KICKLEN': int,
    'LINELEN': int,
    'MAXLIST': _map_items(int),
    'MAXTARGETS': _optional(int),
    'MODES': _optional(int),
    'NETWORK': str,
    'NICKLEN': int,
    'PREFIX': _optional(_parse_prefix),
    'SAFELIST': _no_value,
    'SILENCE': _optional(int),
    'STATUSMSG': _optional(tuple),
    'TARGMAX': _optional(_map_items(int), default=tuple()),
    'TOPICLEN': int,
    'USERLEN': int,
}


def _unescape_param(param):
    """Handle escape sequences in ISUPPORT parameter values.

    Sopel follows the recommendation of `modern.ircdocs.horse`__ which only
    recognizes the escape sequences ``\\x20, \\x5C, \\x3D``. All other such
    escape sequences will be passed through unaltered.

    .. __: https://modern.ircdocs.horse/#rplisupport-005
    """
    HEX_PATTERN = r"\\x([0-9a-fA-F]{2})"

    def _unescape(match):
        num = match.group(1).upper()
        if num == "20":
            result = " "
        elif num == "5C":
            result = "\\"
        elif num == "3D":
            result = "="
        else:
            result = match.group(0)

        return result

    return re.sub(HEX_PATTERN, _unescape, param)


def parse_parameter(arg):
    items = arg.split('=', 1)
    if len(items) == 2:
        key, value = items[0], _unescape_param(items[1])
    else:
        key, value = items[0], None

    if key.startswith('-'):
        # ignore value for removed parameters
        return (key, None)

    parser = ISUPPORT_PARSERS.get(key, _optional(str))
    return (key, parser(value))


class ISupport:
    """Storage class for IRC's ``ISUPPORT`` feature.

    An instance of ``ISupport`` can be used as a read-only dict, to store
    features advertised by the IRC server::

        >>> isupport = ISupport(chanlimit=(('&', None), ('#', 70)))
        >>> isupport['CHANLIMIT']
        (('&', None) ('#', 70))
        >>> isupport.CHANLIMIT  # some parameters are also properties
        {
            '&': None,
            '#': 70,
        }
        >>> 'chanlimit' in isupport  # case-insensitive
        True
        >>> 'chanmode' in isupport
        False
        >>> isupport.CHANMODE  # not advertised by the server!
        Traceback (most recent call last):
          File "<stdin>", line 1, in <module>
        AttributeError: 'ISupport' object has no attribute 'CHANMODE'

    The list of possible parameters can be found at
    `modern.ircdocs.horse's RPL_ISUPPORT Parameters`__.

    .. important::

        While this object's attributes and dict-like behavior are part of
        Sopel's public API, its *methods* are considered internal code and
        plugins should not call them.

    .. __: https://modern.ircdocs.horse/#rplisupport-parameters
    """
    def __init__(self, **kwargs):
        self.__isupport = dict(
            (key.upper(), value)
            for key, value in kwargs.items()
            if not key.startswith('-'))

    def __getitem__(self, key):
        key_ci = key.upper()
        if key_ci not in self.__isupport:
            raise KeyError(key_ci)
        return self.__isupport[key_ci]

    def __contains__(self, key):
        return key.upper() in self.__isupport

    def __getattr__(self, name):
        if name not in self.__isupport:
            raise AttributeError(name)

        return self.__isupport[name]

    def __setattr__(self, name, value):
        # make sure you can't set the value of any ISUPPORT attribute yourself
        if name == '_ISupport__isupport':
            # allow to set self.__isupport inside of the class
            super().__setattr__(name, value)
        elif name in self.__isupport:
            # reject any modification of __isupport
            raise AttributeError("Can't set value for %r" % name)
        elif name not in self.__dict__:
            raise AttributeError('Unknown attribute')

    def get(self, name, default=None):
        """Retrieve value for the feature ``name``.

        :param str name: feature to retrieve
        :param default: default value if the feature is not advertised
                        (defaults to ``None``)
        :return: the value for that feature, if advertised, or ``default``
        """
        return self[name] if name in self else default

    def apply(self, **kwargs):
        """Build a new instance of :class:`ISupport`.

        :return: a new instance, updated with the latest advertised features
        :rtype: :class:`ISupport`

        This method applies the latest advertised features from the server:
        the result contains the new and updated parameters, and doesn't contain
        the removed parameters (marked by ``-{PARAMNAME}``)::

            >>> updated = {'-AWAYLEN': None, 'NICKLEN': 25, 'CHANNELLEN': 10}
            >>> new = isupport.apply(**updated)
            >>> 'CHANNELLEN' in new
            True
            >>> 'AWAYLEN' in new
            False

        """
        kwargs_upper = dict(
            (key.upper(), value)
            for key, value in kwargs.items()
        )
        kept = (
            (key, value)
            for key, value in self.__isupport.items()
            if ('-%s' % key) not in kwargs_upper
        )
        updated = dict(itertools.chain(kept, kwargs_upper.items()))

        return self.__class__(**updated)

    @property
    def CHANLIMIT(self):
        """Expose ``CHANLIMIT`` as a dict, if advertised by the server.

        This exposes information about the maximum number of channels that the
        bot can join for each prefix::

            >>> isupport.CHANLIMIT
            {
                '#': 70,
                '&': None,
            }

        In that example, the bot may join 70 ``#`` channels and any number of
        ``&`` channels.

        This attribute is not available if the server does not provide the
        right information, and accessing it will raise an
        :exc:`AttributeError`.

        .. seealso::

            https://modern.ircdocs.horse/#chanlimit-parameter

        """
        if 'CHANLIMIT' not in self:
            raise AttributeError('CHANLIMIT')

        return dict(self['CHANLIMIT'])

    @property
    def CHANMODES(self):
        """Expose ``CHANMODES`` as a dict.

        This exposes information about 4 types of channel modes::

            >>> isupport.CHANMODES
            {
                'A': 'b',
                'B': 'k',
                'C': 'l',
                'D': 'imnpst',
            }

        The values are empty if the server does not provide this information.

        .. seealso::

            https://modern.ircdocs.horse/#chanmodes-parameter

        """
        if 'CHANMODES' not in self:
            return {"A": "", "B": "", "C": "", "D": ""}

        return dict(zip('ABCD', self['CHANMODES'][:4]))

    @property
    def MAXLIST(self):
        """Expose ``MAXLIST`` as a dict, if advertised by the server.

        This exposes information about maximums for combinations of modes::

            >>> isupport.MAXLIST
            {
                'beI': 100,
                'q': 50,
                'b': 50,
            }

        This attribute is not available if the server does not provide the
        right information, and accessing it will raise an
        :exc:`AttributeError`.

        .. seealso::

            https://modern.ircdocs.horse/#maxlist-parameter

        """
        if 'MAXLIST' not in self:
            raise AttributeError('MAXLIST')

        return dict(self['MAXLIST'])

    @property
    def PREFIX(self) -> dict[str, str]:
        """Expose ``PREFIX`` as a dict, if advertised by the server.

        This exposes information about the modes and nick prefixes used for
        user privileges in channels::

            >>> isupport.PREFIX
            {
                'q': '~',
                'a': '&',
                'o': '@',
                'h': '%',
                'v': '+',
            }

        Entries are in order of descending privilege.

        This attribute is not available if the server does not provide the
        right information, and accessing it will raise an
        :exc:`AttributeError`.

        .. seealso::

            https://modern.ircdocs.horse/#prefix-parameter

        """
        if 'PREFIX' not in self:
            raise AttributeError('PREFIX')

        return dict(self['PREFIX'])

    @property
    def TARGMAX(self):
        """Expose ``TARGMAX`` as a dict, if advertised by the server.

        This exposes information about the maximum number of arguments for
        each command::

            >>> isupport.TARGMAX
            {
                'JOIN': None,
                'PRIVMSG': 3,
                'WHOIS': 1,
            }
            >>> isupport['TARGMAX']  # internal representation
            (('JOIN', None), ('PRIVMSG', 3), ('WHOIS', 1))

        This attribute is not available if the server does not provide the
        right information, and accessing it will raise an
        :exc:`AttributeError`.

        The internal representation of ``TARGMAX`` is a tuple of 2-value
        tuples as seen above.

        .. seealso::

            https://modern.ircdocs.horse/#targmax-parameter

        """
        if 'TARGMAX' not in self:
            raise AttributeError('TARGMAX')

        # always return a dict if None or empty tuple
        return dict(self['TARGMAX'] or [])
