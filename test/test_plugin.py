# coding=utf-8
"""Tests for sopel.plugin decorators"""
from __future__ import absolute_import, division, print_function, unicode_literals

from sopel import plugin


def test_find():
    @plugin.find('.*')
    def mock(bot, trigger, match):
        return True
    assert mock.find_rules == ['.*']


def test_find_args():
    @plugin.find('.*', r'\d+')
    def mock(bot, trigger, match):
        return True
    assert mock.find_rules == ['.*', r'\d+']


def test_find_multiple():
    @plugin.find('.*', r'\d+')
    @plugin.find('.*')
    @plugin.find(r'\w+')
    def mock(bot, trigger, match):
        return True
    assert mock.find_rules == [r'\w+', '.*', r'\d+']


def test_label():
    @plugin.label('hello')
    def mock(bot, trigger):
        return True
    assert mock.rule_label == 'hello'


def test_search():
    @plugin.search('.*')
    def mock(bot, trigger, match):
        return True
    assert mock.search_rules == ['.*']


def test_search_args():
    @plugin.search('.*', r'\d+')
    def mock(bot, trigger, match):
        return True
    assert mock.search_rules == ['.*', r'\d+']


def test_search_multiple():
    @plugin.search('.*', r'\d+')
    @plugin.search('.*')
    @plugin.search(r'\w+')
    def mock(bot, trigger, match):
        return True
    assert mock.search_rules == [r'\w+', '.*', r'\d+']


def test_url_lazy():
    def loader(settings):
        return [r'\w+', '.*', r'\d+']

    @plugin.url_lazy(loader)
    def mock(bot, trigger, match):
        return True

    assert mock.url_lazy_loader == loader
    assert not hasattr(mock, 'url_regex')
