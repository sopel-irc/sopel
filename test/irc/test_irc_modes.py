from __future__ import annotations

import pytest

from sopel.irc.modes import (
    ModeParser,
    ModeTypeImproperlyConfigured,
    ModeTypeUnknown,
    ParamRequired,
    parse_modestring,
)

ADDED = True
REMOVED = False
REQUIRED = True
NOT_REQUIRED = False
PREFIX = True
NOT_PREFIX = False


@pytest.mark.parametrize('modestring, result', (
    ('a', (('a', ADDED),)),
    ('+a', (('a', ADDED),)),
    ('-a', (('a', REMOVED),)),
    ('+a-b', (('a', ADDED), ('b', REMOVED))),
    ('-a+b', (('a', REMOVED), ('b', ADDED))),
    ('+ab-cd', (('a', ADDED), ('b', ADDED), ('c', REMOVED), ('d', REMOVED))),
    ('+a-b+c-d', (('a', ADDED), ('b', REMOVED), ('c', ADDED), ('d', REMOVED))),
))
def test_parse_modestring(modestring, result):
    assert tuple(parse_modestring(modestring)) == result


@pytest.mark.parametrize('mode, letter', (
    ('b', 'A'),
    ('c', 'A'),
    ('e', 'B'),
    ('f', 'B'),
    ('g', 'B'),
))
def test_modemessage_get_mode_type(mode, letter):
    modemessage = ModeParser({
        'A': tuple('bc'),
        'B': tuple('efg'),
    }, {})

    assert modemessage.get_mode_type(mode) == letter


def test_modemessage_get_mode_type_empty():
    modemessage = ModeParser({}, {})

    # common mode
    with pytest.raises(ModeTypeUnknown):
        modemessage.get_mode_type('b')

    # common privilege
    with pytest.raises(ModeTypeUnknown):
        modemessage.get_mode_type('v')


def test_modemessage_get_mode_type_unknown():
    modemessage = ModeParser({
        'A': tuple('bc'),
        'B': tuple('efg'),
    }, {})

    # unknown mode
    with pytest.raises(ModeTypeUnknown):
        modemessage.get_mode_type('z')

    # common privilege
    with pytest.raises(ModeTypeUnknown):
        modemessage.get_mode_type('v')


@pytest.mark.parametrize('mode, is_added, result', (
    # X: always
    ('b', ADDED, ('X', REQUIRED)),
    ('b', REMOVED, ('X', REQUIRED)),
    ('c', ADDED, ('X', REQUIRED)),
    ('c', REMOVED, ('X', REQUIRED)),
    # Y: added only
    ('e', ADDED, ('Y', REQUIRED)),
    ('e', REMOVED, ('Y', NOT_REQUIRED)),
    ('f', ADDED, ('Y', REQUIRED)),
    ('f', REMOVED, ('Y', NOT_REQUIRED)),
    ('g', ADDED, ('Y', REQUIRED)),
    ('g', REMOVED, ('Y', NOT_REQUIRED)),
    # Z: removed only
    ('i', ADDED, ('Z', NOT_REQUIRED)),
    ('i', REMOVED, ('Z', REQUIRED)),
    ('j', ADDED, ('Z', NOT_REQUIRED)),
    ('j', REMOVED, ('Z', REQUIRED)),
    # T: never
    ('k', ADDED, ('T', NOT_REQUIRED)),
    ('k', REMOVED, ('T', NOT_REQUIRED)),
    ('l', ADDED, ('T', NOT_REQUIRED)),
    ('l', REMOVED, ('T', NOT_REQUIRED)),
    ('m', ADDED, ('T', NOT_REQUIRED)),
    ('m', REMOVED, ('T', NOT_REQUIRED)),
))
def test_modemessage_get_mode_info(mode, is_added, result):
    modemessage = ModeParser({
        'X': tuple('bc'),
        'Y': tuple('efg'),
        'Z': tuple('ij'),
        'T': tuple('klm'),
    }, {
        'X': ParamRequired.ALWAYS,
        'Y': ParamRequired.ADDED,
        'Z': ParamRequired.REMOVED,
        'T': ParamRequired.NEVER,
    })

    assert modemessage.get_mode_info(mode, is_added) == result


def test_modemessage_get_mode_info_empty():
    modemessage = ModeParser(chanmodes={}, type_params={}, privileges=set())

    with pytest.raises(ModeTypeUnknown):
        modemessage.get_mode_info('b', ADDED)

    with pytest.raises(ModeTypeUnknown):
        modemessage.get_mode_info('b', REMOVED)


