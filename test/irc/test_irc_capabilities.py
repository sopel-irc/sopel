"""Test ``sopel.irc.capabilities``."""
from __future__ import annotations

import typing

import pytest

from sopel.irc.capabilities import Capabilities, CapabilityInfo
from sopel.plugins.rules import Rule

if typing.TYPE_CHECKING:
    from sopel.tests.factories import TriggerFactory


TMP_CONFIG = """
[core]
owner = testnick
nick = TestBot
enable = coretasks
"""


@pytest.fixture
def tmpconfig(configfactory):
    return configfactory('test.cfg', TMP_CONFIG)


@pytest.fixture
def mockbot(tmpconfig, botfactory):
    return botfactory(tmpconfig)


@pytest.fixture
def mockrule():
    return Rule(regexes=['*'], plugin='test_plugin')


def test_capabilities_empty():
    manager = Capabilities()
    assert not manager.is_available('away-notify')
    assert not manager.is_enabled('away-notify')
    assert not manager.available
    assert not manager.enabled


def test_capabilities_ls(mockbot, triggerfactory: TriggerFactory):
    raw = 'CAP * LS :away-notify'
    wrapped = triggerfactory.wrapper(mockbot, raw)
    manager = Capabilities()
    assert manager.handle_ls(wrapped, wrapped.trigger)
    assert manager.is_available('away-notify')
    assert not manager.is_enabled('away-notify')
    assert manager.available == {'away-notify': None}
    assert not manager.enabled

    expected = CapabilityInfo('away-notify', None, True, False)
    assert manager.get_capability_info('away-notify') == expected


def test_capabilities_ls_parameter(mockbot, triggerfactory: TriggerFactory):
    raw = 'CAP * LS :sasl=EXTERNAL,PLAIN'
    wrapped = triggerfactory.wrapper(mockbot, raw)
    manager = Capabilities()
    assert manager.handle_ls(wrapped, wrapped.trigger)
    assert manager.is_available('sasl')
    assert not manager.is_enabled('sasl')
    assert manager.available == {'sasl': 'EXTERNAL,PLAIN'}

    expected = CapabilityInfo('sasl', 'EXTERNAL,PLAIN', True, False)
    assert manager.get_capability_info('sasl') == expected


def test_capabilities_ls_multiline(mockbot, triggerfactory, mockrule):
    manager = Capabilities()

    raw = 'CAP * LS * :away-notify'
    with mockbot.sopel_wrapper(
        triggerfactory(mockbot, raw), mockrule
    ) as wrapped:
        assert not manager.handle_ls(wrapped, wrapped.trigger)

    assert manager.is_available('away-notify')
    assert not manager.is_enabled('away-notify')
    assert manager.available == {'away-notify': None}

    raw = 'CAP * LS :account-tag'
    with mockbot.sopel_wrapper(
        triggerfactory(mockbot, raw), mockrule
    ) as wrapped:
        assert manager.handle_ls(wrapped, wrapped.trigger)

    assert manager.is_available('away-notify')
    assert manager.is_available('account-tag')
    assert not manager.is_enabled('away-notify')
    assert not manager.is_enabled('account-tag')
    assert manager.available == {'away-notify': None, 'account-tag': None}


def test_capabilities_ack(mockbot, triggerfactory, mockrule):
    raw = 'CAP * ACK :away-notify'
    manager = Capabilities()

    with mockbot.sopel_wrapper(
        triggerfactory(mockbot, raw), mockrule
    ) as wrapped:
        assert manager.handle_ack(wrapped, wrapped.trigger) == ('away-notify',)
    assert not manager.is_available('away-notify'), (
        'ACK a capability does not update server availability.')
    assert manager.is_enabled('away-notify'), (
        'ACK a capability make it enabled.')
    assert manager.enabled == frozenset({'away-notify'})

    raw = 'CAP * ACK :account-tag'
    with mockbot.sopel_wrapper(
        triggerfactory(mockbot, raw), mockrule
    ) as wrapped:
        assert manager.handle_ack(wrapped, wrapped.trigger) == ('account-tag',)
    assert not manager.is_available('away-notify')
    assert not manager.is_available('account-tag')
    assert manager.is_enabled('away-notify')
    assert manager.is_enabled('account-tag')
    assert manager.enabled == frozenset({'away-notify', 'account-tag'})


def test_capabilities_ack_multiple(mockbot, triggerfactory, mockrule):
    raw = 'CAP * ACK :away-notify account-tag'
    manager = Capabilities()

    with mockbot.sopel_wrapper(
        triggerfactory(mockbot, raw), mockrule
    ) as wrapped:
        assert manager.handle_ack(wrapped, wrapped.trigger) == (
            'account-tag', 'away-notify',
        )
    assert not manager.is_available('away-notify')
    assert not manager.is_available('account-tag')
    assert manager.is_enabled('away-notify')
    assert manager.is_enabled('account-tag')
    assert manager.enabled == frozenset({'away-notify', 'account-tag'})

    raw = 'CAP * ACK :echo-message'

    with mockbot.sopel_wrapper(
        triggerfactory(mockbot, raw), mockrule
    ) as wrapped:
        assert manager.handle_ack(wrapped, wrapped.trigger) == ('echo-message',)
    assert not manager.is_available('away-notify')
    assert not manager.is_available('account-tag')
    assert not manager.is_available('echo-message')
    assert manager.is_enabled('away-notify')
    assert manager.is_enabled('account-tag')
    assert manager.is_enabled('echo-message')
    assert manager.enabled == frozenset({
        'away-notify', 'account-tag', 'echo-message',
    })


