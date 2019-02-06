# coding=utf-8
"""Tests for command handling"""
from __future__ import unicode_literals, absolute_import, print_function, division

from contextlib import contextmanager
import os

import pytest

from sopel import run_script, config


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


def test_find_config_local(tmpdir, config_dir):
    """Assert function retrieves configuration file from working dir first"""
    working_dir = tmpdir.mkdir("working")
    working_dir.join('local.cfg').write('')

    with cd(working_dir.strpath):
        found_config = run_script.find_config(config_dir.strpath, 'local.cfg')
        assert found_config == 'local.cfg'

        found_config = run_script.find_config(config_dir.strpath, 'local')
        assert found_config == config_dir.join('local').strpath


def test_find_config_default(tmpdir, config_dir):
    """Assert function retrieves configuration file from given config dir"""
    working_dir = tmpdir.mkdir("working")
    working_dir.join('local.cfg').write('')

    with cd(working_dir.strpath):
        found_config = run_script.find_config(config_dir.strpath, 'config')
        assert found_config == config_dir.join('config.cfg').strpath

        found_config = run_script.find_config(config_dir.strpath, 'config.cfg')
        assert found_config == config_dir.join('config.cfg').strpath


def test_find_config_extension(tmpdir, config_dir):
    """Assert function retrieves configuration file with the given extension"""
    working_dir = tmpdir.mkdir("working")
    working_dir.join('local.cfg').write('')

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


def test_get_running_pid(tmpdir):
    """Assert function retrieves an integer from a given filename"""
    pid_file = tmpdir.join('sopel.pid')
    pid_file.write('7814')

    result = run_script.get_running_pid(pid_file.strpath)
    assert result == 7814


def test_get_running_pid_not_integer(tmpdir):
    """Assert function returns None when the content is not an Integer"""
    pid_file = tmpdir.join('sopel.pid')
    pid_file.write('')

    result = run_script.get_running_pid(pid_file.strpath)
    assert result is None

    pid_file.write('abcdefg')

    result = run_script.get_running_pid(pid_file.strpath)
    assert result is None


def test_get_running_pid_no_file(tmpdir):
    """Assert function returns None when there is no such file"""
    pid_file = tmpdir.join('sopel.pid')

    result = run_script.get_running_pid(pid_file.strpath)
    assert result is None
