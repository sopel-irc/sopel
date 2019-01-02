# coding=utf-8
"""Tests for command handling"""
from __future__ import unicode_literals, absolute_import, print_function, division

from sopel import run_script


def test_enumerate_configs(tmpdir):
    """Assert function retrieves only .cfg files by default"""
    config_dir = tmpdir.mkdir("config")
    config_dir.join('config.cfg').write('')
    config_dir.join('extra.ini').write('')
    config_dir.join('module.cfg').write('')
    config_dir.join('README').write('')
    results = list(run_script.enumerate_configs(config_dir.strpath))

    assert 'config.cfg' in results
    assert 'module.cfg' in results
    assert 'extra.ini' not in results
    assert 'README' not in results
    assert len(results) == 2


def test_enumerate_configs_extension(tmpdir):
    """Assert function retrieves only files with the given extension"""
    config_dir = tmpdir.mkdir("config")
    config_dir.join('config.cfg').write('')
    config_dir.join('extra.ini').write('')
    config_dir.join('module.cfg').write('')
    config_dir.join('README').write('')
    results = list(run_script.enumerate_configs(config_dir.strpath, '.ini'))

    assert 'config.cfg' not in results
    assert 'module.cfg' not in results
    assert 'extra.ini' in results
    assert 'README' not in results
    assert len(results) == 1
