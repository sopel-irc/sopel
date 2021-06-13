# coding=utf-8
from __future__ import absolute_import, division, print_function, unicode_literals

import os
import sys

import pytest

from sopel import config
from sopel.config import types


FAKE_CONFIG = """
[core]
owner=dgw
homedir={homedir}
"""


MULTILINE_CONFIG = FAKE_CONFIG + """
[spam]
eggs = one, two, three, four, and a half
bacons = grilled
    burn out, 
    , greasy, fat, and tasty
cheeses =   
    cheddar
      reblochon   
  camembert
channels =
    "#sopel"
    &peculiar
# regular comment
    # python 3 only comment
    "#private"
    "#startquote
    &endquote"
    "&quoted"

[somesection]
is_defined = no
"""  # noqa (trailing whitespaces are intended)

TEST_CHANNELS = [
    '#sopel',
    '&peculiar',
    '#private',
    '"#startquote',  # start quote without end quote: kept
    '&endquote"',
    '"&quoted"',  # quoted, but no #: quotes kept
]

if sys.version_info.major < 3:
    # Python 2.7's ConfigParser interprets as comment
    # a line that starts with # or ;.
    # Python 3, on the other hand, allows comments to be indented.
    # As a result, the same config file will result in a different
    # config object depending on the Python version used.
    # TODO: Deprecated with Python 2.7.
    TEST_CHANNELS = [
        '#sopel',
        '&peculiar',
        '# python 3 only comment',  # indented lines cannot be comments in Py2
        '#private',
        '"#startquote',
        '&endquote"',
        '"&quoted"',
    ]


class FakeConfigSection(types.StaticSection):
    valattr = types.ValidatedAttribute('valattr')
    listattr = types.ListAttribute('listattr')
    choiceattr = types.ChoiceAttribute('choiceattr', ['spam', 'egg', 'bacon'])
    booleanattr = types.BooleanAttribute('booleanattr')
    booleanattr_true = types.BooleanAttribute('booleanattr', default=True)
    af_fileattr = types.FilenameAttribute('af_fileattr', relative=False, directory=False)
    ad_fileattr = types.FilenameAttribute('ad_fileattr', relative=False, directory=True)
    rf_fileattr = types.FilenameAttribute('rf_fileattr', relative=True, directory=False)
    rd_fileattr = types.FilenameAttribute('rd_fileattr', relative=True, directory=True)


class SpamSection(types.StaticSection):
    eggs = types.ListAttribute('eggs')
    bacons = types.ListAttribute('bacons', strip=False)
    cheeses = types.ListAttribute('cheeses')
    channels = types.ListAttribute('channels')


@pytest.fixture
def tmphomedir(tmpdir):
    sopel_homedir = tmpdir.join('.sopel')
    sopel_homedir.mkdir()
    sopel_homedir.join('test.tmp').write('')
    sopel_homedir.join('test.d').mkdir()
    return sopel_homedir


@pytest.fixture
def fakeconfig(tmphomedir):
    conf_file = tmphomedir.join('conf.cfg')
    conf_file.write(FAKE_CONFIG.format(homedir=tmphomedir.strpath))

    test_settings = config.Config(conf_file.strpath)
    test_settings.define_section('fake', FakeConfigSection)
    return test_settings


@pytest.fixture
def multi_fakeconfig(tmphomedir):
    conf_file = tmphomedir.join('conf.cfg')
    conf_file.write(MULTILINE_CONFIG.format(homedir=tmphomedir.strpath))

    test_settings = config.Config(conf_file.strpath)
    test_settings.define_section('fake', FakeConfigSection)
    test_settings.define_section('spam', SpamSection)
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
    assert fakeconfig.fake.listattr == [
        'spam', 'egg', 'sausage', 'bacon'
    ], 'Line break are always converted to new item'

    fakeconfig.fake.listattr = ['spam', 'egg\\sausage', 'bacon']
    assert fakeconfig.fake.listattr == ['spam', 'egg\\sausage', 'bacon']


def test_listattribute_with_value_ending_in_special_chars(fakeconfig):
    fakeconfig.fake.listattr = ['spam', 'egg', 'sausage\\', 'bacon']
    assert fakeconfig.fake.listattr == ['spam', 'egg', 'sausage\\', 'bacon']

    fakeconfig.fake.listattr = ['spam', 'egg', 'sausage,', 'bacon']
    assert fakeconfig.fake.listattr == ['spam', 'egg', 'sausage', 'bacon']

    fakeconfig.fake.listattr = ['spam', 'egg', 'sausage,,', 'bacon']
    assert fakeconfig.fake.listattr == ['spam', 'egg', 'sausage', 'bacon']


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


def test_booleanattribute_default(fakeconfig):
    assert fakeconfig.fake.booleanattr is False
    assert fakeconfig.fake.booleanattr_true is True


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


def test_configparser_env_priority_over_file(monkeypatch, fakeconfig):
    monkeypatch.setenv('SOPEL_CORE_OWNER', 'not_dgw')
    assert fakeconfig.core.owner == 'not_dgw'