def test_capabilities_ack_disable_prefix(mockbot, triggerfactory, mockrule):
    raw = 'CAP * ACK :away-notify account-tag -echo-message'
    manager = Capabilities()
    with mockbot.sopel_wrapper(
        triggerfactory(mockbot, raw), mockrule
    ) as wrapped:
        assert manager.handle_ack(wrapped, wrapped.trigger) == (
            '-echo-message',
            'account-tag',
            'away-notify',
        )
    assert not manager.is_available('away-notify')
    assert not manager.is_available('account-tag')
    assert not manager.is_available('echo-message')
    assert manager.is_enabled('away-notify')
    assert manager.is_enabled('account-tag')
    assert not manager.is_enabled('echo-message')
    assert manager.enabled == frozenset({'away-notify', 'account-tag'})

    raw = 'CAP * ACK :-account-tag'
    with mockbot.sopel_wrapper(
        triggerfactory(mockbot, raw), mockrule
    ) as wrapped:
        assert manager.handle_ack(wrapped, wrapped.trigger) == (
            '-account-tag',
        )
    assert not manager.is_available('away-notify')
    assert not manager.is_available('account-tag')
    assert manager.is_enabled('away-notify')
    assert not manager.is_enabled('account-tag'), (
        'account-tag must be disabled now')
    assert not manager.is_enabled('echo-message')
    assert manager.enabled == frozenset({'away-notify'})


def test_capabilities_nak(mockbot, triggerfactory, mockrule):
    raw = 'CAP * NAK :away-notify'
    manager = Capabilities()
    with mockbot.sopel_wrapper(
        triggerfactory(mockbot, raw), mockrule
    ) as wrapped:
        assert manager.handle_nak(wrapped, wrapped.trigger) == ('away-notify',)
    assert not manager.is_available('away-notify'), (
        'NAK a capability does not update server availability.')
    assert not manager.is_enabled('away-notify'), (
        'NAK a capability make it not enabled.')
    assert not manager.enabled

    raw = 'CAP * NAK :account-tag'
    with mockbot.sopel_wrapper(
        triggerfactory(mockbot, raw), mockrule
    ) as wrapped:
        assert manager.handle_nak(wrapped, wrapped.trigger) == ('account-tag',)
    assert not manager.is_available('away-notify')
    assert not manager.is_available('account-tag')
    assert not manager.is_enabled('away-notify')
    assert not manager.is_enabled('account-tag')
    assert not manager.enabled


def test_capabilities_nack_multiple(mockbot, triggerfactory, mockrule):
    raw = 'CAP * NAK :away-notify account-tag'
    manager = Capabilities()
    with mockbot.sopel_wrapper(
        triggerfactory(mockbot, raw), mockrule
    ) as wrapped:
        assert manager.handle_nak(wrapped, wrapped.trigger) == (
            'account-tag', 'away-notify',
        )
    assert not manager.is_available('away-notify')
    assert not manager.is_available('account-tag')
    assert not manager.is_enabled('away-notify')
    assert not manager.is_enabled('account-tag')
    assert not manager.enabled

    raw = 'CAP * NAK :echo-message'
    with mockbot.sopel_wrapper(
        triggerfactory(mockbot, raw), mockrule
    ) as wrapped:
        assert manager.handle_nak(wrapped, wrapped.trigger) == ('echo-message',)
    assert not manager.is_available('away-notify')
    assert not manager.is_available('account-tag')
    assert not manager.is_available('echo-message')
    assert not manager.is_enabled('away-notify')
    assert not manager.is_enabled('account-tag')
    assert not manager.is_enabled('echo-message')
    assert not manager.enabled


def test_capabilities_ack_and_nack(mockbot, triggerfactory, mockrule):
    manager = Capabilities()

    # ACK a single CAP
    raw = 'CAP * ACK :echo-message'
    with mockbot.sopel_wrapper(
        triggerfactory(mockbot, raw), mockrule
    ) as wrapped:
        assert manager.handle_ack(wrapped, wrapped.trigger) == (
            'echo-message',
        )

    # ACK multiple CAPs
    raw = 'CAP * ACK :away-notify account-tag'
    with mockbot.sopel_wrapper(
        triggerfactory(mockbot, raw), mockrule
    ) as wrapped:
        assert manager.handle_ack(wrapped, wrapped.trigger) == (
            'account-tag', 'away-notify',
        )

    # NAK a single CAP
    raw = 'CAP * NAK :batch'
    with mockbot.sopel_wrapper(
        triggerfactory(mockbot, raw), mockrule
    ) as wrapped:
        assert manager.handle_nak(wrapped, wrapped.trigger) == (
            'batch',
        )

    # NAK multiple CAPs
    raw = 'CAP * NAK :batch echo-message'
    with mockbot.sopel_wrapper(
        triggerfactory(mockbot, raw), mockrule
    ) as wrapped:
        assert manager.handle_nak(wrapped, wrapped.trigger) == (
            'batch', 'echo-message',
        )

    # check the result
    assert not manager.available, 'ACK/NAK do not change availability.'
    assert manager.enabled == frozenset({
        'echo-message', 'away-notify', 'account-tag',
    })


