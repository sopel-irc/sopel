"""Tests for the ``sopel.plugins.handlers`` module."""
from __future__ import annotations

import importlib.metadata
import os
import sys

import pytest

from sopel.plugins import handlers


MOCK_MODULE_CONTENT = """
\"\"\"plugin label
\"\"\"
"""


@pytest.fixture
def plugin_tmpfile(tmpdir):
    root = tmpdir.mkdir('loader_mods')
    mod_file = root.join('file_mod.py')
    mod_file.write(MOCK_MODULE_CONTENT)

    return mod_file


@pytest.fixture
def plugin_tmpfile_nodoc(tmpdir):
    root = tmpdir.mkdir('loader_mods')
    mod_file = root.join('file_mod_nodoc.py')
    mod_file.write("")

    return mod_file


def test_get_label_pymodule():
    plugin = handlers.PyModulePlugin('coretasks', 'sopel')
    meta = plugin.get_meta_description()

    assert 'name' in meta
    assert 'label' in meta
    assert 'type' in meta
    assert 'source' in meta

    assert meta['name'] == 'coretasks'
    assert meta['label'] == 'coretasks plugin', 'Expecting default label'
    assert meta['type'] == handlers.PyModulePlugin.PLUGIN_TYPE
    assert meta['source'] == 'sopel.coretasks'


def test_get_label_pyfile(plugin_tmpfile):
    plugin = handlers.PyFilePlugin(plugin_tmpfile.strpath)
    meta = plugin.get_meta_description()

    assert meta['name'] == 'file_mod'
    assert meta['label'] == 'file_mod plugin', 'Expecting default label'
    assert meta['type'] == handlers.PyFilePlugin.PLUGIN_TYPE
    assert meta['source'] == plugin_tmpfile.strpath


def test_get_label_pyfile_loaded(plugin_tmpfile):
    plugin = handlers.PyFilePlugin(plugin_tmpfile.strpath)
    plugin.load()
    meta = plugin.get_meta_description()

    assert meta['name'] == 'file_mod'
    assert meta['label'] == 'plugin label'
    assert meta['type'] == handlers.PyFilePlugin.PLUGIN_TYPE
    assert meta['source'] == plugin_tmpfile.strpath


def test_get_label_pyfile_loaded_nodoc(plugin_tmpfile_nodoc):
    plugin = handlers.PyFilePlugin(plugin_tmpfile_nodoc.strpath)
    plugin.load()
    meta = plugin.get_meta_description()

    assert meta['name'] == 'file_mod_nodoc'
    assert meta['label'] == 'file_mod_nodoc plugin', 'Expecting default label'
    assert meta['type'] == handlers.PyFilePlugin.PLUGIN_TYPE
    assert meta['source'] == plugin_tmpfile_nodoc.strpath


def test_get_label_entrypoint(plugin_tmpfile):
    # set up for manual load/import
    distrib_dir = os.path.dirname(plugin_tmpfile.strpath)
    sys.path.append(distrib_dir)

    # load the entry point
    try:
        entry_point = importlib.metadata.EntryPoint(
            'test_plugin', 'file_mod', 'sopel.plugins')
        plugin = handlers.EntryPointPlugin(entry_point)
        plugin.load()
    finally:
        sys.path.remove(distrib_dir)

    meta = plugin.get_meta_description()
    assert meta['name'] == 'test_plugin'
    assert meta['label'] == 'plugin label'
    assert meta['type'] == handlers.EntryPointPlugin.PLUGIN_TYPE
    assert meta['source'] == 'test_plugin = file_mod'


MOCK_PARENT_MODULE = """
from sopel import plugin

from .sub import foo


@plugin.command('mock')
def mock(bot, trigger):
    bot.say(foo)
"""

MOCK_SUB_MODULE = """
foo = 'bar baz'
"""


@pytest.fixture
def plugin_folder(tmp_path):
    root = tmp_path / 'test_folder_plugin'
    root.mkdir()

    parent = root / '__init__.py'
    with open(parent, 'w') as f:
        f.write(MOCK_PARENT_MODULE)

    submodule = root / 'sub.py'
    with open(submodule, 'w') as f:
        f.write(MOCK_SUB_MODULE)

    return str(root)


def test_folder_plugin_imports(plugin_folder):
    """Ensure submodule imports work as expected in folder plugins.

    Regression test for https://github.com/sopel-irc/sopel/issues/2619
    """
    handler = handlers.PyFilePlugin(plugin_folder)
    handler.load()
    assert handler.module.foo == 'bar baz'


def test_get_version_entrypoint_package_does_not_match(plugin_tmpfile):
    # See gh-2593, wherein an entrypoint plugin whose project/package names
    # are not equal raised an exception that propagated too far
    distrib_dir = os.path.dirname(plugin_tmpfile.strpath)
    sys.path.append(distrib_dir)

    try:
        entry_point = importlib.metadata.EntryPoint(
            'test_plugin', 'file_mod', 'sopel.plugins')
        plugin = handlers.EntryPointPlugin(entry_point)
        plugin.load()
        plugin.module.__package__ = "FAKEFAKEFAKE"
        # Under gh-2593, this call raises a PackageNotFound error
        assert plugin.get_version() is None
    finally:
        sys.path.remove(distrib_dir)