@pytest.mark.parametrize('privilege', ('v', 'h', 'a', 'q', 'o', 'y', 'Y'))
def test_modemessage_get_mode_info_privileges(privilege):
    modemessage = ModeParser(chanmodes={}, type_params={})

    with pytest.raises(ModeTypeUnknown):
        modemessage.get_mode_info(privilege, ADDED)

    with pytest.raises(ModeTypeUnknown):
        modemessage.get_mode_info(privilege, REMOVED)


@pytest.mark.parametrize('privilege', ('v', 'h', 'a', 'q', 'o', 'y', 'Y'))
def test_modemessage_get_mode_info_empty_privileges_config(privilege):
    modemessage = ModeParser(chanmodes={}, type_params={}, privileges=set())

    with pytest.raises(ModeTypeUnknown):
        modemessage.get_mode_info(privilege, ADDED)

    with pytest.raises(ModeTypeUnknown):
        modemessage.get_mode_info(privilege, REMOVED)


def test_modemessage_get_mode_info_no_param_config():
    modemessage = ModeParser({
        'X': tuple('bc'),
        'Y': tuple('efg'),
        'Z': tuple('ij'),
        'T': tuple('klm'),
    }, {})

    with pytest.raises(ModeTypeImproperlyConfigured):
        modemessage.get_mode_info('b', ADDED)

    with pytest.raises(ModeTypeImproperlyConfigured):
        modemessage.get_mode_info('b', REMOVED)


def test_modemessage_get_mode_info_custom_privileges():
    modemessage = ModeParser(chanmodes={}, type_params={}, privileges=set('b'))
    with pytest.raises(ModeTypeUnknown):
        modemessage.get_mode_info('b', ADDED)

    with pytest.raises(ModeTypeUnknown):
        modemessage.get_mode_info('b', REMOVED)


def test_modemessage_parse_modestring_default():
    modeparser = ModeParser()
    result = modeparser.parse(
        '+Oimn-psrt+lk-beI' + '+Z',
        tuple('abcdef'))
    assert result.modes == (
        ('D', 'O', ADDED, None),
        ('D', 'i', ADDED, None),
        ('D', 'm', ADDED, None),
        ('D', 'n', ADDED, None),
        ('D', 'p', REMOVED, None),
        ('D', 's', REMOVED, None),
        ('D', 'r', REMOVED, None),
        ('D', 't', REMOVED, None),
        ('C', 'l', ADDED, 'a'),
        ('B', 'k', ADDED, 'b'),
        ('A', 'b', REMOVED, 'c'),
        ('A', 'e', REMOVED, 'd'),
        ('A', 'I', REMOVED, 'e'),
    )
    assert result.ignored_modes == (('Z', ADDED),)
    assert not result.privileges
    assert result.leftover_params == ('f',)


def test_modemessage_parse_modestring_single_mode():
    modemessage = ModeParser({
        'X': tuple('bc'),
        'Y': tuple('efg'),
        'Z': tuple('ij'),
        'T': tuple('klm'),
    }, {
        'X': ParamRequired.ALWAYS,
        'Y': ParamRequired.ADDED,
        'Z': ParamRequired.REMOVED,
        'T': ParamRequired.NEVER,
    })

    # X: always a parameter
    result = modemessage.parse('+b', ('Arg1',))
    assert result.modes == (('X', 'b', ADDED, 'Arg1'),)
    assert not result.ignored_modes
    assert not result.privileges
    assert not result.leftover_params

    result = modemessage.parse('-b', ('Arg1',))
    assert result.modes == (('X', 'b', REMOVED, 'Arg1'),)
    assert not result.ignored_modes
    assert not result.privileges
    assert not result.leftover_params

    # Y: parameter when added only
    result = modemessage.parse('+e', ('Arg1',))
    assert result.modes == (('Y', 'e', ADDED, 'Arg1'),)
    assert not result.ignored_modes
    assert not result.privileges
    assert not result.leftover_params

    result = modemessage.parse('-e', ('Arg1',))
    assert result.modes == (('Y', 'e', REMOVED, None),)
    assert not result.ignored_modes
    assert not result.privileges
    assert result.leftover_params == ('Arg1',)

    # Z: parameter when removed only
    result = modemessage.parse('+i', ('Arg1',))
    assert result.modes == (('Z', 'i', ADDED, None),)
    assert not result.ignored_modes
    assert not result.privileges
    assert result.leftover_params == ('Arg1',)

    result = modemessage.parse('-i', ('Arg1',))
    assert result.modes == (('Z', 'i', REMOVED, 'Arg1'),)
    assert not result.ignored_modes
    assert not result.privileges
    assert not result.leftover_params

    # T: no parameter
    result = modemessage.parse('+k', ('Arg1',))
    assert result.modes == (('T', 'k', ADDED, None),)
    assert not result.ignored_modes
    assert not result.privileges
    assert result.leftover_params == ('Arg1',)

    result = modemessage.parse('-k', ('Arg1',))
    assert result.modes == (('T', 'k', REMOVED, None),)
    assert not result.ignored_modes
    assert not result.privileges
    assert result.leftover_params == ('Arg1',)

    # Common privilege
    result = modemessage.parse('+v', ('Arg1',))
    assert not result.modes
    assert not result.ignored_modes
    assert result.privileges == (('v', ADDED, 'Arg1'),)
    assert not result.leftover_params

    result = modemessage.parse('-v', ('Arg1',))
    assert not result.modes
    assert not result.ignored_modes
    assert result.privileges == (('v', REMOVED, 'Arg1'),)
    assert not result.leftover_params


