# coding=utf-8
"""Test for the ``sopel.plugins.handlers`` module."""
from __future__ import unicode_literals, absolute_import, print_function, division

import pytest

from sopel.plugins import handlers


MOCK_MODULE_CONTENT = """# coding=utf-8
\"\"\"module label
\"\"\"
"""


@pytest.fixture
def plugin_tmpfile(tmpdir):
    root = tmpdir.mkdir('loader_mods')
    mod_file = root.join('file_mod.py')
    mod_file.write(MOCK_MODULE_CONTENT)

    return mod_file


def test_get_label_pymodule():
    plugin = handlers.PyModulePlugin('coretasks', 'sopel')
    meta = plugin.get_meta_description()

    assert 'name' in meta
    assert 'label' in meta
    assert 'type' in meta
    assert 'source' in meta

    assert meta['name'] == 'coretasks'
    assert meta['label'] == 'coretasks module', 'Expecting default label'
    assert meta['type'] == handlers.PyModulePlugin.PLUGIN_TYPE
    assert meta['source'] == 'sopel.coretasks'


def test_get_label_pyfile(plugin_tmpfile):
    plugin = handlers.PyFilePlugin(plugin_tmpfile.strpath)
    meta = plugin.get_meta_description()

    assert meta['name'] == 'file_mod'
    assert meta['label'] == 'file_mod module', 'Expecting default label'
    assert meta['type'] == handlers.PyFilePlugin.PLUGIN_TYPE
    assert meta['source'] == plugin_tmpfile.strpath


def test_get_label_pyfile_loaded(plugin_tmpfile):
    plugin = handlers.PyFilePlugin(plugin_tmpfile.strpath)
    plugin.load()
    meta = plugin.get_meta_description()

    assert meta['name'] == 'file_mod'
    assert meta['label'] == 'module label'
    assert meta['type'] == handlers.PyFilePlugin.PLUGIN_TYPE
    assert meta['source'] == plugin_tmpfile.strpath
