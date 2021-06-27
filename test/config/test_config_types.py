from __future__ import generator_stop

import os

import pytest

from sopel.config import types


def test_validated_attribute():
    option = types.ValidatedAttribute('foo')
    assert option.name == 'foo'
    assert option.default is None
    assert option.is_secret is False


def test_validated_parse():
    option = types.ValidatedAttribute('foo')
    assert option.parse('string') == 'string'
    assert option.parse('1') == '1'
    assert option.parse('') == ''
    assert option.parse(None) is None
    assert option.parse(1) == 1


def test_validated_parse_custom():
    def _fixed_parser(value):
        return 'fixed value'

    option = types.ValidatedAttribute('foo', parse=_fixed_parser)
    assert option.parse('string') == 'fixed value'
    assert option.parse('1') == 'fixed value'
    assert option.parse('') == 'fixed value'
    assert option.parse(None) == 'fixed value'
    assert option.parse(1) == 'fixed value'


def test_validated_parse_bool():
    option = types.ValidatedAttribute('foo', parse=bool)
    assert option.parse('string') is False
    assert option.parse('1') is True
    assert option.parse('') is False
    assert option.parse(None) is False
    assert option.parse(1) == 1  # TODO: cast as ``True``?

    # true-ish values
    assert option.parse('yes') is True
    assert option.parse('YES') is True
    assert option.parse('yES') is True
    assert option.parse('y') is True
    assert option.parse('Y') is True
    assert option.parse('true') is True
    assert option.parse('True') is True
    assert option.parse('TRUE') is True
    assert option.parse('trUE') is True
    assert option.parse('on') is True
    assert option.parse('ON') is True
    assert option.parse('On') is True

    # everything else
    assert option.parse('no') is False
    assert option.parse('disable') is False
    assert option.parse('disabled') is False
    assert option.parse('enable') is False  # TODO: maybe true-ish?
    assert option.parse('enabled') is False  # TODO: maybe true-ish?


def test_validated_parse_int():
    option = types.ValidatedAttribute('foo', parse=int)
    assert option.parse('0') == 0
    assert option.parse('1') == 1
    assert option.parse('7814') == 7814
    assert option.parse('-1') == -1
    assert option.parse(1) == 1

    with pytest.raises(ValueError):
        option.parse('785.56')

    with pytest.raises(ValueError):
        option.parse('string')

    with pytest.raises(ValueError):
        option.parse('')

    with pytest.raises(TypeError):
        option.parse(None)


def test_validated_serialize():
    option = types.ValidatedAttribute('foo')
    assert option.serialize('string') == 'string'
    assert option.serialize('1') == '1'
    assert option.serialize('') == ''
    assert option.serialize(None) == 'None'  # TODO: empty string instead?
    assert option.serialize(1) == '1'


def test_validated_serialize_custom():
    def _fixed_serialize(value):
        return 'fixed value'

    option = types.ValidatedAttribute('foo', serialize=_fixed_serialize)
    assert option.serialize('string') == 'fixed value'
    assert option.serialize('1') == 'fixed value'
    assert option.serialize('') == 'fixed value'
    assert option.serialize(None) == 'fixed value'
    assert option.serialize(1) == 'fixed value'


def test_validated_serialize_bool():
    option = types.ValidatedAttribute('foo', parse=bool)
    assert option.serialize(True) == 'true'
    assert option.serialize('string') == 'false'
    assert option.serialize('1') == 'true'
    assert option.serialize('') == 'false'
    assert option.serialize(None) == 'false'
    assert option.serialize(1) == 'true'

    # true-ish values
    assert option.serialize('yes') == 'true'
    assert option.serialize('YES') == 'true'
    assert option.serialize('yES') == 'true'
    assert option.serialize('y') == 'true'
    assert option.serialize('Y') == 'true'
    assert option.serialize('true') == 'true'
    assert option.serialize('True') == 'true'
    assert option.serialize('TRUE') == 'true'
    assert option.serialize('trUE') == 'true'
    assert option.serialize('on') == 'true'
    assert option.serialize('ON') == 'true'
    assert option.serialize('On') == 'true'

    # everything else
    assert option.serialize('no') == 'false'
    assert option.serialize('disable') == 'false'
    assert option.serialize('disabled') == 'false'
    assert option.serialize('enable') == 'false'  # TODO: maybe true-ish?
    assert option.serialize('enabled') == 'false'  # TODO: maybe true-ish?


