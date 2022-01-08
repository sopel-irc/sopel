"""Tests for core ``sopel.irc.isupport``"""
from __future__ import annotations

from collections import OrderedDict

import pytest

from sopel.irc import isupport


def test_isupport_apply():
    instance = isupport.ISupport()

    assert 'AWAYLEN' not in instance

    new = instance.apply(awaylen=50)

    assert 'AWAYLEN' not in instance
    assert 'AWAYLEN' in new
    assert new['AWAYLEN'] == 50

    new_removed = new.apply(**{'-AWAYLEN': None, 'NICKLEN': 31})

    assert 'AWAYLEN' not in instance
    assert 'AWAYLEN' in new
    assert 'AWAYLEN' not in new_removed
    assert new['AWAYLEN'] == 50, 'original instance must not be modified'

    assert 'NICKLEN' in new_removed
    assert new_removed['NICKLEN'] == 31


def test_isupport_apply_case_insensitive():
    """Test removed parameters are case-insensitive."""
    instance = isupport.ISupport()
    new = instance.apply(awaylen=50, NICKLEN=31, channellen=16)
    new_removed = new.apply(**{
        '-awaylen': None,
        '-NICKLEN': None,
        'channellen': 24,
    })

    assert 'AWAYLEN' in new
    assert 'AWAYLEN' not in new_removed

    assert 'NICKLEN' in new
    assert 'NICKLEN' not in new_removed

    assert 'CHANNELLEN' in new
    assert 'CHANNELLEN' in new_removed
    assert new['CHANNELLEN'] == 16
    assert new_removed['CHANNELLEN'] == 24

    new_removed_ci = new.apply(**{
        '-AWAYLEN': None,
        '-nicklen': None,
        'CHANNELLEN': 34,
    })

    assert 'AWAYLEN' in new
    assert 'AWAYLEN' not in new_removed_ci

    assert 'NICKLEN' in new
    assert 'NICKLEN' not in new_removed_ci

    assert 'CHANNELLEN' in new
    assert 'CHANNELLEN' in new_removed_ci
    assert new['CHANNELLEN'] == 16
    assert new_removed_ci['CHANNELLEN'] == 34


def test_isupport_removed_parameter():
    """Test removed parameters are ignored."""
    instance = isupport.ISupport(**{'-AWAYLEN': 50})

    assert 'AWAYLEN' not in instance
    assert '-AWAYLEN' not in instance


def test_isupport_get():
    """Test parameter access through the ``get`` method."""
    instance = isupport.ISupport(AWAYLEN=50)

    assert instance.get('AWAYLEN') == 50
    assert instance.get('AWAYLEN', 20) == 50, (
        'Default must be ignored if name exists')
    assert instance.get('AWAYLEN', default=10) == 50, (
        'Default must be ignored if name exists')
    assert instance.get('UNKNOWN') is None
    assert instance.get('UNKNOWN', 20) == 20, (
        'Default must be used if name does not exist')
    assert instance.get('UNKNOWN', default=10) == 10, (
        'Default must be used if name does not exist')


def test_isupport_getitem():
    """Test basic parameter access."""
    instance = isupport.ISupport(AWAYLEN=50)

    assert 'AWAYLEN' in instance
    assert 'UNKNOWN' not in instance
    assert instance['AWAYLEN'] == 50

    with pytest.raises(KeyError):
        instance['UNKNOWN']


def test_isupport_getitem_case_insensitive():
    """Test access to parameters is case insensitive."""
    instance = isupport.ISupport(awaylen=50)

    assert 'AWAYLEN' in instance
    assert 'awaylen' in instance
    assert instance['AWAYLEN'] == 50
    assert instance['awaylen'] == 50


def test_isupport_getattr():
    """Test using ISUPPORT parameters as read-only attributes."""
    instance = isupport.ISupport(awaylen=50)

    assert hasattr(instance, 'AWAYLEN')
    assert not hasattr(instance, 'awaylen'), 'attributes are ALL_UPPERCASE'
    assert not hasattr(instance, 'UNKNOWN')

    assert instance.AWAYLEN == 50

    # you can't set attributes yourself
    with pytest.raises(AttributeError):
        instance.AWAYLEN = 20

    with pytest.raises(AttributeError):
        instance.awaylen = 20

    with pytest.raises(AttributeError):
        instance.UNKNOWN = 'not possible'


def test_isupport_setitem():
    """Test you can't set a key."""
    instance = isupport.ISupport(awaylen=50)

    with pytest.raises(TypeError):
        instance['AWAYLEN'] = 10


