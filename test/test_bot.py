# coding=utf-8
"""Tests for core ``sopel.bot`` module"""
from __future__ import unicode_literals, absolute_import, print_function, division

import pytest

from sopel import bot, config, plugins


@pytest.fixture
def tmpconfig(tmpdir):
    conf_file = tmpdir.join('conf.ini')
    conf_file.write("\n".join([
        "[core]",
        "owner=testnick",
        "nick = TestBot",
        "enable = coretasks"
        ""
    ]))
    return config.Config(conf_file.strpath)


def test_remove_plugin_unknown_plugin(tmpconfig):
    sopel = bot.Sopel(tmpconfig, daemon=False)
    sopel.scheduler.stop()
    sopel.scheduler.join(timeout=10)

    plugin = plugins.handlers.PyModulePlugin('admin', 'sopel.modules')
    with pytest.raises(plugins.exceptions.PluginNotRegistered):
        sopel.remove_plugin(plugin, [], [], [], [])


def test_remove_plugin_unregistered_plugin(tmpconfig):
    sopel = bot.Sopel(tmpconfig, daemon=False)
    sopel.scheduler.stop()
    sopel.scheduler.join(timeout=10)
    plugin = sopel._plugins.get('coretasks')

    assert plugin is not None, 'coretasks should always be loaded'

    # Unregister the plugin
    plugin.unregister(sopel)
    # And now it must raise an exception
    with pytest.raises(plugins.exceptions.PluginNotRegistered):
        sopel.remove_plugin(plugin, [], [], [], [])


def test_reload_plugin_unregistered_plugin(tmpconfig):
    sopel = bot.Sopel(tmpconfig, daemon=False)
    sopel.scheduler.stop()
    sopel.scheduler.join(timeout=10)
    plugin = sopel._plugins.get('coretasks')

    assert plugin is not None, 'coretasks should always be loaded'

    # Unregister the plugin
    plugin.unregister(sopel)
    # And now it must raise an exception
    with pytest.raises(plugins.exceptions.PluginNotRegistered):
        sopel.reload_plugin(plugin.name)
