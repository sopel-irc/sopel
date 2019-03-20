# coding=utf-8
"""Tests for command handling"""
from __future__ import unicode_literals, absolute_import, print_function, division

import argparse
from contextlib import contextmanager
import os

import pytest

from sopel import config
from sopel.cli.run import (
    build_parser,
    get_configuration,
    get_pid_filename,
    get_running_pid
)


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


def test_build_parser_legacy():
    """Assert parser's namespace exposes legacy's options (default values)"""
    parser = build_parser()
    options = parser.parse_args(['legacy'])

    assert isinstance(options, argparse.Namespace)
    assert hasattr(options, 'config')
    assert hasattr(options, 'daemonize')
    assert hasattr(options, 'quiet')
    assert hasattr(options, 'quit')
    assert hasattr(options, 'kill')
    assert hasattr(options, 'restart')
    assert hasattr(options, 'version')
    assert hasattr(options, 'version_legacy')
    assert hasattr(options, 'wizard')
    assert hasattr(options, 'mod_wizard')
    assert hasattr(options, 'list_configs')

    assert options.config is None
    assert options.daemonize is False
    assert options.quiet is False
    assert options.quit is False
    assert options.kill is False
    assert options.restart is False
    assert options.version is False
    assert options.version_legacy is False
    assert options.wizard is False
    assert options.mod_wizard is False
    assert options.list_configs is False


def test_build_parser_legacy_config():
    parser = build_parser()
    options = parser.parse_args(['legacy', '-c', 'custom'])
    assert options.config == 'custom'

    options = parser.parse_args(['legacy', '--config', 'custom'])
    assert options.config == 'custom'


def test_build_parser_legacy_daemonize():
    parser = build_parser()
    options = parser.parse_args(['legacy', '-d'])
    assert options.daemonize is True

    options = parser.parse_args(['legacy', '--fork'])
    assert options.daemonize is True


def test_build_parser_legacy_quiet():
    parser = build_parser()
    options = parser.parse_args(['legacy', '--quiet'])
    assert options.quiet is True


def test_build_parser_legacy_quit():
    parser = build_parser()
    options = parser.parse_args(['legacy', '-q'])
    assert options.quit is True

    options = parser.parse_args(['legacy', '--quit'])
    assert options.quit is True


def test_build_parser_legacy_kill():
    parser = build_parser()
    options = parser.parse_args(['legacy', '-k'])
    assert options.kill is True

    options = parser.parse_args(['legacy', '--kill'])
    assert options.kill is True


def test_build_parser_legacy_restart():
    parser = build_parser()
    options = parser.parse_args(['legacy', '-r'])
    assert options.restart is True

    options = parser.parse_args(['legacy', '--restart'])
    assert options.restart is True


def test_build_parser_legacy_version():
    parser = build_parser()
    options = parser.parse_args(['legacy', '-v'])
    assert options.version is False
    assert options.version_legacy is True

    options = parser.parse_args(['legacy', '-V'])
    assert options.version is True
    assert options.version_legacy is False

    options = parser.parse_args(['legacy', '--version'])
    assert options.version is True
    assert options.version_legacy is False


def test_build_parser_legacy_wizard():
    parser = build_parser()
    options = parser.parse_args(['legacy', '-w'])
    assert options.wizard is True
    assert options.mod_wizard is False

    options = parser.parse_args(['legacy', '--configure-all'])
    assert options.wizard is True
    assert options.mod_wizard is False

    options = parser.parse_args(['legacy', '--configure-modules'])
    assert options.wizard is False
    assert options.mod_wizard is True


def test_build_parser_legacy_list_config():
    parser = build_parser()
    options = parser.parse_args(['legacy', '-l'])
    assert options.list_configs is True

    options = parser.parse_args(['legacy', '--list'])
    assert options.list_configs is True


def test_build_parser_start():
    """Assert parser's namespace exposes start's options (default values)"""
    parser = build_parser()
    options = parser.parse_args(['start'])

    assert isinstance(options, argparse.Namespace)
    assert hasattr(options, 'config')
    assert hasattr(options, 'daemonize')
    assert hasattr(options, 'quiet')

    assert options.config is None
    assert options.daemonize is False
    assert options.quiet is False


def test_build_parser_start_config():
    parser = build_parser()

    options = parser.parse_args(['start', '-c', 'custom'])
    assert options.config == 'custom'

    options = parser.parse_args(['start', '--config', 'custom'])
    assert options.config == 'custom'


def test_build_parser_start_daemonize():
    parser = build_parser()

    options = parser.parse_args(['start', '-d'])
    assert options.daemonize is True

    options = parser.parse_args(['start', '--fork'])
    assert options.daemonize is True


def test_build_parser_start_quiet():
    parser = build_parser()

    options = parser.parse_args(['start', '--quiet'])
    assert options.quiet is True