def test_validated_serialize_bool_custom():
    def _fixed_serialized(value):
        return 'fixed value'

    option = types.ValidatedAttribute(
        'foo', parse=bool, serialize=_fixed_serialized)
    assert option.serialize(True) == 'fixed value'
    assert option.serialize('string') == 'fixed value'
    assert option.serialize('1') == 'fixed value'
    assert option.serialize('') == 'fixed value'
    assert option.serialize(None) == 'fixed value'
    assert option.serialize(1) == 'fixed value'

    # true-ish values
    assert option.serialize('yes') == 'fixed value'
    assert option.serialize('YES') == 'fixed value'
    assert option.serialize('yES') == 'fixed value'
    assert option.serialize('y') == 'fixed value'
    assert option.serialize('Y') == 'fixed value'
    assert option.serialize('true') == 'fixed value'
    assert option.serialize('True') == 'fixed value'
    assert option.serialize('TRUE') == 'fixed value'
    assert option.serialize('trUE') == 'fixed value'
    assert option.serialize('on') == 'fixed value'
    assert option.serialize('ON') == 'fixed value'
    assert option.serialize('On') == 'fixed value'

    # everything else
    assert option.serialize('no') == 'fixed value'
    assert option.serialize('disable') == 'fixed value'
    assert option.serialize('disabled') == 'fixed value'
    assert option.serialize('enable') == 'fixed value'
    assert option.serialize('enabled') == 'fixed value'


def test_boolean_attribute():
    option = types.BooleanAttribute('foo')
    assert option.name == 'foo'
    assert option.default is False


def test_boolean_parse():
    option = types.BooleanAttribute('foo')
    assert option.parse('string') is False
    assert option.parse('1') is True
    assert option.parse('') is False
    assert option.parse(1) is True

    # true-ish values
    assert option.parse('yes') is True
    assert option.parse('YES') is True
    assert option.parse('yES') is True
    assert option.parse('y') is True
    assert option.parse('Y') is True
    assert option.parse('true') is True
    assert option.parse('True') is True
    assert option.parse('TRUE') is True
    assert option.parse('trUE') is True
    assert option.parse('on') is True
    assert option.parse('ON') is True
    assert option.parse('On') is True
    assert option.parse('enable') is True
    assert option.parse('enabled') is True

    # everything else
    assert option.parse('no') is False
    assert option.parse('off') is False
    assert option.parse('disable') is False
    assert option.parse('disabled') is False


def test_boolean_serialize():
    option = types.BooleanAttribute('foo')
    assert option.serialize(True) == 'true'
    assert option.serialize('string') == 'false'
    assert option.serialize('1') == 'true'
    assert option.serialize('') == 'false'
    assert option.serialize(1) == 'true'

    # true-ish values
    assert option.serialize('yes') == 'true'
    assert option.serialize('YES') == 'true'
    assert option.serialize('yES') == 'true'
    assert option.serialize('y') == 'true'
    assert option.serialize('Y') == 'true'
    assert option.serialize('true') == 'true'
    assert option.serialize('True') == 'true'
    assert option.serialize('TRUE') == 'true'
    assert option.serialize('trUE') == 'true'
    assert option.serialize('on') == 'true'
    assert option.serialize('ON') == 'true'
    assert option.serialize('On') == 'true'
    assert option.serialize('enable') == 'true'
    assert option.serialize('enabled') == 'true'

    # everything else
    assert option.serialize('no') == 'false'
    assert option.serialize('disable') == 'false'
    assert option.serialize('disabled') == 'false'


def test_secret_attribute():
    option = types.SecretAttribute('foo')
    assert option.name == 'foo'
    assert option.default is None
    assert option.is_secret is True


def test_list_attribute():
    option = types.ListAttribute('foo')
    assert option.name == 'foo'
    assert option.default == []
    assert option.is_secret is False


def test_list_parse_single_value():
    option = types.ListAttribute('foo')
    assert option.parse('string') == ['string']
    assert option.parse('1') == ['1']
    assert option.parse('') == []

    with pytest.raises(TypeError):
        option.parse(None)

    with pytest.raises(TypeError):
        option.parse(1)


def test_list_parse_new_lines():
    option = types.ListAttribute('foo')
    assert option.parse("""
    value 1
    "# value 2"
    value 3
    """) == [
        'value 1',
        '# value 2',
        'value 3',
    ]