def test_modemessage_parse_modestring_multi_mode_add_only():
    modemessage = ModeParser({
        'X': tuple('bc'),
        'Y': tuple('efg'),
        'Z': tuple('ij'),
        'T': tuple('klm'),
    }, {
        'X': ParamRequired.ALWAYS,
        'Y': ParamRequired.ADDED,
        'Z': ParamRequired.REMOVED,
        'T': ParamRequired.NEVER,
    })

    # modes only
    result = modemessage.parse('+beik', ('Arg1', 'Arg2'))
    assert result.modes == (
        ('X', 'b', ADDED, 'Arg1'),
        ('Y', 'e', ADDED, 'Arg2'),
        ('Z', 'i', ADDED, None),
        ('T', 'k', ADDED, None),
    )
    assert not result.ignored_modes
    assert not result.privileges
    assert not result.leftover_params

    # privileges only
    result = modemessage.parse('+vo', ('Arg1', 'Arg2'))
    assert not result.modes
    assert not result.ignored_modes
    assert result.privileges == (
        ('v', ADDED, 'Arg1'),
        ('o', ADDED, 'Arg2'),
    )
    assert not result.leftover_params

    # modes & privileges
    result = modemessage.parse(
        '+bveoik', ('Arg1', 'Arg2', 'Arg3', 'Arg4'))
    assert result.modes == (
        ('X', 'b', ADDED, 'Arg1'),
        ('Y', 'e', ADDED, 'Arg3'),
        ('Z', 'i', ADDED, None),
        ('T', 'k', ADDED, None),
    )
    assert not result.ignored_modes
    assert result.privileges == (
        ('v', ADDED, 'Arg2'),
        ('o', ADDED, 'Arg4'),
    )
    assert not result.leftover_params


def test_modemessage_parse_modestring_multi_mode_remove_only():
    modemessage = ModeParser({
        'X': tuple('bc'),
        'Y': tuple('efg'),
        'Z': tuple('ij'),
        'T': tuple('klm'),
    }, {
        'X': ParamRequired.ALWAYS,
        'Y': ParamRequired.ADDED,
        'Z': ParamRequired.REMOVED,
        'T': ParamRequired.NEVER,
    })

    # modes only
    result = modemessage.parse('-beik', ('Arg1', 'Arg2'))
    assert result.modes == (
        ('X', 'b', REMOVED, 'Arg1'),
        ('Y', 'e', REMOVED, None),
        ('Z', 'i', REMOVED, 'Arg2'),
        ('T', 'k', REMOVED, None),
    )
    assert not result.ignored_modes
    assert not result.privileges
    assert not result.leftover_params

    # privileges only
    result = modemessage.parse('-vo', ('Arg1', 'Arg2'))
    assert not result.modes
    assert not result.ignored_modes
    assert result.privileges == (
        ('v', REMOVED, 'Arg1'),
        ('o', REMOVED, 'Arg2'),
    )
    assert not result.leftover_params

    # modes & privileges
    result = modemessage.parse(
        '-bveoik', ('Arg1', 'Arg2', 'Arg3', 'Arg4'))
    assert result.modes == (
        ('X', 'b', REMOVED, 'Arg1'),
        ('Y', 'e', REMOVED, None),
        ('Z', 'i', REMOVED, 'Arg4'),
        ('T', 'k', REMOVED, None),
    )
    assert not result.ignored_modes
    assert result.privileges == (
        ('v', REMOVED, 'Arg2'),
        ('o', REMOVED, 'Arg3'),
    )
    assert not result.leftover_params


