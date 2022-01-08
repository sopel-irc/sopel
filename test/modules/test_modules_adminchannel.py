"""Tests for Sopel's ``adminchannel`` plugin"""
from __future__ import annotations

import pytest

from sopel.modules import adminchannel


VALID_INPUTS = (
    ('justanick', 'justanick!*@*'),
    ('just-a.host', '*!*@just-a.host'),
    ('justauser@', '*!justauser@*'),
    ('someuser@just-a.host', '*!someuser@just-a.host'),
    ('someuser@dotlesshost', '*!someuser@dotlesshost'),
    ('somenick!someuser', 'somenick!someuser@*'),
    ('somenick!someuser@', 'somenick!someuser@*'),
    ('somenick!someuser@', 'somenick!someuser@*'),
    ('full!host@mask', 'full!host@mask'),
    ('full!mask@host.with.dots', 'full!mask@host.with.dots'),
    ('libera/style/cloak', '*!*@libera/style/cloak'),
)

INVALID_INPUTS = (
    'mask with whitespace',
    'cloak/with whitespace',
    'nick!auser@something with whitespace',
    'nick with spaces!user@host',
    'nick!user with spaces@host',
    'two!user!names@host',
    'two!user@host@names',
)


@pytest.mark.parametrize('raw, checked', VALID_INPUTS)
def test_configureHostMask(raw, checked):
    """Test the `configureHostMask` helper for functionality and compatibility."""
    assert adminchannel.configureHostMask(raw) == checked


@pytest.mark.parametrize('raw', INVALID_INPUTS)
def test_configureHostMask_invalid(raw):
    with pytest.raises(ValueError):
        adminchannel.configureHostMask(raw)
