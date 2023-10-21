"""Tests for Sopel Memory data-structures"""
from __future__ import annotations

import pytest

from sopel.tools import identifiers, memories


def test_sopel_identifier_memory_none():
    memory = memories.SopelIdentifierMemory()
    assert None not in memory


def test_sopel_identifier_memory_str():
    user = identifiers.Identifier('Exirel')
    memory = memories.SopelIdentifierMemory()
    test_value = 'king'

    memory['Exirel'] = test_value
    assert user in memory
    assert 'Exirel' in memory
    assert 'exirel' in memory
    assert 'exi' not in memory
    assert '#channel' not in memory

    assert memory[user] == test_value
    assert memory['Exirel'] == test_value
    assert memory['exirel'] == test_value


def test_sopel_identifier_memory_id():
    user = identifiers.Identifier('Exirel')
    memory = memories.SopelIdentifierMemory()
    test_value = 'king'

    memory[user] = test_value
    assert user in memory
    assert 'Exirel' in memory
    assert 'exirel' in memory
    assert 'exi' not in memory
    assert '#channel' not in memory

    assert memory[user] == test_value
    assert memory['Exirel'] == test_value
    assert memory['exirel'] == test_value


def test_sopel_identifier_memory_channel_str():
    channel = identifiers.Identifier('#adminchannel')
    memory = memories.SopelIdentifierMemory()
    test_value = 'perfect'

    memory['#adminchannel'] = test_value
    assert channel in memory
    assert '#adminchannel' in memory
    assert '#AdminChannel' in memory
    assert 'adminchannel' not in memory
    assert 'Exirel' not in memory

    assert memory[channel] == test_value
    assert memory['#adminchannel'] == test_value
    assert memory['#AdminChannel'] == test_value


def test_sopel_identifier_memory_del_key():
    memory = memories.SopelIdentifierMemory()
    memory['KeY'] = True
    assert 'KeY' in memory
    del memory['KeY']
    assert 'KeY' not in memory

    memory['kEy'] = True
    assert 'KeY' in memory
    del memory['KeY']
    assert 'KeY' not in memory


def test_sopel_identifier_memory_copy():
    memory = memories.SopelIdentifierMemory()
    memory['SomeCamelCase'] = True
    memory['loweronly'] = False
    assert len(memory) == 2
    assert isinstance(memory, memories.SopelIdentifierMemory)

    copied = memory.copy()
    assert len(copied) == 2
    assert 'SomeCamelCase' in copied
    assert 'loweronly' in copied
    assert isinstance(memory, memories.SopelIdentifierMemory)

    # be absolutely sure it's a new object
    copied['newOnly'] = True
    assert 'NewOnly' in copied
    assert 'NewOnly' not in memory
    del copied['LowerOnly']
    assert 'LowerOnly' not in copied
    assert 'LowerOnly' in memory


def test_sopel_identifier_memory_get():
    memory = memories.SopelIdentifierMemory()
    memory['SomeCamelCase'] = True
    memory['loweronly'] = False
    assert len(memory) == 2

    # verify key-exists behavior w/implicit default
    assert memory.get('somecamelcase') == memory['somecamelcase']
    assert memory.get('LowerOnly') == memory['LowerOnly']
    assert len(memory) == 2

    # verify key-exists behavior w/explicit default of None
    assert memory.get('somecamelcase', None) == memory['somecamelcase']
    assert memory.get('LowerOnly', None) == memory['LowerOnly']
    assert len(memory) == 2

    # verify key-exists behavior w/explicit "real" default value
    assert memory.get('somecamelcase', 'DEFAULT') == memory['somecamelcase']
    assert memory.get('LowerOnly', 'DEFAULT') == memory['LowerOnly']
    assert len(memory) == 2

    # verify key-missing behavior w/implicit default
    assert 'missing_key' not in memory
    assert memory.get('missing_key') is None
    assert len(memory) == 2

    # verify key-missing behavior w/explicit default of None
    assert 'missing_key' not in memory
    assert memory.get('missing_key', None) is None
    assert len(memory) == 2

    # verify key-missing behavior w/explicit "real" default value
    assert 'missing_key' not in memory
    assert memory.get('missing_key', 'DEFAULT') == 'DEFAULT'
    assert len(memory) == 2


