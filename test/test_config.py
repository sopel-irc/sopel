# coding=utf-8
from __future__ import unicode_literals, division, print_function, absolute_import

import os

import pytest

from sopel import config
from sopel.config import types


FAKE_CONFIG = """
[core]
owner=dgw
homedir={homedir}
"""


class FakeConfigSection(types.StaticSection):
    valattr = types.ValidatedAttribute('valattr')
    listattr = types.ListAttribute('listattr')
    choiceattr = types.ChoiceAttribute('choiceattr', ['spam', 'egg', 'bacon'])
    af_fileattr = types.FilenameAttribute('af_fileattr', relative=False, directory=False)
    ad_fileattr = types.FilenameAttribute('ad_fileattr', relative=False, directory=True)
    rf_fileattr = types.FilenameAttribute('rf_fileattr', relative=True, directory=False)
    rd_fileattr = types.FilenameAttribute('rd_fileattr', relative=True, directory=True)


@pytest.fixture
def fakeconfig(tmpdir):
    sopel_homedir = tmpdir.join('.sopel')
    sopel_homedir.mkdir()
    sopel_homedir.join('test.tmp').write('')
    sopel_homedir.join('test.d').mkdir()
    conf_file = sopel_homedir.join('conf.cfg')
    conf_file.write(FAKE_CONFIG.format(homedir=sopel_homedir.strpath))

    test_settings = config.Config(conf_file.strpath)
    test_settings.define_section('fake', FakeConfigSection)
    return test_settings


def test_validated_string_when_none(fakeconfig):
    fakeconfig.fake.valattr = None
    assert fakeconfig.fake.valattr is None


def test_listattribute_when_empty(fakeconfig):
    fakeconfig.fake.listattr = []
    assert fakeconfig.fake.listattr == []


def test_listattribute_with_one_value(fakeconfig):
    fakeconfig.fake.listattr = ['foo']
    assert fakeconfig.fake.listattr == ['foo']


def test_listattribute_with_multiple_values(fakeconfig):
    fakeconfig.fake.listattr = ['egg', 'sausage', 'bacon']
    assert fakeconfig.fake.listattr == ['egg', 'sausage', 'bacon']


def test_listattribute_with_value_containing_comma(fakeconfig):
    fakeconfig.fake.listattr = ['spam, egg, sausage', 'bacon']
    assert fakeconfig.fake.listattr == ['spam, egg, sausage', 'bacon']


def test_listattribute_with_value_containing_nonescape_backslash(fakeconfig):
    fakeconfig.fake.listattr = ['spam', r'egg\sausage', 'bacon']
    assert fakeconfig.fake.listattr == ['spam', r'egg\sausage', 'bacon']

    fakeconfig.fake.listattr = ['spam', r'egg\tacos', 'bacon']
    assert fakeconfig.fake.listattr == ['spam', r'egg\tacos', 'bacon']


def test_listattribute_with_value_containing_standard_escape_sequence(fakeconfig):
    fakeconfig.fake.listattr = ['spam', 'egg\tsausage', 'bacon']
    assert fakeconfig.fake.listattr == ['spam', 'egg\tsausage', 'bacon']

    fakeconfig.fake.listattr = ['spam', 'egg\nsausage', 'bacon']
    assert fakeconfig.fake.listattr == ['spam', 'egg\nsausage', 'bacon']

    fakeconfig.fake.listattr = ['spam', 'egg\\sausage', 'bacon']
    assert fakeconfig.fake.listattr == ['spam', 'egg\\sausage', 'bacon']


def test_listattribute_with_value_ending_in_special_chars(fakeconfig):
    fakeconfig.fake.listattr = ['spam', 'egg', 'sausage\\', 'bacon']
    assert fakeconfig.fake.listattr == ['spam', 'egg', 'sausage\\', 'bacon']

    fakeconfig.fake.listattr = ['spam', 'egg', 'sausage,', 'bacon']
    assert fakeconfig.fake.listattr == ['spam', 'egg', 'sausage,', 'bacon']

    fakeconfig.fake.listattr = ['spam', 'egg', 'sausage,,', 'bacon']
    assert fakeconfig.fake.listattr == ['spam', 'egg', 'sausage,,', 'bacon']


def test_listattribute_with_value_containing_adjacent_special_chars(fakeconfig):
    fakeconfig.fake.listattr = ['spam', r'egg\,sausage', 'bacon']
    assert fakeconfig.fake.listattr == ['spam', r'egg\,sausage', 'bacon']

    fakeconfig.fake.listattr = ['spam', r'egg\,\sausage', 'bacon']
    assert fakeconfig.fake.listattr == ['spam', r'egg\,\sausage', 'bacon']

    fakeconfig.fake.listattr = ['spam', r'egg,\,sausage', 'bacon']
    assert fakeconfig.fake.listattr == ['spam', r'egg,\,sausage', 'bacon']

    fakeconfig.fake.listattr = ['spam', 'egg,,sausage', 'bacon']
    assert fakeconfig.fake.listattr == ['spam', 'egg,,sausage', 'bacon']

    fakeconfig.fake.listattr = ['spam', r'egg\\sausage', 'bacon']
    assert fakeconfig.fake.listattr == ['spam', r'egg\\sausage', 'bacon']


def test_choiceattribute_when_none(fakeconfig):
    fakeconfig.fake.choiceattr = None
    assert fakeconfig.fake.choiceattr is None


def test_choiceattribute_when_not_in_set(fakeconfig):
    with pytest.raises(ValueError):
        fakeconfig.fake.choiceattr = 'sausage'


def test_choiceattribute_when_valid(fakeconfig):
    fakeconfig.fake.choiceattr = 'bacon'
    assert fakeconfig.fake.choiceattr == 'bacon'


def test_fileattribute_valid_absolute_file_path(fakeconfig):
    testfile = os.path.join(fakeconfig.core.homedir, 'test.tmp')
    fakeconfig.fake.af_fileattr = testfile
    assert fakeconfig.fake.af_fileattr == testfile


def test_fileattribute_valid_absolute_dir_path(fakeconfig):
    testdir = os.path.join(fakeconfig.core.homedir, 'test.d')
    fakeconfig.fake.ad_fileattr = testdir
    assert fakeconfig.fake.ad_fileattr == testdir


def test_fileattribute_given_relative_when_absolute(fakeconfig):
    with pytest.raises(ValueError):
        fakeconfig.fake.af_fileattr = '../testconfig.tmp'


def test_fileattribute_given_absolute_when_relative(fakeconfig):
    testfile = os.path.join(fakeconfig.core.homedir, 'test.tmp')
    fakeconfig.fake.rf_fileattr = testfile
    assert fakeconfig.fake.rf_fileattr == testfile


def test_fileattribute_given_dir_when_file(fakeconfig):
    testdir = os.path.join(fakeconfig.core.homedir, 'test.d')
    with pytest.raises(ValueError):
        fakeconfig.fake.af_fileattr = testdir


def test_fileattribute_given_file_when_dir(fakeconfig):
    testfile = os.path.join(fakeconfig.core.homedir, 'test.tmp')
    with pytest.raises(ValueError):
        fakeconfig.fake.ad_fileattr = testfile
