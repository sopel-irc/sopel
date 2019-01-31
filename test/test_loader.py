# coding=utf-8
"""Test for the ``sopel.loader`` module."""
import imp
import inspect
import os

import pytest

from sopel import loader, config, module


MOCK_MODULE_CONTENT = """# coding=utf-8
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


@sopel.module.event('TOPIC')
def on_topic_command(bot):
    pass


def shutdown():
    pass


def ignored():
    pass

"""


@pytest.fixture
def func():
    """Pytest fixture to get a function that will return True all the time"""
    def bot_command():
        """Test callable defined as a pytest fixture."""
        return True
    return bot_command


@pytest.fixture
def tmpconfig(tmpdir):
    conf_file = tmpdir.join('conf.ini')
    conf_file.write("\n".join([
        "[core]",
        "owner=testnick",
        "nick = TestBot",
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
    mod_file.write(MOCK_MODULE_CONTENT)

    test_mod, _ = loader.load_module(
        'file_mod', mod_file.strpath, imp.PY_SOURCE)
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


def test_clean_callable_default(tmpconfig, func):
    loader.clean_callable(func, tmpconfig)

    # Default values
    assert hasattr(func, 'unblockable')
    assert func.unblockable is False
    assert hasattr(func, 'priority')
    assert func.priority == 'medium'
    assert hasattr(func, 'thread')
    assert func.thread is True
    assert hasattr(func, 'rate')
    assert func.rate == 0
    assert hasattr(func, 'channel_rate')
    assert func.rate == 0
    assert hasattr(func, 'global_rate')
    assert func.global_rate == 0
    assert hasattr(func, 'event')
    assert func.event == ['PRIVMSG']

    # Not added by default
    assert not hasattr(func, 'rule')
    assert not hasattr(func, 'commands')
    assert not hasattr(func, 'intents')


def test_clean_callable_event(tmpconfig, func):
    setattr(func, 'event', ['low', 'UP', 'MiXeD'])
    loader.clean_callable(func, tmpconfig)

    assert hasattr(func, 'event')
    assert func.event == ['LOW', 'UP', 'MIXED']


def test_clean_callable_event_string(tmpconfig, func):
    setattr(func, 'event', 'some')
    loader.clean_callable(func, tmpconfig)

    assert hasattr(func, 'event')
    assert func.event == ['SOME']


def test_clean_callable_rule(tmpconfig, func):
    setattr(func, 'rule', [r'abc'])
    loader.clean_callable(func, tmpconfig)

    assert hasattr(func, 'rule')
    assert len(func.rule) == 1

    # Test the regex is compiled properly
    regex = func.rule[0]
    assert regex.match('abc')
    assert regex.match('abcd')
    assert not regex.match('efg')


def test_clean_callable_rule_string(tmpconfig, func):
    setattr(func, 'rule', r'abc')
    loader.clean_callable(func, tmpconfig)

    assert hasattr(func, 'rule')
    assert len(func.rule) == 1

    # Test the regex is compiled properly
    regex = func.rule[0]
    assert regex.match('abc')
    assert regex.match('abcd')
    assert not regex.match('efg')


def test_clean_callable_rule_nick(tmpconfig, func):
    """Assert ``$nick`` in a rule will match ``TestBot: `` or ``TestBot, ``."""
    setattr(func, 'rule', [r'$nickhello'])
    loader.clean_callable(func, tmpconfig)

    assert hasattr(func, 'rule')
    assert len(func.rule) == 1

    # Test the regex is compiled properly
    regex = func.rule[0]
    assert regex.match('TestBot: hello')
    assert regex.match('TestBot, hello')
    assert not regex.match('TestBot not hello')


def test_clean_callable_rule_nickname(tmpconfig, func):
    """Assert ``$nick`` in a rule will match ``TestBot``."""
    setattr(func, 'rule', [r'$nickname\s+hello'])
    loader.clean_callable(func, tmpconfig)

    assert hasattr(func, 'rule')
    assert len(func.rule) == 1

    # Test the regex is compiled properly
    regex = func.rule[0]
    assert regex.match('TestBot hello')
    assert not regex.match('TestBot not hello')


def test_clean_callable_nickname_command(tmpconfig, func):
    setattr(func, 'nickname_commands', ['hello!'])
    loader.clean_callable(func, tmpconfig)

    assert hasattr(func, 'nickname_commands')
    assert len(func.nickname_commands) == 1
    assert func.nickname_commands == ['hello!']
    assert hasattr(func, 'rule')
    assert len(func.rule) == 1

    regex = func.rule[0]
    assert regex.match('TestBot hello!')
    assert regex.match('TestBot, hello!')
    assert regex.match('TestBot: hello!')
    assert not regex.match('TestBot not hello')


def test_clean_callable_events(tmpconfig, func):
    setattr(func, 'event', ['TOPIC'])
    loader.clean_callable(func, tmpconfig)

    assert hasattr(func, 'event')
    assert func.event == ['TOPIC']

    setattr(func, 'event', ['TOPIC', 'JOIN'])
    loader.clean_callable(func, tmpconfig)

    assert hasattr(func, 'event')
    assert func.event == ['TOPIC', 'JOIN']

    setattr(func, 'event', ['TOPIC', 'join', 'Nick'])
    loader.clean_callable(func, tmpconfig)

    assert hasattr(func, 'event')
    assert func.event == ['TOPIC', 'JOIN', 'NICK']


def test_clean_callable_events_basetring(tmpconfig, func):
    setattr(func, 'event', 'topic')
    loader.clean_callable(func, tmpconfig)

    assert hasattr(func, 'event')
    assert func.event == ['TOPIC']

    setattr(func, 'event', 'JOIN')
    loader.clean_callable(func, tmpconfig)

    assert hasattr(func, 'event')
    assert func.event == ['JOIN']


def test_clean_callable_example(tmpconfig, func):
    module.commands('test')(func)
    module.example('.test hello')(func)

    loader.clean_callable(func, tmpconfig)

    assert hasattr(func, '_docs')
    assert len(func._docs) == 1
    assert 'test' in func._docs

    docs = func._docs['test']
    assert len(docs) == 2
    assert docs[0] == inspect.cleandoc(func.__doc__).splitlines()
    assert docs[1] == '.test hello'


def test_clean_callable_example_multi_commands(tmpconfig, func):
    module.commands('test')(func)
    module.commands('unit')(func)
    module.example('.test hello')(func)

    loader.clean_callable(func, tmpconfig)

    assert hasattr(func, '_docs')
    assert len(func._docs) == 2
    assert 'test' in func._docs
    assert 'unit' in func._docs

    test_docs = func._docs['test']
    unit_docs = func._docs['unit']
    assert len(test_docs) == 2
    assert test_docs == unit_docs

    assert test_docs[0] == inspect.cleandoc(func.__doc__).splitlines()
    assert test_docs[1] == '.test hello'


def test_clean_callable_example_first_only(tmpconfig, func):
    module.commands('test')(func)
    module.example('.test hello')(func)
    module.example('.test bonjour')(func)

    loader.clean_callable(func, tmpconfig)

    assert len(func._docs) == 1
    assert 'test' in func._docs

    docs = func._docs['test']
    assert len(docs) == 2
    assert docs[0] == inspect.cleandoc(func.__doc__).splitlines()
    assert docs[1] == '.test hello'


def test_clean_callable_example_first_only_multi_commands(tmpconfig, func):
    module.commands('test')(func)
    module.commands('unit')(func)
    module.example('.test hello')(func)
    module.example('.test bonjour')(func)

    loader.clean_callable(func, tmpconfig)

    assert hasattr(func, '_docs')
    assert len(func._docs) == 2
    assert 'test' in func._docs
    assert 'unit' in func._docs

    test_docs = func._docs['test']
    unit_docs = func._docs['unit']
    assert len(test_docs) == 2
    assert test_docs == unit_docs

    assert test_docs[0] == inspect.cleandoc(func.__doc__).splitlines()
    assert test_docs[1] == '.test hello'


def test_clean_callable_example_default_prefix(tmpconfig, func):
    module.commands('test')(func)
    module.example('.test hello')(func)

    tmpconfig.core.help_prefix = '!'
    loader.clean_callable(func, tmpconfig)

    assert len(func._docs) == 1
    assert 'test' in func._docs

    docs = func._docs['test']
    assert len(docs) == 2
    assert docs[0] == inspect.cleandoc(func.__doc__).splitlines()
    assert docs[1] == '!test hello'


def test_clean_callable_example_nickname(tmpconfig, func):
    module.commands('test')(func)
    module.example('$nickname: hello')(func)

    loader.clean_callable(func, tmpconfig)

    assert len(func._docs) == 1
    assert 'test' in func._docs

    docs = func._docs['test']
    assert len(docs) == 2
    assert docs[0] == inspect.cleandoc(func.__doc__).splitlines()
    assert docs[1] == 'TestBot: hello'


def test_clean_callable_intents(tmpconfig, func):
    setattr(func, 'intents', [r'abc'])
    loader.clean_callable(func, tmpconfig)

    assert hasattr(func, 'intents')
    assert len(func.intents) == 1

    # Test the regex is compiled properly
    regex = func.intents[0]
    assert regex.match('abc')
    assert regex.match('abcd')
    assert regex.match('ABC')
    assert regex.match('AbCdE')
    assert not regex.match('efg')


def test_load_module_pymod(tmpdir):
    root = tmpdir.mkdir('loader_mods')
    mod_file = root.join('file_mod.py')
    mod_file.write(MOCK_MODULE_CONTENT)

    test_mod, timeinfo = loader.load_module(
        'file_mod', mod_file.strpath, imp.PY_SOURCE)

    assert hasattr(test_mod, 'first_command')
    assert hasattr(test_mod, 'second_command')
    assert hasattr(test_mod, 'interval5s')
    assert hasattr(test_mod, 'interval10s')
    assert hasattr(test_mod, 'example_url')
    assert hasattr(test_mod, 'shutdown')
    assert hasattr(test_mod, 'ignored')

    assert timeinfo == os.path.getmtime(mod_file.strpath)


def test_load_module_pypackage(tmpdir):
    root = tmpdir.mkdir('loader_mods')
    package_dir = root.mkdir('dir_mod')
    mod_file = package_dir.join('__init__.py')
    mod_file.write(MOCK_MODULE_CONTENT)

    test_mod, timeinfo = loader.load_module(
        'dir_mod', package_dir.strpath, imp.PKG_DIRECTORY)

    assert hasattr(test_mod, 'first_command')
    assert hasattr(test_mod, 'second_command')
    assert hasattr(test_mod, 'interval5s')
    assert hasattr(test_mod, 'interval10s')
    assert hasattr(test_mod, 'example_url')
    assert hasattr(test_mod, 'shutdown')
    assert hasattr(test_mod, 'ignored')

    assert timeinfo == os.path.getmtime(package_dir.strpath)


def test_load_module_error(tmpdir):
    root = tmpdir.mkdir('loader_mods')
    mod_file = root.join('file_mod.py')
    mod_file.write(MOCK_MODULE_CONTENT)

    with pytest.raises(TypeError):
        loader.load_module('file_mod', mod_file.strpath, None)
