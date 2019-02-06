# coding=utf-8
"""Tests for sopel.cli.utils"""
from __future__ import unicode_literals, absolute_import, print_function, division

from contextlib import contextmanager
import os

import pytest

from sopel.cli.utils import enumerate_configs, find_config


@contextmanager
def cd(newdir):
    prevdir = os.getcwd()
    os.chdir(os.path.expanduser(newdir))
    try:
        yield
    finally:
        os.chdir(prevdir)


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


def test_find_config_local(tmpdir, config_dir):
    """Assert function retrieves configuration file from working dir first"""
    working_dir = tmpdir.mkdir("working")
    working_dir.join('local.cfg').write('')

    with cd(working_dir.strpath):
        found_config = find_config(config_dir.strpath, 'local.cfg')
        assert found_config == 'local.cfg'

        found_config = find_config(config_dir.strpath, 'local')
        assert found_config == config_dir.join('local').strpath


def test_find_config_default(tmpdir, config_dir):
    """Assert function retrieves configuration file from given config dir"""
    working_dir = tmpdir.mkdir("working")
    working_dir.join('local.cfg').write('')

    with cd(working_dir.strpath):
        found_config = find_config(config_dir.strpath, 'config')
        assert found_config == config_dir.join('config.cfg').strpath

        found_config = find_config(config_dir.strpath, 'config.cfg')
        assert found_config == config_dir.join('config.cfg').strpath


def test_find_config_extension(tmpdir, config_dir):
    """Assert function retrieves configuration file with the given extension"""
    working_dir = tmpdir.mkdir("working")
    working_dir.join('local.cfg').write('')

    with cd(working_dir.strpath):
        found_config = find_config(
            config_dir.strpath, 'extra', '.ini')
        assert found_config == config_dir.join('extra.ini').strpath
