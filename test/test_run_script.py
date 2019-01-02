# coding=utf-8
"""Tests for command handling"""
from __future__ import unicode_literals, absolute_import, print_function, division

from contextlib import contextmanager
import os

from sopel import run_script, config


@contextmanager
def cd(newdir):
    prevdir = os.getcwd()
    os.chdir(os.path.expanduser(newdir))
    try:
        yield
    finally:
        os.chdir(prevdir)


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


def test_find_config_local(tmpdir):
    """Assert function retrieves configuration file from working dir first"""
    working_dir = tmpdir.mkdir("working")
    working_dir.join('local.cfg').write('')
    config_dir = tmpdir.mkdir("config")

    with cd(working_dir.strpath):
        found_config = run_script.find_config(config_dir.strpath, 'local.cfg')
        assert found_config == 'local.cfg'

        found_config = run_script.find_config(config_dir.strpath, 'local')
        assert found_config == config_dir.join('local').strpath


def test_find_config_default(tmpdir):
    """Assert function retrieves configuration file from given config dir"""
    working_dir = tmpdir.mkdir("working")
    working_dir.join('local.cfg').write('')
    config_dir = tmpdir.mkdir("config")
    config_dir.join('config.cfg').write('')
    config_dir.join('extra.ini').write('')
    config_dir.join('module.cfg').write('')
    config_dir.join('README').write('')

    with cd(working_dir.strpath):
        found_config = run_script.find_config(config_dir.strpath, 'config')
        assert found_config == config_dir.join('config.cfg').strpath

        found_config = run_script.find_config(config_dir.strpath, 'config.cfg')
        assert found_config == config_dir.join('config.cfg').strpath


def test_find_config_extension(tmpdir):
    """Assert function retrieves configuration file with the given extension"""
    working_dir = tmpdir.mkdir("working")
    working_dir.join('local.cfg').write('')
    config_dir = tmpdir.mkdir("config")
    config_dir.join('config.cfg').write('')
    config_dir.join('extra.ini').write('')
    config_dir.join('module.cfg').write('')
    config_dir.join('README').write('')

    with cd(working_dir.strpath):
        found_config = run_script.find_config(
            config_dir.strpath, 'extra', '.ini')
        assert found_config == config_dir.join('extra.ini').strpath


def test_get_configuration(tmpdir):
    """Assert function returns a Sopel ``Config`` object"""
    working_dir = tmpdir.mkdir("working")
    working_dir.join('default.cfg').write('\n'.join([
        '[core]',
        'owner = TestName'
    ]))

    parser = run_script.build_parser()
    options = parser.parse_args(['-c', 'default.cfg'])

    with cd(working_dir.strpath):
        result = run_script.get_configuration(options)
        assert isinstance(result, config.Config)
        assert result.core.owner == 'TestName'


def test_get_pid_filename_default():
    """Assert function returns the default filename from given ``pid_dir``"""
    pid_dir = '/pid'
    parser = run_script.build_parser()
    options = parser.parse_args([])

    result = run_script.get_pid_filename(options, pid_dir)
    assert result == pid_dir + '/sopel.pid'


def test_get_pid_filename_named():
    """Assert function returns a specific filename when config (with extension) is set"""
    pid_dir = '/pid'
    parser = run_script.build_parser()

    # With extension
    options = parser.parse_args(['-c', 'test.cfg'])

    result = run_script.get_pid_filename(options, pid_dir)
    assert result == pid_dir + '/sopel-test.pid'

    # Without extension
    options = parser.parse_args(['-c', 'test'])

    result = run_script.get_pid_filename(options, pid_dir)
    assert result == pid_dir + '/sopel-test.pid'


def test_get_pid_filename_ext_not_cfg():
    """Assert function keeps the config file extension when it is not cfg"""
    pid_dir = '/pid'
    parser = run_script.build_parser()
    options = parser.parse_args(['-c', 'test.ini'])

    result = run_script.get_pid_filename(options, pid_dir)
    assert result == pid_dir + '/sopel-test.ini.pid'
