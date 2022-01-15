"""Tests for Sopel Memory data-structures"""
from __future__ import annotations

from sopel.tools import identifiers, memories


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