def test_isupport_chanlimit():
    instance = isupport.ISupport(chanlimit=(('#', 50), ('$', 10)))
    assert '#' in instance.CHANLIMIT
    assert '$' in instance.CHANLIMIT
    assert instance.CHANLIMIT['#'] == 50
    assert instance.CHANLIMIT['$'] == 10

    with pytest.raises(AttributeError):
        instance.CHANLIMIT = 'something'


def test_isupport_chanlimit_undefined():
    instance = isupport.ISupport()

    assert not hasattr(instance, 'CHANLIMIT')

    with pytest.raises(AttributeError):
        instance.CHANLIMIT


def test_isupport_chanmodes():
    instance = isupport.ISupport(chanmodes=('b', 'k', 'l', 'imnpst', tuple()))

    assert 'A' in instance.CHANMODES
    assert 'B' in instance.CHANMODES
    assert 'C' in instance.CHANMODES
    assert 'D' in instance.CHANMODES

    with pytest.raises(AttributeError):
        instance.CHANMODES = 'something'


def test_isupport_chanmodes_undefined():
    instance = isupport.ISupport()

    assert set(instance.CHANMODES.keys()) == set("ABCD")
    assert set(instance.CHANMODES.values()) == {""}


def test_isupport_maxlist():
    instance = isupport.ISupport(maxlist=(('Z', 10), ('beI', 25)))
    assert 'Z' in instance.MAXLIST
    assert 'beI' in instance.MAXLIST
    assert instance.MAXLIST['Z'] == 10
    assert instance.MAXLIST['beI'] == 25

    with pytest.raises(AttributeError):
        instance.MAXLIST = 'something'


def test_isupport_maxlist_undefined():
    instance = isupport.ISupport()

    assert not hasattr(instance, 'MAXLIST')

    with pytest.raises(AttributeError):
        instance.MAXLIST


def test_isupport_prefix():
    instance = isupport.ISupport(prefix=(('o', '@'), ('v', '+')))
    assert 'o' in instance.PREFIX
    assert 'v' in instance.PREFIX
    assert instance.PREFIX['o'] == '@'
    assert instance.PREFIX['v'] == '+'

    with pytest.raises(AttributeError):
        instance.PREFIX = 'something'


def test_isupport_prefix_undefined():
    instance = isupport.ISupport()

    assert not hasattr(instance, 'PREFIX')

    with pytest.raises(AttributeError):
        instance.PREFIX


def test_isupport_targmax():
    instance = isupport.ISupport(
        targmax=(('JOIN', None), ('PRIVMSG', 3), ('WHOIS', 1)))
    assert 'JOIN' in instance.TARGMAX
    assert 'PRIVMSG' in instance.TARGMAX
    assert 'WHOIS' in instance.TARGMAX
    assert instance.TARGMAX['JOIN'] is None
    assert instance.TARGMAX['PRIVMSG'] == 3
    assert instance.TARGMAX['WHOIS'] == 1

    with pytest.raises(AttributeError):
        instance.TARGMAX = 'something'


def test_isupport_targmax_optional():
    instance = isupport.ISupport(targmax=None)

    assert instance.TARGMAX == {}


def test_isupport_targmax_undefined():
    instance = isupport.ISupport()

    assert not hasattr(instance, 'TARGMAX')

    with pytest.raises(AttributeError):
        instance.TARGMAX


# these parameters with basic parsing
VALID_PARSE_VALUE = (
    ('AWAYLEN=50', ('AWAYLEN', 50)),
    ('CASEMAPPING=ascii', ('CASEMAPPING', 'ascii')),
    ('CHANNELLEN=31', ('CHANNELLEN', 31)),
    ('CHANTYPES=#~', ('CHANTYPES', ('#', '~'))),
    ('EXCEPTS=d', ('EXCEPTS', 'd')),
    ('HOSTLEN=64', ('HOSTLEN', 64)),
    ('INVEX=J', ('INVEX', 'J')),
    ('KICKLEN=307', ('KICKLEN', 307)),
    ('MAXTARGETS=5', ('MAXTARGETS', 5)),
    ('MODES=5', ('MODES', 5)),
    ('NETWORK=Freenode', ('NETWORK', 'Freenode')),
    ('NICKLEN=31', ('NICKLEN', 31)),
    ('SILENCE=5', ('SILENCE', 5)),
    ('STATUSMSG', ('STATUSMSG', None)),
    ('STATUSMSG=ABCD', ('STATUSMSG', ('A', 'B', 'C', 'D'))),
    ('TOPICLEN=5', ('TOPICLEN', 5)),
    ('USERLEN=5', ('USERLEN', 5)),
)


