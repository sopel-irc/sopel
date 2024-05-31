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


def test_entrypoint_plugin_get_version(plugin_tmpfile):
    # See gh-2593, an entrypoint plugin whose project/package names are not
    # equal raises an exception other than ValueError
    distrib_dir = os.path.dirname(plugin_tmpfile.strpath)
    sys.path.append(distrib_dir)

    # load the entry point
    try:
        entry_point = importlib.metadata.EntryPoint(
            'test_plugin', 'file_mod', 'sopel.plugins')
        plugin = handlers.EntryPointPlugin(entry_point)
        plugin.load()
        plugin.module.__package__ = "FAKEFAKEFAKE"
        plugin.get_version()
    finally:
        sys.path.remove(distrib_dir)