def test_list_parse_new_lines_no_strip():
    option = types.ListAttribute('foo', strip=False)
    # strip isn't used for newline-based list attribute
    assert option.parse("""
    value 1
    "# value 2"
    value 3
    """) == [
        'value 1',
        '# value 2',
        'value 3',
    ]


def test_list_parse_legacy_comma():
    option = types.ListAttribute('foo')
    assert option.parse("""value 1, # value 2, value 3""") == [
        'value 1',
        '# value 2',
        'value 3',
    ]


def test_list_parse_legacy_comma_no_strip():
    option = types.ListAttribute('foo', strip=False)
    assert option.parse("""value 1, # value 2   ,   value 3""") == [
        'value 1',
        ' # value 2   ',
        '   value 3',
    ]


def test_list_parse_new_lines_legacy_comma():
    option = types.ListAttribute('foo')
    assert option.parse("""
        value 1, value 2,
        value 3
    """) == [
        'value 1, value 2',
        'value 3',
    ]


def test_list_serialize():
    option = types.ListAttribute('foo')
    assert option.serialize([]) == ''
    assert option.serialize(['value 1', 'value 2', 'value 3']) == (
        '\n'
        'value 1\n'
        'value 2\n'
        'value 3'
    )

    assert option.serialize(set()) == ''
    assert option.serialize(set(['1', '2', '3'])) == (
        '\n' + '\n'.join(set(['1', '2', '3']))
    )


def test_list_serialize_quote():
    option = types.ListAttribute('foo')
    assert option.serialize(['value 1', '# value 2', 'value 3']) == (
        '\n'
        'value 1\n'
        '"# value 2"\n'
        'value 3'
    )


def test_list_serialize_value_error():
    option = types.ListAttribute('foo')

    with pytest.raises(ValueError):
        option.serialize('value 1')

    with pytest.raises(ValueError):
        option.serialize(('1', '2', '3'))  # tuple is not allowed


def test_choice_attribute():
    option = types.ChoiceAttribute('foo', choices=['a', 'b', 'c'])
    assert option.name == 'foo'
    assert option.default is None
    assert option.is_secret is False


def test_choice_parse():
    option = types.ChoiceAttribute('foo', choices=['a', 'b', 'c'])
    assert option.parse('a') == 'a'
    assert option.parse('b') == 'b'
    assert option.parse('c') == 'c'

    with pytest.raises(ValueError):
        option.parse('d')


def test_choice_serialize():
    option = types.ChoiceAttribute('foo', choices=['a', 'b', 'c'])
    assert option.serialize('a') == 'a'
    assert option.serialize('b') == 'b'
    assert option.serialize('c') == 'c'

    with pytest.raises(ValueError):
        option.serialize('d')


def test_filename_attribute():
    option = types.FilenameAttribute('foo')
    assert option.name == 'foo'
    assert option.default is None
    assert option.is_secret is False
    assert option.directory is False
    assert option.relative is True


def test_filename_parse(tmpdir):
    testfile = tmpdir.join('foo.txt')
    testfile.write('')
    option = types.FilenameAttribute('foo')
    assert option.parse(testfile.strpath) == testfile.strpath
    assert option.parse(None) is None
    assert option.parse('') is None


def test_filename_parse_create(tmpdir):
    testfile = tmpdir.join('foo.txt')

    option = types.FilenameAttribute('foo')
    assert not os.path.exists(testfile.strpath), 'Test file must not exist yet'
    assert option.parse(testfile.strpath) == testfile.strpath
    assert os.path.exists(testfile.strpath), 'Test file must exist now'
    assert os.path.isfile(testfile.strpath), 'Test file must be a file'


def test_filename_parse_directory(tmpdir):
    testdir = tmpdir.join('foo')
    testdir.mkdir()
    option = types.FilenameAttribute('foo', directory=True)
    assert option.parse(testdir.strpath) == testdir.strpath


def test_filename_parse_directory_create(tmpdir):
    testdir = tmpdir.join('foo')
    option = types.FilenameAttribute('foo', directory=True)
    assert not os.path.exists(testdir.strpath), 'Test dir must not exist yet'
    assert option.parse(testdir.strpath) == testdir.strpath
    assert os.path.exists(testdir.strpath), 'Test dir must exist now'
    assert os.path.isdir(testdir.strpath), 'Test dir must be a directory'