@pytest.mark.parametrize('arg, expected', VALID_PARSE_VALUE)
def test_parse_parameter(arg, expected):
    key, value = isupport.parse_parameter(arg)

    assert (key, value) == expected


# these parameters don't require a value
VALID_PARSE_OPTIONAL = (
    ('CHANTYPES', ('CHANTYPES', None)),
    ('EXCEPTS', ('EXCEPTS', 'e')),
    ('INVEX', ('INVEX', 'I')),
    ('MAXTARGETS', ('MAXTARGETS', None)),
    ('MODES', ('MODES', None)),
    ('SILENCE', ('SILENCE', None)),
)


@pytest.mark.parametrize('arg, expected', VALID_PARSE_OPTIONAL)
def test_parse_parameter_optional(arg, expected):
    key, value = isupport.parse_parameter(arg)

    assert (key, value) == expected


# these parameters don't accept value
VALID_PARSE_NO_VALUE = (
    ('SAFELIST', ('SAFELIST', None)),
)


@pytest.mark.parametrize('arg, expected', VALID_PARSE_NO_VALUE)
def test_parse_parameter_no_value(arg, expected):
    key, value = isupport.parse_parameter(arg)

    assert (key, value) == expected


# single-letter parameters parsing must raise when more than one character
INVALID_PARSE_SINGLE_LETTER = (
    'EXCEPTS=ed',
    'EXCEPTS=edoui',
    'INVEX=IJ',
    'INVEX=IJKLMNOP',
)


@pytest.mark.parametrize('arg', INVALID_PARSE_SINGLE_LETTER)
def test_parse_parameter_single_letter_raise(arg):
    with pytest.raises(ValueError):
        isupport.parse_parameter(arg)


# every parameter can be removed
VALID_PARSE_REMOVED = (
    '-AWAYLEN',
    '-CASEMAPPING',
    '-CHANLIMIT',
    '-CHANMODES',
    '-CHANNELLEN',
    '-CHANTYPES',
    '-ELIST',
    '-EXCEPTS',
    '-EXTBAN',
    '-HOSTLEN',
    '-INVEX',
    '-KICKLEN',
    '-MAXLIST',
    '-MAXTARGETS',
    '-MODES',
    '-NETWORK',
    '-NICKLEN',
    '-PREFIX',
    '-SAFELIST',
    '-SILENCE',
    '-STATUSMSG',
    '-TARGMAX',
    '-TOPICLEN',
    '-USERLEN',
)


@pytest.mark.parametrize('arg', VALID_PARSE_REMOVED)
def test_parse_parameter_removed(arg):
    key, value = isupport.parse_parameter(arg)

    assert value is None
    assert key == arg


def test_parse_parameter_chanlimit_single():
    key, value = isupport.parse_parameter('CHANLIMIT=#:50')

    assert key == 'CHANLIMIT'
    assert value == (('#', 50),)


def test_parse_parameter_chanlimit_many():
    key, value = isupport.parse_parameter('CHANLIMIT=#:50,$:10')

    assert key == 'CHANLIMIT'
    assert value == (('#', 50), ('$', 10))


def test_parse_parameter_chanlimit_limit_optional():
    key, value = isupport.parse_parameter('CHANLIMIT=#:50,$:10,~:')

    assert key == 'CHANLIMIT'
    assert value == (('#', 50), ('$', 10), ('~', None))


def test_parse_parameter_chanmode():
    key, value = isupport.parse_parameter('CHANMODES=b,k,l,imnpst')

    assert key == 'CHANMODES'
    assert value == ('b', 'k', 'l', 'imnpst', tuple())


def test_parse_parameter_chanmode_extra():
    key, value = isupport.parse_parameter('CHANMODES=b,k,l,imnpst,bkl')

    assert key == 'CHANMODES'
    assert value == ('b', 'k', 'l', 'imnpst', ('bkl',))


def test_parse_parameter_chanmode_extra_many():
    key, value = isupport.parse_parameter('CHANMODES=b,k,l,imnpst,bkl,imnpst')

    assert key == 'CHANMODES'
    assert value == ('b', 'k', 'l', 'imnpst', ('bkl', 'imnpst'))


def test_parse_parameter_chanmode_raise():
    with pytest.raises(ValueError):
        isupport.parse_parameter('CHANMODES=b,k,l')


def test_parse_parameter_elist():
    key, value = isupport.parse_parameter('ELIST=C')

    assert key == 'ELIST'
    assert value == ('C',)


