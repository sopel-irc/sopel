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


def test_sopel_identifier_memory_setdefault():
    memory = memories.SopelIdentifierMemory()
    assert 'foo' not in memory

    memory.setdefault('Foo')
    assert len(memory) == 1
    assert 'foo' in memory
    assert 'fOO' in memory
    assert memory['fOo'] is None

    memory.setdefault('bAr', 'DEFAULT')
    assert len(memory) == 2
    assert 'FoO' in memory
    assert 'BaR' in memory
    assert memory['Bar'] == 'DEFAULT'

    assert memory.setdefault('baR', 'different') == 'DEFAULT'
    assert len(memory) == 2


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


def test_sopel_identifier_memory_update():
    memory = memories.SopelIdentifierMemory({
        'FromIdentifierMemory': True,
    })
    tuple_ = (('FromTuplePairs', True), ('FromIdentifierMemory', False))
    list_ = [('FromTuplePairs', False), ('FromListPairs', True)]
    dict_ = {'FromDict': True, 'FromListPairs': False}
    set_ = set((('FromDict', False), ('FromSet', True)))

    assert len(memory) == 1
    assert memory['froMidentifieRmemorY'] is True
    assert 'froMtuplEpairS' not in memory
    assert 'froMlisTpairS' not in memory
    assert 'froMdicT' not in memory
    assert 'froMseT' not in memory

    memory.update(tuple_)
    assert len(memory) == 2
    assert memory['froMidentifieRmemorY'] is False
    assert memory['froMtuplEpairS'] is True
    assert 'froMlisTpairS' not in memory
    assert 'froMdicT' not in memory
    assert 'froMseT' not in memory

    memory.update(list_)
    assert len(memory) == 3
    assert memory['froMidentifieRmemorY'] is False
    assert memory['froMtuplEpairS'] is False
    assert memory['froMlisTpairS'] is True
    assert 'froMdicT' not in memory
    assert 'froMseT' not in memory

    memory.update(dict_)
    assert len(memory) == 4
    assert memory['froMidentifieRmemorY'] is False
    assert memory['froMtuplEpairS'] is False
    assert memory['froMlisTpairS'] is False
    assert memory['froMdicT'] is True
    assert 'froMseT' not in memory

    memory.update(set_)
    assert len(memory) == 5
    assert memory['froMidentifieRmemorY'] is False
    assert memory['froMtuplEpairS'] is False
    assert memory['froMlisTpairS'] is False
    assert memory['froMdicT'] is False
    assert memory['froMseT'] is True


def test_sopel_identifier_memory_or_op():
    memory = memories.SopelIdentifierMemory({
        'FromMemory': True,
        'FromOther': False,
    })
    assert len(memory) == 2
    assert memory['froMmemorY'] is True
    assert memory['froMotheR'] is False

    other_memory = memories.SopelIdentifierMemory({
        'FromMemory': False,
        'FromOther': True,
    })
    assert len(other_memory) == 2
    assert 'FromOther' in other_memory
    assert other_memory['FromOther'] is True
    assert 'fromother' in other_memory

    result = memory | other_memory
    assert len(result) == 2
    assert result['fROmMemorY'] is False
    assert result['fROmoTHEr'] is True

    result = other_memory | memory
    assert len(result) == 2
    assert result['FroMMemorY'] is True
    assert result['FroMOtheR'] is False


def test_sopel_identifier_memory_or_op_dict():
    memory = memories.SopelIdentifierMemory({'FromMemory': True, 'FromDict': False})
    assert len(memory) == 2
    assert memory['froMmemorY'] is True
    assert memory['froMdicT'] is False

    dictionary = {'FromMemory': False, 'FromDict': True, 'AlsoFromDict': True}
    assert len(dictionary) == 3
    assert dictionary['FromDict'] is True
    assert dictionary['FromMemory'] is False
    assert dictionary['AlsoFromDict'] is True
    assert 'alsofromdict' not in dictionary

    # __or__
    result = memory | dictionary
    assert len(result) == 3
    assert result['fROmMemorY'] is False
    assert result['fROmDicT'] is True
    assert result['alsOfroMdicT'] is True

    # __ror__
    result = dictionary | memory
    assert len(result) == 3
    assert result['fROmMemorY'] is True
    assert result['fROmDicT'] is False
    assert result['alsOfroMdicT'] is True