def test_modemessage_parse_modestring_multi_mode_mixed_add_remove():
    modemessage = ModeParser({
        'X': tuple('bc'),
        'Y': tuple('efg'),
        'Z': tuple('ij'),
        'T': tuple('klm'),
    }, {
        'X': ParamRequired.ALWAYS,
        'Y': ParamRequired.ADDED,
        'Z': ParamRequired.REMOVED,
        'T': ParamRequired.NEVER,
    })

    # added first
    result = modemessage.parse(
        '+bveik-cofjl', ('Arg1', 'Arg2', 'Arg3', 'Arg4', 'Arg5', 'Arg6'))
    assert result.modes == (
        ('X', 'b', ADDED, 'Arg1'),
        ('Y', 'e', ADDED, 'Arg3'),
        ('Z', 'i', ADDED, None),
        ('T', 'k', ADDED, None),
        ('X', 'c', REMOVED, 'Arg4'),
        ('Y', 'f', REMOVED, None),
        ('Z', 'j', REMOVED, 'Arg6'),
        ('T', 'l', REMOVED, None),
    )
    assert not result.ignored_modes
    assert result.privileges == (
        ('v', ADDED, 'Arg2'),
        ('o', REMOVED, 'Arg5'),
    )
    assert not result.leftover_params

    # removed first
    result = modemessage.parse(
        '-cofjl+bveik', ('Arg1', 'Arg2', 'Arg3', 'Arg4', 'Arg5', 'Arg6'))
    assert result.modes == (
        ('X', 'c', REMOVED, 'Arg1'),
        ('Y', 'f', REMOVED, None),
        ('Z', 'j', REMOVED, 'Arg3'),
        ('T', 'l', REMOVED, None),
        ('X', 'b', ADDED, 'Arg4'),
        ('Y', 'e', ADDED, 'Arg6'),
        ('Z', 'i', ADDED, None),
        ('T', 'k', ADDED, None),
    )
    assert not result.ignored_modes
    assert result.privileges == (
        ('o', REMOVED, 'Arg2'),
        ('v', ADDED, 'Arg5'),
    )
    assert not result.leftover_params

    # mixed add/remove
    result = modemessage.parse(
        '+bve-cof+ik-jl', ('Arg1', 'Arg2', 'Arg3', 'Arg4', 'Arg5', 'Arg6'))
    assert result.modes == (
        ('X', 'b', ADDED, 'Arg1'),
        ('Y', 'e', ADDED, 'Arg3'),
        ('X', 'c', REMOVED, 'Arg4'),
        ('Y', 'f', REMOVED, None),
        ('Z', 'i', ADDED, None),
        ('T', 'k', ADDED, None),
        ('Z', 'j', REMOVED, 'Arg6'),
        ('T', 'l', REMOVED, None),
    )
    assert not result.ignored_modes
    assert result.privileges == (
        ('v', ADDED, 'Arg2'),
        ('o', REMOVED, 'Arg5'),
    )
    assert not result.leftover_params


def test_modemessage_parse_modestring_leftover_params():
    modemessage = ModeParser({
        'X': tuple('bc'),
        'Y': tuple('efg'),
        'Z': tuple('ij'),
        'T': tuple('klm'),
    }, {
        'X': ParamRequired.ALWAYS,
        'Y': ParamRequired.ADDED,
        'Z': ParamRequired.REMOVED,
        'T': ParamRequired.NEVER,
    })

    # Single mode
    result = modemessage.parse(
        '+b', ('Arg1', 'Arg2'))
    assert result.modes == (
        ('X', 'b', ADDED, 'Arg1'),
    )
    assert not result.ignored_modes
    assert not result.privileges
    assert result.leftover_params == ('Arg2',)

    # Single privilege
    result = modemessage.parse(
        '+v', ('Arg1', 'Arg2'))
    assert not result.modes
    assert not result.ignored_modes
    assert result.privileges == (
        ('v', ADDED, 'Arg1'),
    )
    assert result.leftover_params == ('Arg2',)

    # Multi modes
    result = modemessage.parse(
        '+be-fi+jk-l', ('Arg1', 'Arg2', 'Arg3', 'Arg4'))
    assert result.modes == (
        ('X', 'b', ADDED, 'Arg1'),
        ('Y', 'e', ADDED, 'Arg2'),
        ('Y', 'f', REMOVED, None),
        ('Z', 'i', REMOVED, 'Arg3'),
        ('Z', 'j', ADDED, None),
        ('T', 'k', ADDED, None),
        ('T', 'l', REMOVED, None),
    )
    assert not result.ignored_modes
    assert not result.privileges
    assert result.leftover_params == ('Arg4',)