def test_build_parser_stop():
    """Assert parser's namespace exposes stop's options (default values)"""
    parser = build_parser()
    options = parser.parse_args(['stop'])

    assert isinstance(options, argparse.Namespace)
    assert hasattr(options, 'config')
    assert hasattr(options, 'kill')
    assert hasattr(options, 'quiet')

    assert options.config is None
    assert options.kill is False
    assert options.quiet is False


def test_build_parser_stop_config():
    parser = build_parser()

    options = parser.parse_args(['stop', '-c', 'custom'])
    assert options.config == 'custom'

    options = parser.parse_args(['stop', '--config', 'custom'])
    assert options.config == 'custom'


def test_build_parser_stop_kill():
    parser = build_parser()

    options = parser.parse_args(['stop', '-k'])
    assert options.kill is True

    options = parser.parse_args(['stop', '--kill'])
    assert options.kill is True


def test_build_parser_stop_quiet():
    parser = build_parser()

    options = parser.parse_args(['stop', '--quiet'])
    assert options.quiet is True


def test_build_parser_restart():
    """Assert parser's namespace exposes restart's options (default values)"""
    parser = build_parser()
    options = parser.parse_args(['restart'])

    assert isinstance(options, argparse.Namespace)
    assert hasattr(options, 'config')
    assert hasattr(options, 'quiet')

    assert options.config is None
    assert options.quiet is False


def test_build_parser_restart_config():
    parser = build_parser()

    options = parser.parse_args(['restart', '-c', 'custom'])
    assert options.config == 'custom'

    options = parser.parse_args(['restart', '--config', 'custom'])
    assert options.config == 'custom'


def test_build_parser_restart_quiet():
    parser = build_parser()

    options = parser.parse_args(['restart', '--quiet'])
    assert options.quiet is True


def test_build_parser_configure():
    """Assert parser's namespace exposes configure's options (default values)"""
    parser = build_parser()
    options = parser.parse_args(['configure'])

    assert isinstance(options, argparse.Namespace)
    assert hasattr(options, 'config')
    assert hasattr(options, 'modules')

    assert options.config is None
    assert options.modules is False


def test_build_parser_configure_config():
    parser = build_parser()

    options = parser.parse_args(['configure', '-c', 'custom'])
    assert options.config == 'custom'

    options = parser.parse_args(['configure', '--config', 'custom'])
    assert options.config == 'custom'


def test_build_parser_configure_modules():
    parser = build_parser()

    options = parser.parse_args(['configure', '--modules'])
    assert options.modules is True


def test_get_configuration(tmpdir):
    """Assert function returns a Sopel ``Config`` object"""
    working_dir = tmpdir.mkdir("working")
    working_dir.join('default.cfg').write('\n'.join([
        '[core]',
        'owner = TestName'
    ]))

    parser = build_parser()
    options = parser.parse_args(['legacy', '-c', 'default.cfg'])

    with cd(working_dir.strpath):
        result = get_configuration(options)
        assert isinstance(result, config.Config)
        assert result.core.owner == 'TestName'


def test_get_pid_filename_default():
    """Assert function returns the default filename from given ``pid_dir``"""
    pid_dir = '/pid'
    parser = build_parser()
    options = parser.parse_args(['legacy'])

    result = get_pid_filename(options, pid_dir)
    assert result == pid_dir + '/sopel.pid'


def test_get_pid_filename_named():
    """Assert function returns a specific filename when config (with extension) is set"""
    pid_dir = '/pid'
    parser = build_parser()

    # With extension
    options = parser.parse_args(['legacy', '-c', 'test.cfg'])

    result = get_pid_filename(options, pid_dir)
    assert result == pid_dir + '/sopel-test.pid'

    # Without extension
    options = parser.parse_args(['legacy', '-c', 'test'])

    result = get_pid_filename(options, pid_dir)
    assert result == pid_dir + '/sopel-test.pid'


def test_get_pid_filename_ext_not_cfg():
    """Assert function keeps the config file extension when it is not cfg"""
    pid_dir = '/pid'
    parser = build_parser()
    options = parser.parse_args(['legacy', '-c', 'test.ini'])

    result = get_pid_filename(options, pid_dir)
    assert result == pid_dir + '/sopel-test.ini.pid'


def test_get_running_pid(tmpdir):
    """Assert function retrieves an integer from a given filename"""
    pid_file = tmpdir.join('sopel.pid')
    pid_file.write('7814')

    result = get_running_pid(pid_file.strpath)
    assert result == 7814


def test_get_running_pid_not_integer(tmpdir):
    """Assert function returns None when the content is not an Integer"""
    pid_file = tmpdir.join('sopel.pid')
    pid_file.write('')

    result = get_running_pid(pid_file.strpath)
    assert result is None

    pid_file.write('abcdefg')

    result = get_running_pid(pid_file.strpath)
    assert result is None


def test_get_running_pid_no_file(tmpdir):
    """Assert function returns None when there is no such file"""
    pid_file = tmpdir.join('sopel.pid')

    result = get_running_pid(pid_file.strpath)
    assert result is None
