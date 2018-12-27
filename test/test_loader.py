# coding=utf-8
"""Test for the ``sopel.loader`` module."""
import imp

import pytest

from sopel import loader, config


@pytest.fixture
def tmpconfig(tmpdir):
    conf_file = tmpdir.join('conf.ini')
    conf_file.write("\n".join([
        "[core]",
        "owner=testnick",
        ""
    ]))
    return config.Config(conf_file.strpath)


def test_get_module_description_good_file(tmpdir):
    root = tmpdir.mkdir('loader_mods')
    test_file = root.join('file_module.py')
    test_file.write('')

    filename = test_file.strpath
    assert loader.get_module_description(filename) == (
        'file_module', filename, imp.PY_SOURCE
    )


def test_get_module_description_bad_file_pyc(tmpdir):
    root = tmpdir.mkdir('loader_mods')
    test_file = root.join('file_module.pyc')
    test_file.write('')

    filename = test_file.strpath
    assert loader.get_module_description(filename) is None


def test_get_module_description_bad_file_no_ext(tmpdir):
    root = tmpdir.mkdir('loader_mods')
    test_file = root.join('file_module')
    test_file.write('')

    filename = test_file.strpath
    assert loader.get_module_description(filename) is None


def test_get_module_description_good_dir(tmpdir):
    root = tmpdir.mkdir('loader_mods')
    test_dir = root.mkdir('dir_package')
    test_dir.join('__init__.py').write('')

    filename = test_dir.strpath
    assert loader.get_module_description(filename) == (
        'dir_package', filename, imp.PKG_DIRECTORY
    )


def test_get_module_description_bad_dir_empty(tmpdir):
    root = tmpdir.mkdir('loader_mods')
    test_dir = root.mkdir('dir_package')

    filename = test_dir.strpath
    assert loader.get_module_description(filename) is None


def test_get_module_description_bad_dir_no_init(tmpdir):
    root = tmpdir.mkdir('loader_mods')
    test_dir = root.mkdir('dir_package')
    test_dir.join('no_init.py').write('')

    filename = test_dir.strpath
    assert loader.get_module_description(filename) is None


def test_clean_module_commands(tmpdir, tmpconfig):
    root = tmpdir.mkdir('loader_mods')
    mod_file = root.join('file_mod.py')
    mod_file.write("""
# coding=utf-8

import sopel.module


@sopel.module.commands("first")
def first_command(bot, trigger):
    pass


@sopel.module.commands("second")
def second_command(bot, trigger):
    pass


@sopel.module.interval(5)
def interval5s(bot):
    pass


@sopel.module.interval(10)
def interval10s(bot):
    pass


@sopel.module.url(r'.\\.example\\.com')
def example_url(bot):
    pass


def shutdown():
    pass


def ignored():
    pass

""")

    test_mod, _ = loader.load_module('file_mod', mod_file.strpath, imp.PY_SOURCE)
    callables, jobs, shutdowns, urls = loader.clean_module(
        test_mod, tmpconfig)

    assert len(callables) == 2
    assert test_mod.first_command in callables
    assert test_mod.second_command in callables
    assert len(jobs) == 2
    assert test_mod.interval5s in jobs
    assert test_mod.interval10s in jobs
    assert len(shutdowns)
    assert test_mod.shutdown in shutdowns
    assert len(urls) == 1
    assert test_mod.example_url in urls

    # ignored function is ignored
    assert test_mod.ignored not in callables
    assert test_mod.ignored not in jobs
    assert test_mod.ignored not in shutdowns
    assert test_mod.ignored not in urls