def test_modemessage_parse_modestring_ignored_modes():
    modemessage = ModeParser({
        'X': tuple('bc'),
        'Y': tuple('efg'),
        'Z': tuple('ij'),
        'T': tuple('klm'),
    }, {
        'X': ParamRequired.ALWAYS,
        'Y': ParamRequired.ADDED,
        'Z': ParamRequired.REMOVED,
        'T': ParamRequired.NEVER,
    })

    # Single mode
    result = modemessage.parse('+B', ('Arg1',))
    assert not result.modes
    assert result.ignored_modes == (('B', ADDED),)
    assert not result.privileges
    assert result.leftover_params == ('Arg1',)

    # Multi modes/privileges
    result = modemessage.parse(
        '+bv+B-o', ('Arg1', 'Arg2', 'Arg3'))
    assert result.modes == (
        ('X', 'b', ADDED, 'Arg1'),
    )
    assert result.ignored_modes == (
        ('B', ADDED),
        ('o', REMOVED),
    )
    assert result.privileges == (
        ('v', ADDED, 'Arg2'),
    )
    assert result.leftover_params == ('Arg3',)


def test_modemessage_parse_modestring_no_params():
    modemessage = ModeParser({
        'X': tuple('bc'),
        'Y': tuple('efg'),
        'Z': tuple('ij'),
        'T': tuple('klm'),
    }, {
        'X': ParamRequired.ALWAYS,
        'Y': ParamRequired.ADDED,
        'Z': ParamRequired.REMOVED,
        'T': ParamRequired.NEVER,
    })

    # Single mode
    result = modemessage.parse('+b', tuple())
    assert not result.modes
    assert result.ignored_modes == (('b', ADDED),)
    assert not result.privileges
    assert not result.leftover_params

    result = modemessage.parse('-b', tuple())
    assert not result.modes
    assert result.ignored_modes == (('b', REMOVED),)
    assert not result.privileges
    assert not result.leftover_params

    # Single privilege
    result = modemessage.parse('+v', tuple())
    assert not result.modes
    assert result.ignored_modes == (('v', ADDED),)
    assert not result.privileges
    assert not result.leftover_params

    result = modemessage.parse('-v', tuple())
    assert not result.modes
    assert result.ignored_modes == (('v', REMOVED),)
    assert not result.privileges
    assert not result.leftover_params

    # Mixed multi modes/privileges
    result = modemessage.parse('+b-v', tuple())
    assert not result.modes
    assert result.ignored_modes == (('b', ADDED), ('v', REMOVED),)
    assert not result.privileges
    assert not result.leftover_params


def test_modemessage_parse_modestring_missing_params():
    modemessage = ModeParser({
        'X': tuple('bc'),
        'Y': tuple('efg'),
        'Z': tuple('ij'),
        'T': tuple('klm'),
    }, {
        'X': ParamRequired.ALWAYS,
        'Y': ParamRequired.ADDED,
        'Z': ParamRequired.REMOVED,
        'T': ParamRequired.NEVER,
    })

    # Modes only
    result = modemessage.parse('+bc', ('Arg1',))
    assert result.modes == (
        ('X', 'b', ADDED, 'Arg1'),
    )
    assert result.ignored_modes == (('c', ADDED),)
    assert not result.privileges
    assert not result.leftover_params

    result = modemessage.parse('-bc', ('Arg1',))
    assert result.modes == (
        ('X', 'b', REMOVED, 'Arg1'),
    )
    assert result.ignored_modes == (('c', REMOVED),)
    assert not result.privileges
    assert not result.leftover_params

    # Prefixes only
    result = modemessage.parse('+vo', ('Arg1',))
    assert not result.modes
    assert result.ignored_modes == (('o', ADDED),)
    assert result.privileges == (
        ('v', ADDED, 'Arg1'),
    )
    assert not result.leftover_params

    result = modemessage.parse('-vo', ('Arg1',))
    assert not result.modes
    assert result.ignored_modes == (('o', REMOVED),)
    assert result.privileges == (
        ('v', REMOVED, 'Arg1'),
    )
    assert not result.leftover_params

    # Mixed modes/privileges
    result = modemessage.parse('+bv-co', ('Arg1', 'Arg2', 'Arg3'))
    assert result.modes == (
        ('X', 'b', ADDED, 'Arg1'),
        ('X', 'c', REMOVED, 'Arg3'),
    )
    assert result.ignored_modes == (('o', REMOVED),)
    assert result.privileges == (
        ('v', ADDED, 'Arg2'),
    )
    assert not result.leftover_params