def test_parse_parameter_elist_many():
    key, value = isupport.parse_parameter('ELIST=CMNTU')

    assert key == 'ELIST'
    assert value == ('C', 'M', 'N', 'T', 'U')


def test_parse_parameter_elist_many_sorted():
    key, value = isupport.parse_parameter('ELIST=MTCUN')

    assert key == 'ELIST'
    assert value == ('C', 'M', 'N', 'T', 'U')


def test_parse_parameter_extban():
    key, value = isupport.parse_parameter('EXTBAN=~,qjncrRa')

    assert key == 'EXTBAN'
    assert value == ('~', ('R', 'a', 'c', 'j', 'n', 'q', 'r'))


def test_parse_parameter_extban_no_prefix():
    key, value = isupport.parse_parameter('EXTBAN=,ABCNOcjmp')

    assert key == 'EXTBAN'
    assert value == (None, ('A', 'B', 'C', 'N', 'O', 'c', 'j', 'm', 'p'))


def test_parse_parameter_extban_invalid():
    with pytest.raises(ValueError):
        isupport.parse_parameter('EXTBAN=ABCNOcjmp')


def test_parse_parameter_maxlist():
    key, value = isupport.parse_parameter('MAXLIST=beI:25')

    assert key == 'MAXLIST'
    assert value == (('beI', 25),)


def test_parse_parameter_maxlist_many():
    key, value = isupport.parse_parameter('MAXLIST=b:60,e:40,I:50')

    assert key == 'MAXLIST'
    assert value == (('I', 50), ('b', 60), ('e', 40))


def test_parse_parameter_maxlist_many_mixed():
    key, value = isupport.parse_parameter('MAXLIST=beI:25,Z:10')

    assert key == 'MAXLIST'
    assert value == (('Z', 10), ('beI', 25))


def test_parse_parameter_maxlist_many_mixed_override():
    key, value = isupport.parse_parameter('MAXLIST=b:10,beI:25,Z:10,I:40')

    assert key == 'MAXLIST'
    assert value == (('I', 40), ('Z', 10), ('b', 10), ('beI', 25))


def test_parse_parameter_maxlist_invalid():
    with pytest.raises(ValueError):
        isupport.parse_parameter('MAXLIST=b:60,e,I:50')


def test_parse_parameter_prefix():
    key, value = isupport.parse_parameter('PREFIX=(ov)@+')

    assert key == 'PREFIX'
    assert value == (('o', '@'), ('v', '+'))


def test_parse_parameter_prefix_invalid_format():
    with pytest.raises(ValueError):
        isupport.parse_parameter('PREFIX=ov@+')

    with pytest.raises(ValueError):
        isupport.parse_parameter('PREFIX=(ov)@')

    with pytest.raises(ValueError):
        isupport.parse_parameter('PREFIX=(o)@+')


def test_parse_parameter_prefix_order_parser():
    """Ensure PREFIX order is maintained through parser.

    https://modern.ircdocs.horse/#prefix-parameter
    """
    key, value = isupport.parse_parameter('PREFIX=(qov)~@+')

    assert value == (('q', '~'), ('o', '@'), ('v', '+'))


def test_parse_parameter_prefix_order_property():
    """Ensure PREFIX order is maintained in property."""
    instance = isupport.ISupport()

    key, value = isupport.parse_parameter('PREFIX=(qov)~@+')
    new = instance.apply(
        prefix=value,
    )

    assert new.PREFIX == OrderedDict((('q', '~'), ('o', '@'), ('v', '+')))
    assert tuple(new.PREFIX.keys()) == ('q', 'o', 'v')


def test_parse_parameter_targmax():
    key, value = isupport.parse_parameter('TARGMAX=PRIVMSG:3')

    assert key == 'TARGMAX'
    assert value == (('PRIVMSG', 3),)


def test_parse_parameter_targmax_optional():
    key, value = isupport.parse_parameter('TARGMAX=')

    assert key == 'TARGMAX'
    assert value == tuple()


def test_parse_parameter_targmax_many():
    key, value = isupport.parse_parameter('TARGMAX=PRIVMSG:3,WHOIS:1')

    assert key == 'TARGMAX'
    assert value == (('PRIVMSG', 3), ('WHOIS', 1))


def test_parse_parameter_targmax_many_optional():
    key, value = isupport.parse_parameter('TARGMAX=PRIVMSG:3,JOIN:,WHOIS:1')

    assert key == 'TARGMAX'
    assert value == (('JOIN', None), ('PRIVMSG', 3), ('WHOIS', 1))