def test_sopel_identifier_memory_pop():
    memory = memories.SopelIdentifierMemory()
    memory['SomeCamelCase'] = True
    assert len(memory) == 1

    # verify SopelIdentifierMemory.pop('key') behavior
    pop_me = memory.copy()
    assert len(pop_me) == 1
    assert pop_me.pop('someCAMELcase') is True
    assert len(memory) == 1  # sanity check
    assert len(pop_me) == 0

    # verify SopelIdentifierMemory.pop('key', None) behavior
    pop_me = memory.copy()
    assert len(pop_me) == 1
    assert pop_me.pop('someCAMELcase', None) is True
    assert len(pop_me) == 0

    # verify SopelIdentifierMemory.pop('key', 'default_value') behavior
    pop_me = memory.copy()
    assert len(pop_me) == 1
    assert pop_me.pop('someCAMELcase', 'DEFAULT') is True
    assert len(pop_me) == 0

    # verify SopelIdentifierMemory.pop('missing_key') behavior
    pop_me = memory.copy()
    assert len(pop_me) == 1
    assert 'missing_key' not in pop_me
    with pytest.raises(KeyError):
        pop_me.pop('missing_key')
    assert len(pop_me) == 1

    # verify SopelIdentifierMemory.pop('missing_key', None) behavior
    assert 'missing_key' not in pop_me
    assert pop_me.pop('missing_key', None) is None
    assert len(pop_me) == 1

    # verify SopelIdentifierMemory.pop('missing_key', 'default_value') behavior
    assert 'missing_key' not in pop_me
    assert pop_me.pop('missing_key', 'DEFAULT') == 'DEFAULT'
    assert len(pop_me) == 1


def test_sopel_identifier_memory_from_dict():
    dictionary = {'CamelCaseKey': True, 'lowercasekey': False}

    memory = memories.SopelIdentifierMemory(dictionary)
    assert 'CamelCaseKey' in memory
    assert 'camelcasekey' in memory
    assert memory['cameLcasEkeY'] == dictionary['CamelCaseKey']
    assert 'lowercasekey' in memory
    assert 'LowerCaseKey' in memory
    assert memory['LoWeRcAsEkEy'] == dictionary['lowercasekey']


def test_sopel_identifier_memory_from_identifier_memory():
    original_memory = memories.SopelIdentifierMemory(
        {'CamelCaseKey': True, 'lowercasekey': False}
    )
    assert 'CamelCaseKey' in original_memory
    assert 'camelcasekey' in original_memory
    assert 'lowercasekey' in original_memory
    assert 'LowerCaseKey' in original_memory

    memory = memories.SopelIdentifierMemory(original_memory)
    assert 'CamelCaseKey' in memory
    assert 'camelcasekey' in memory
    assert memory['cameLcasEkeY'] is True
    assert 'lowercasekey' in memory
    assert 'LowerCaseKey' in memory
    assert memory['LoWeRcAsEkEy'] is False

    # be sure we really have a new object
    memory['newOnly'] = True
    assert 'NewOnly' in memory
    assert 'NewOnly' not in original_memory
    del memory['cameLcasEkeY']
    assert 'cameLcasEkeY' not in memory
    assert 'cameLcasEkeY' in original_memory


def test_sopel_identifier_memory_from_list():
    pairs_list = [('CamelCaseKey', True), ('lowercasekey', False)]
    memory = memories.SopelIdentifierMemory(pairs_list)

    assert 'CamelCaseKey' in memory
    assert 'camelcasekey' in memory
    assert memory['cameLcasEkeY'] is True
    assert 'lowercasekey' in memory
    assert 'LowerCaseKey' in memory
    assert memory['LoWeRcAsEkEy'] is False


def test_sopel_identifier_memory_from_tuple():
    pairs_tuple = (('CamelCaseKey', True), ('lowercasekey', False))
    memory = memories.SopelIdentifierMemory(pairs_tuple)
    assert 'CamelCaseKey' in memory
    assert 'camelcasekey' in memory
    assert memory['cameLcasEkeY'] is True
    assert 'lowercasekey' in memory
    assert 'LowerCaseKey' in memory
    assert memory['LoWeRcAsEkEy'] is False


def test_sopel_identifier_memory_from_kwargs():
    # This is unsupported behavior, by design.
    with pytest.raises(TypeError):
        memories.SopelIdentifierMemory(CamelCaseKey=True, lowercasekey=False)


def test_sopel_identifier_memory_clear():
    memory = memories.SopelIdentifierMemory(
        {'FooBar': 'foobar', 'BarFoo': 'barfoo'}
    )
    assert isinstance(memory, memories.SopelIdentifierMemory)
    assert len(memory) == 2
    assert 'FooBar' in memory
    assert memory['FooBar'] == 'foobar'
    assert 'BarFoo' in memory
    assert memory['BarFoo'] == 'barfoo'

    memory.clear()
    assert isinstance(memory, memories.SopelIdentifierMemory)
    assert len(memory) == 0
    assert 'FooBar' not in memory
    assert 'BarFoo' not in memory

    memory['spameggs'] = 'spameggs'
    assert len(memory) == 1
    assert 'SpamEggs' in memory
    assert memory['SpamEggs'] == 'spameggs'
    assert memory['spaMeggS'] == 'spameggs'
    assert memory['spameggs'] == memory['sPAmeGGs']
