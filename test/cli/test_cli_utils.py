# coding=utf-8
"""Tests for sopel.cli.utils"""
from __future__ import unicode_literals, absolute_import, print_function, division

import pytest

from sopel.cli.utils import enumerate_configs


@pytest.fixture
def config_dir(tmpdir):
    """Pytest fixture used to generate a temporary configuration directory"""
    test_dir = tmpdir.mkdir("config")
    test_dir.join('config.cfg').write('')
    test_dir.join('extra.ini').write('')
    test_dir.join('module.cfg').write('')
    test_dir.join('README').write('')

    return test_dir


def test_enumerate_configs(config_dir):
    """Assert function retrieves only .cfg files by default"""
    results = list(enumerate_configs(config_dir.strpath))

    assert 'config.cfg' in results
    assert 'module.cfg' in results
    assert 'extra.ini' not in results
    assert 'README' not in results
    assert len(results) == 2


def test_enumerate_configs_extension(config_dir):
    """Assert function retrieves only files with the given extension"""
    results = list(enumerate_configs(config_dir.strpath, '.ini'))

    assert 'config.cfg' not in results
    assert 'module.cfg' not in results
    assert 'extra.ini' in results
    assert 'README' not in results
    assert len(results) == 1
