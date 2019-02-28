# coding=utf-8
"""Tests for sopel.cli.utils"""
from __future__ import unicode_literals, absolute_import, print_function, division

import argparse
from contextlib import contextmanager
import os

import pytest

from sopel.cli.utils import enumerate_configs, find_config, add_common_arguments


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


def test_add_common_arguments():
    """Assert function adds the -c/--config option."""
    parser = argparse.ArgumentParser()
    add_common_arguments(parser)

    options = parser.parse_args([])
    assert hasattr(options, 'config')
    assert options.config is None

    options = parser.parse_args(['-c', 'test-short'])
    assert options.config == 'test-short'

    options = parser.parse_args(['--config', 'test-long'])
    assert options.config == 'test-long'


def test_add_common_arguments_subparser():
    """Assert function adds the -c/--config option on a subparser."""
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest='action')
    sub = subparsers.add_parser('sub')
    add_common_arguments(sub)

    options = parser.parse_args(['sub'])
    assert hasattr(options, 'config')
    assert options.config is None

    options = parser.parse_args(['sub', '-c', 'test-short'])
    assert options.config == 'test-short'

    options = parser.parse_args(['sub', '--config', 'test-long'])
    assert options.config == 'test-long'
