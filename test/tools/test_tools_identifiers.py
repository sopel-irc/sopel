"""Tests for IRC Identifier"""
from __future__ import annotations

import pytest

from sopel.tools import identifiers


ASCII_PARAMS = (
    ('abcd', 'abcd'),
    ('ABCD', 'abcd'),
    ('abc[]d', 'abc[]d'),
    ('abc\\d', 'abc\\d'),
    ('abc~d', 'abc~d'),
    ('[A]B\\C~D', '[a]b\\c~d'),
    ('ÙNÏÇÔDÉ', 'ÙnÏÇÔdÉ'),
)
RFC1459_PARAMS = (
    ('abcd', 'abcd'),
    ('ABCD', 'abcd'),
    ('abc[]d', 'abc{}d'),
    ('abc\\d', 'abc|d'),
    ('abc~d', 'abc^d'),
    ('[A]B\\C~D', '{a}b|c^d'),
    ('ÙNÏÇÔDÉ', 'ÙnÏÇÔdÉ'),
)
RFC1459_STRICT_PARAMS = (
    ('abcd', 'abcd'),
    ('ABCD', 'abcd'),
    ('abc[]d', 'abc{}d'),
    ('abc\\d', 'abc|d'),
    ('abc~d', 'abc~d'),
    ('[A]B\\C~D', '{a}b|c~d'),
    ('ÙNÏÇÔDÉ', 'ÙnÏÇÔdÉ'),
)


@pytest.mark.parametrize('name, slug', ASCII_PARAMS)
def test_ascii_lower(name: str, slug: str):
    assert identifiers.ascii_lower(name) == slug


@pytest.mark.parametrize('name, slug', RFC1459_PARAMS)
def test_rfc1459_lower(name: str, slug: str):
    assert identifiers.rfc1459_lower(name) == slug


@pytest.mark.parametrize('name, slug', RFC1459_STRICT_PARAMS)
def test_rfc1459_strict_lower(name: str, slug: str):
    assert identifiers.rfc1459_strict_lower(name) == slug


def test_identifier_repr():
    assert "Identifier('ABCD[]')" == '%r' % identifiers.Identifier('ABCD[]')


@pytest.mark.parametrize('name, slug, gt, lt', (
    ('abcd', 'abcd', 'abcde', 'abc'),
    ('ABCD', 'abcd', 'ABCDE', 'abc'),
    ('abc[]d', 'abc{}d', 'abc[]de', 'abc{}'),
    ('abc\\d', 'abc|d', 'abc\\de', 'abc|'),
    ('abc~d', 'abc^d', 'abc~de', 'abc^'),
    ('[A]B\\C~D', '{a}b|c^d', '[A]B\\C~DE', '{a}b|c^'),
))
def test_identifier_default_casemapping(name, slug, gt, lt):
    identifier = identifiers.Identifier(name)
    assert slug == identifier.lower()
    assert slug == identifiers.Identifier._lower(name)
    assert slug == identifiers.Identifier._lower(identifier)
    assert hash(slug) == hash(identifier)

    # eq
    assert identifier == slug
    assert identifier == name
    assert identifier == identifiers.Identifier(slug)
    assert identifier == identifiers.Identifier(name)

    # not eq
    assert identifier != slug + 'f'
    assert identifier != name + 'f'
    assert identifier != identifiers.Identifier(slug + 'f')
    assert identifier != identifiers.Identifier(name + 'f')

    # gt(e)
    assert identifier >= slug
    assert identifier >= name
    assert identifier >= lt
    assert identifier > lt
    assert identifier >= identifiers.Identifier(lt)
    assert identifier > identifiers.Identifier(lt)

    # lt(e)
    assert identifier <= slug
    assert identifier <= name
    assert identifier <= gt
    assert identifier < gt
    assert identifier <= identifiers.Identifier(gt)
    assert identifier < identifiers.Identifier(gt)


@pytest.mark.parametrize('name, slug', ASCII_PARAMS)
def test_identifier_ascii_casemapping(name, slug):
    identifier = identifiers.Identifier(
        name,
        casemapping=identifiers.ascii_lower,
    )
    assert identifier.lower() == slug
    assert hash(identifier) == hash(slug)
    assert identifier == name
    assert identifier == slug
    assert slug == identifiers.Identifier._lower(identifier), (
        'Always use identifier.lower()',
    )


@pytest.mark.parametrize('name, slug', RFC1459_PARAMS)
def test_identifier_rfc1459_casemapping(name, slug):
    identifier = identifiers.Identifier(
        name,
        casemapping=identifiers.rfc1459_lower,
    )
    assert identifier.lower() == slug
    assert hash(identifier) == hash(slug)
    assert identifier == name
    assert identifier == slug
    assert slug == identifiers.Identifier._lower(identifier), (
        'Always use identifier.lower()',
    )


@pytest.mark.parametrize('name, slug', RFC1459_STRICT_PARAMS)
def test_identifier_rfc1459_strict_casemapping(name, slug):
    identifier = identifiers.Identifier(
        name,
        casemapping=identifiers.rfc1459_strict_lower,
    )
    assert identifier.lower() == slug
    assert hash(identifier) == hash(slug)
    assert identifier == name
    assert identifier == slug
    assert slug == identifiers.Identifier._lower(identifier), (
        'Always use identifier.lower()',
    )


@pytest.mark.parametrize('wrong_type', (
    None, 0, 10, 3.14, object()
))
def test_identifier_compare_invalid(wrong_type):
    identifier = identifiers.Identifier('xnaas')

    # you can compare equality (or lack thereof)
    assert not (identifier == wrong_type)
    assert identifier != wrong_type

    with pytest.raises(TypeError):
        identifier >= wrong_type

    with pytest.raises(TypeError):
        identifier > wrong_type

    with pytest.raises(TypeError):
        identifier <= wrong_type

    with pytest.raises(TypeError):
        identifier < wrong_type


@pytest.mark.parametrize('name, chantypes', (
    ('Exirel', identifiers.DEFAULT_CHANTYPES),
    ('@Exirel', identifiers.DEFAULT_CHANTYPES),
    ('+Exirel', ('#',)),
    ('!Exirel', ('#',)),
    ('&Exirel', ('#',)),
))
def test_identifier_is_nick(name, chantypes):
    assert identifiers.Identifier(name, chantypes=chantypes).is_nick()


@pytest.mark.parametrize('name, chantypes', (
    ('#Exirel', identifiers.DEFAULT_CHANTYPES),
    ('+Exirel', identifiers.DEFAULT_CHANTYPES),
    ('!Exirel', identifiers.DEFAULT_CHANTYPES),
    ('&Exirel', identifiers.DEFAULT_CHANTYPES),
    ('@Exirel', ('#', '@')),
))
def test_identifier_is_nick_channel(name, chantypes):
    assert not identifiers.Identifier(name, chantypes=chantypes).is_nick()


def test_identifier_is_nick_empty():
    assert not identifiers.Identifier('').is_nick()
    assert not identifiers.Identifier('', chantypes=('',)).is_nick()