def test_configparser_multi_lines(multi_fakeconfig):
    # spam
    assert multi_fakeconfig.spam.eggs == [
        'one',
        'two',
        'three',
        'four',
        'and a half',  # no-newline + comma
    ], 'Comma separated line: "four" and "and a half" must be separated'
    assert multi_fakeconfig.spam.bacons == [
        'grilled',
        'burn out',
        'greasy, fat, and tasty',
    ]
    assert multi_fakeconfig.spam.cheeses == [
        'cheddar',
        'reblochon',
        'camembert',
    ]

    assert multi_fakeconfig.spam.channels == TEST_CHANNELS


def test_configparser_multi_env(monkeypatch, multi_fakeconfig):
    monkeypatch.setenv('SOPEL_SPAM_EGGS', 'five, six, seven, eight, and a half')
    monkeypatch.setenv('SOPEL_SPAM_BACONS', 'microwaved\nfreeze in,\n, dry, thin, and disgusting')
    monkeypatch.setenv('SOPEL_SPAM_CHEESES', ' swiss\n  sbrinz\ncottage')
    # Comments not allowed when passing channels via ENV
    monkeypatch.setenv(
        'SOPEL_SPAM_CHANNELS',
        '"#sopel"\n&strange\n*someZnc\n"#public"\n"#frontquote\n&backquote"\n"&bothquoted"\n"*starchan"'
    )

    assert multi_fakeconfig.spam.eggs == [
        'five',
        'six',
        'seven',
        'eight',
        'and a half',  # no-newline + comma
    ]
    assert multi_fakeconfig.spam.bacons == [
        'microwaved',
        'freeze in',
        'dry, thin, and disgusting',
    ]
    assert multi_fakeconfig.spam.cheeses == [
        'swiss',
        'sbrinz',
        'cottage',
    ]
    assert multi_fakeconfig.spam.channels == [
        '#sopel',
        '&strange',
        '*someZnc',
        '#public',
        '"#frontquote',
        '&backquote"',
        '"&bothquoted"',
        '"*starchan"'
    ]


def test_save_unmodified_config(multi_fakeconfig):
    """Assert type attributes are kept as they should be"""
    multi_fakeconfig.save()
    saved_config = config.Config(multi_fakeconfig.filename)
    saved_config.define_section('fake', FakeConfigSection)
    saved_config.define_section('spam', SpamSection)

    # core
    assert saved_config.core.owner == 'dgw'

    # fake
    assert saved_config.fake.valattr is None
    assert saved_config.fake.listattr == []
    assert saved_config.fake.choiceattr is None
    assert saved_config.fake.af_fileattr is None
    assert saved_config.fake.ad_fileattr is None
    assert saved_config.fake.rf_fileattr is None
    assert saved_config.fake.rd_fileattr is None

    # spam
    assert saved_config.spam.eggs == [
        'one',
        'two',
        'three',
        'four',
        'and a half',  # no-newline + comma
    ], 'Comma separated line: "four" and "and a half" must be separated'
    assert saved_config.spam.bacons == [
        'grilled',
        'burn out',
        'greasy, fat, and tasty',
    ]
    assert saved_config.spam.cheeses == [
        'cheddar',
        'reblochon',
        'camembert',
    ]
    assert saved_config.spam.channels == TEST_CHANNELS


def test_save_modified_config(multi_fakeconfig):
    """Assert modified values are restored properly"""
    multi_fakeconfig.fake.choiceattr = 'spam'
    multi_fakeconfig.spam.eggs = [
        'one',
        'two',
    ]
    multi_fakeconfig.spam.cheeses = [
        'camembert, reblochon, and cheddar',
    ]
    multi_fakeconfig.spam.channels = [
        '#sopel',
        '#private',
        '&peculiar',
        '"#startquote',
        '&endquote"',
        '"&quoted"',
    ]

    multi_fakeconfig.save()

    with open(multi_fakeconfig.filename) as fd:
        print(fd.read())  # used for debug purpose if an assert fails

    saved_config = config.Config(multi_fakeconfig.filename)
    saved_config.define_section('fake', FakeConfigSection)
    saved_config.define_section('spam', SpamSection)

    assert saved_config.fake.choiceattr == 'spam'
    assert saved_config.spam.eggs == ['one', 'two']
    assert saved_config.spam.cheeses == [
        'camembert, reblochon, and cheddar',
    ], (
        'ListAttribute with one line only, with commas, must *not* be split '
        'differently from what was expected, i.e. into one (and only one) value'
    )
    assert saved_config.spam.channels == [
        '#sopel',
        '#private',
        '&peculiar',
        '"#startquote',  # start quote without end quote: kept
        '&endquote"',
        '"&quoted"',  # doesn't start with a # so it isn't escaped
    ]


def test_get_defined_sections(multi_fakeconfig):
    assert multi_fakeconfig.parser.has_section('core')
    assert multi_fakeconfig.parser.has_section('fake')
    assert multi_fakeconfig.parser.has_section('spam')
    assert multi_fakeconfig.parser.has_section('somesection')

    results = multi_fakeconfig.get_defined_sections()

    assert len(results) == 3, 'There should be 3 defined sections'

    items = dict(results)
    assert 'core' in items, 'core must be always defined'
    assert 'fake' in items
    assert 'spam' in items
    assert 'somesection' not in items, (
        'somesection was not defined and should not appear as such')
