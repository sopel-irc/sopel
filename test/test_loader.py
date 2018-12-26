# coding=utf-8
"""Test for the ``sopel.loader`` module."""
import imp

from sopel import loader


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