def test_sopel_identifier_memory_or_op_other():
    memory = memories.SopelIdentifierMemory()

    with pytest.raises(TypeError):
        # __or__
        memory | 5
    with pytest.raises(TypeError):
        # __ror__
        'str' | memory


def test_sopel_identifier_memory_ior_op():
    memory = memories.SopelIdentifierMemory({'FromMemory': True})
    assert len(memory) == 1
    assert memory['froMmemorY'] is True

    other_memory = memories.SopelIdentifierMemory({
        'FromMemory': False,
        'FromOther': True,
    })
    assert len(other_memory) == 2
    assert 'FromOther' in other_memory
    assert other_memory['froMotheR'] is True

    memory |= other_memory
    assert len(memory) == 2
    assert memory['fROmMemorY'] is False
    assert memory['fROmoTHEr'] is True


def test_sopel_identifier_memory_ior_op_dict():
    memory = memories.SopelIdentifierMemory({'FromMemory': True})
    assert len(memory) == 1
    assert memory['froMmemorY'] is True

    dictionary = {'FromDict': True}
    assert len(dictionary) == 1
    assert 'FromDict' in dictionary
    assert dictionary['FromDict'] is True
    assert 'fromdict' not in dictionary

    memory |= dictionary
    assert len(memory) == 2
    assert memory['fROmMemorY'] is True
    assert memory['fROmDicT'] is True


def test_sopel_identifier_memory_ior_op_other():
    memory = memories.SopelIdentifierMemory()

    with pytest.raises(TypeError):
        memory |= 5
    with pytest.raises(TypeError):
        memory |= 'str'


def test_sopel_identifier_memory_eq():
    """Test equality checks between two `SopelIdentifierMemory` instances."""
    memory = memories.SopelIdentifierMemory({'Foo': 'bar', 'Baz': 'Luhrmann'})
    other_memory = memories.SopelIdentifierMemory((('Foo', 'bar'), ('Baz', 'Luhrmann')))

    assert memory == other_memory
    assert other_memory == memory  # cover our bases vis-a-vis operand precedence

    memory = memories.SopelIdentifierMemory({'fOO': 'bar', 'bAZ': 'Luhrmann'})

    assert memory == other_memory
    assert other_memory == memory  # cover our bases vis-a-vis operand precedence


def test_sopel_identifier_memory_eq_dict_id():
    """Test ``SopelIdentifierMemory`` comparison to ``dict[Identifier, Any]``.

    These can be equivalent, just like two ``dict`` objects with identical
    ``Identifier`` keys can be.
    """
    memory = memories.SopelIdentifierMemory({'Foo': 'bar', 'Baz': 'Luhrmann'})
    dictionary = dict(memory)

    assert dictionary == memory
    assert memory == dictionary  # cover our bases vis-a-vis operand precedence


def test_sopel_identifier_memory_eq_dict_str():
    """Test ``SopelIdentifierMemory`` comparison to ``dict[str, Any]``.

    These are intentionally not considered equivalent.
    """
    dictionary = {'Foo': 'bar', 'Baz': 'Luhrmann'}
    memory = memories.SopelIdentifierMemory(dictionary)

    assert dictionary != memory
    assert memory != dictionary  # cover our bases vis-a-vis operand precedence

    memory = memories.SopelIdentifierMemory((('Spam', 'eggs'), ('GreenEggs', 'ham')))

    assert dictionary != memory
    assert memory != dictionary  # cover our bases vis-a-vis operand precedence


def test_sopel_identifier_memory_eq_other():
    """Test ``SopelIdentifierMemory`` comparison to non-dict types.

    Never equivalent (``NotImplemented``).
    """
    memory = memories.SopelIdentifierMemory({'Foo': 'bar', 'Baz': 'Luhrmann'})

    assert memory != 'string'
    assert memory != 5
    assert memory != ('Foo', 'Bar')

    # operator precedence ass-covering
    assert 'string' != memory