def test_capabilities_new(mockbot, triggerfactory, mockrule):
    manager = Capabilities()

    # NEW CAP
    raw = 'CAP * NEW :echo-message'
    with mockbot.sopel_wrapper(
        triggerfactory(mockbot, raw), mockrule
    ) as wrapped:
        assert manager.handle_new(wrapped, wrapped.trigger) == (
            'echo-message',
        )
    assert manager.is_available('echo-message')
    assert not manager.is_enabled('echo-message')
    assert manager.available == {'echo-message': None}
    assert not manager.enabled

    # NEW CAP again
    raw = 'CAP * NEW :away-notify'
    with mockbot.sopel_wrapper(
        triggerfactory(mockbot, raw), mockrule
    ) as wrapped:
        assert manager.handle_new(wrapped, wrapped.trigger) == (
            'away-notify',
        )
    assert manager.is_available('echo-message')
    assert manager.is_available('away-notify')
    assert not manager.is_enabled('echo-message')
    assert not manager.is_enabled('away-notify')
    assert manager.available == {'echo-message': None, 'away-notify': None}
    assert not manager.enabled


def test_capabilities_new_multiple(mockbot, triggerfactory):
    manager = Capabilities()

    raw = 'CAP * NEW :echo-message away-notify'
    wrapped = triggerfactory.wrapper(mockbot, raw)
    assert manager.handle_new(wrapped, wrapped.trigger) == (
        'away-notify', 'echo-message',
    )
    assert manager.is_available('echo-message')
    assert manager.is_available('away-notify')
    assert not manager.is_enabled('echo-message')
    assert not manager.is_enabled('away-notify')
    assert manager.available == {'echo-message': None, 'away-notify': None}
    assert not manager.enabled


def test_capabilities_new_params(mockbot, triggerfactory):
    manager = Capabilities()

    # NEW CAP
    raw = 'CAP * NEW :sasl=PLAIN,EXTERNAL'
    wrapped = triggerfactory.wrapper(mockbot, raw)
    assert manager.handle_new(wrapped, wrapped.trigger) == (
        'sasl',
    )
    assert manager.is_available('sasl')
    assert not manager.is_enabled('sasl')
    assert manager.available == {'sasl': 'PLAIN,EXTERNAL'}
    assert not manager.enabled


def test_capabilities_del(mockbot, triggerfactory):
    manager = Capabilities()

    # DEL CAP
    raw = 'CAP * DEL :echo-message'
    wrapped = triggerfactory.wrapper(mockbot, raw)
    assert manager.handle_del(wrapped, wrapped.trigger) == (
        'echo-message',
    )
    assert not manager.is_available('echo-message')
    assert not manager.is_enabled('echo-message')
    assert not manager.available
    assert not manager.enabled


def test_capabilities_del_available(mockbot, triggerfactory, mockrule):
    manager = Capabilities()

    # NEW CAP
    raw = 'CAP * NEW :echo-message'
    with mockbot.sopel_wrapper(
        triggerfactory(mockbot, raw), mockrule
    ) as wrapped:
        manager.handle_new(wrapped, wrapped.trigger)

    # DEL CAP
    raw = 'CAP * DEL :echo-message'
    with mockbot.sopel_wrapper(
        triggerfactory(mockbot, raw), mockrule
    ) as wrapped:
        assert manager.handle_del(wrapped, wrapped.trigger) == (
            'echo-message',
        )
    assert not manager.is_available('echo-message')
    assert not manager.is_enabled('echo-message')
    assert not manager.available
    assert not manager.enabled


def test_capabilities_del_enabled(mockbot, triggerfactory, mockrule):
    manager = Capabilities()

    # NEW CAP
    raw = 'CAP * NEW :echo-message'
    with mockbot.sopel_wrapper(
        triggerfactory(mockbot, raw), mockrule
    ) as wrapped:
        manager.handle_new(wrapped, wrapped.trigger)

    # ACK CAP
    raw = 'CAP * ACK :echo-message'
    with mockbot.sopel_wrapper(
        triggerfactory(mockbot, raw), mockrule
    ) as wrapped:
        manager.handle_ack(wrapped, wrapped.trigger)

    # DEL CAP
    raw = 'CAP * DEL :echo-message'
    with mockbot.sopel_wrapper(
        triggerfactory(mockbot, raw), mockrule
    ) as wrapped:
        assert manager.handle_del(wrapped, wrapped.trigger) == (
            'echo-message',
        )
    assert not manager.is_available('echo-message')
    assert not manager.is_enabled('echo-message')
    assert not manager.available
    assert not manager.enabled
