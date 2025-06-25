"""Test ``sopel.irc.capabilities``."""
from __future__ import annotations

import typing

import pytest

from sopel.irc.capabilities import Capabilities, CapabilityInfo


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
    assert manager.handle_ls(wrapped, wrapped._trigger)
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
    assert manager.handle_ls(wrapped, wrapped._trigger)
    assert manager.is_available('sasl')
    assert not manager.is_enabled('sasl')
    assert manager.available == {'sasl': 'EXTERNAL,PLAIN'}

    expected = CapabilityInfo('sasl', 'EXTERNAL,PLAIN', True, False)
    assert manager.get_capability_info('sasl') == expected


def test_capabilities_ls_multiline(mockbot, triggerfactory):
    raw = 'CAP * LS * :away-notify'
    wrapped = triggerfactory.wrapper(mockbot, raw)
    manager = Capabilities()
    assert not manager.handle_ls(wrapped, wrapped._trigger)
    assert manager.is_available('away-notify')
    assert not manager.is_enabled('away-notify')
    assert manager.available == {'away-notify': None}

    raw = 'CAP * LS :account-tag'
    wrapped = triggerfactory.wrapper(mockbot, raw)
    assert manager.handle_ls(wrapped, wrapped._trigger)
    assert manager.is_available('away-notify')
    assert manager.is_available('account-tag')
    assert not manager.is_enabled('away-notify')
    assert not manager.is_enabled('account-tag')
    assert manager.available == {'away-notify': None, 'account-tag': None}


def test_capabilities_ls_trailing_space(mockbot, triggerfactory: TriggerFactory):
    raw = 'CAP * LS :away-notify '
    wrapped = triggerfactory.wrapper(mockbot, raw)
    manager = Capabilities()
    assert manager.handle_ls(wrapped, wrapped._trigger)
    assert manager.is_available('away-notify')
    assert not manager.is_enabled('away-notify')
    assert manager.available == {'away-notify': None}
    assert not manager.enabled

    expected = CapabilityInfo('away-notify', None, True, False)
    assert manager.get_capability_info('away-notify') == expected


def test_capabilities_ack(mockbot, triggerfactory):
    raw = 'CAP * ACK :away-notify'
    wrapped = triggerfactory.wrapper(mockbot, raw)
    manager = Capabilities()
    assert manager.handle_ack(wrapped, wrapped._trigger) == ('away-notify',)
    assert not manager.is_available('away-notify'), (
        'ACK a capability does not update server availability.')
    assert manager.is_enabled('away-notify'), (
        'ACK a capability make it enabled.')
    assert manager.enabled == frozenset({'away-notify'})

    raw = 'CAP * ACK :account-tag'
    wrapped = triggerfactory.wrapper(mockbot, raw)
    assert manager.handle_ack(wrapped, wrapped._trigger) == ('account-tag',)
    assert not manager.is_available('away-notify')
    assert not manager.is_available('account-tag')
    assert manager.is_enabled('away-notify')
    assert manager.is_enabled('account-tag')
    assert manager.enabled == frozenset({'away-notify', 'account-tag'})


def test_capabilities_ack_trailing_space(mockbot, triggerfactory):
    raw = 'CAP * ACK :away-notify '
    wrapped = triggerfactory.wrapper(mockbot, raw)
    manager = Capabilities()
    assert manager.handle_ack(wrapped, wrapped._trigger) == ('away-notify',)
    assert not manager.is_available('away-notify'), (
        'ACK a capability does not update server availability.')
    assert manager.is_enabled('away-notify'), (
        'ACK a capability make it enabled.')
    assert manager.enabled == frozenset({'away-notify'})


def test_capabilities_ack_multiple(mockbot, triggerfactory):
    raw = 'CAP * ACK :away-notify account-tag'
    wrapped = triggerfactory.wrapper(mockbot, raw)
    manager = Capabilities()
    assert manager.handle_ack(wrapped, wrapped._trigger) == (
        'account-tag', 'away-notify',
    )
    assert not manager.is_available('away-notify')
    assert not manager.is_available('account-tag')
    assert manager.is_enabled('away-notify')
    assert manager.is_enabled('account-tag')
    assert manager.enabled == frozenset({'away-notify', 'account-tag'})

    raw = 'CAP * ACK :echo-message'
    wrapped = triggerfactory.wrapper(mockbot, raw)
    assert manager.handle_ack(wrapped, wrapped._trigger) == ('echo-message',)
    assert not manager.is_available('away-notify')
    assert not manager.is_available('account-tag')
    assert not manager.is_available('echo-message')
    assert manager.is_enabled('away-notify')
    assert manager.is_enabled('account-tag')
    assert manager.is_enabled('echo-message')
    assert manager.enabled == frozenset({
        'away-notify', 'account-tag', 'echo-message',
    })


def test_capabilities_ack_disable_prefix(mockbot, triggerfactory):
    raw = 'CAP * ACK :away-notify account-tag -echo-message'
    wrapped = triggerfactory.wrapper(mockbot, raw)
    manager = Capabilities()
    assert manager.handle_ack(wrapped, wrapped._trigger) == (
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
    wrapped = triggerfactory.wrapper(mockbot, raw)
    assert manager.handle_ack(wrapped, wrapped._trigger) == (
        '-account-tag',
    )
    assert not manager.is_available('away-notify')
    assert not manager.is_available('account-tag')
    assert manager.is_enabled('away-notify')
    assert not manager.is_enabled('account-tag'), (
        'account-tag must be disabled now')
    assert not manager.is_enabled('echo-message')
    assert manager.enabled == frozenset({'away-notify'})


def test_capabilities_nak(mockbot, triggerfactory):
    raw = 'CAP * NAK :away-notify'
    wrapped = triggerfactory.wrapper(mockbot, raw)
    manager = Capabilities()
    assert manager.handle_nak(wrapped, wrapped._trigger) == ('away-notify',)
    assert not manager.is_available('away-notify'), (
        'NAK a capability does not update server availability.')
    assert not manager.is_enabled('away-notify'), (
        'NAK a capability make it not enabled.')
    assert not manager.enabled

    raw = 'CAP * NAK :account-tag'
    wrapped = triggerfactory.wrapper(mockbot, raw)
    assert manager.handle_nak(wrapped, wrapped._trigger) == ('account-tag',)
    assert not manager.is_available('away-notify')
    assert not manager.is_available('account-tag')
    assert not manager.is_enabled('away-notify')
    assert not manager.is_enabled('account-tag')
    assert not manager.enabled


def test_capabilities_nak_trailing_space(mockbot, triggerfactory):
    raw = 'CAP * NAK :away-notify '
    wrapped = triggerfactory.wrapper(mockbot, raw)
    manager = Capabilities()
    assert manager.handle_nak(wrapped, wrapped._trigger) == ('away-notify',)
    assert not manager.is_available('away-notify'), (
        'NAK a capability does not update server availability.')
    assert not manager.is_enabled('away-notify'), (
        'NAK a capability make it not enabled.')
    assert not manager.enabled


def test_capabilities_nak_multiple(mockbot, triggerfactory):
    raw = 'CAP * NAK :away-notify account-tag'
    wrapped = triggerfactory.wrapper(mockbot, raw)
    manager = Capabilities()
    assert manager.handle_nak(wrapped, wrapped._trigger) == (
        'account-tag', 'away-notify',
    )
    assert not manager.is_available('away-notify')
    assert not manager.is_available('account-tag')
    assert not manager.is_enabled('away-notify')
    assert not manager.is_enabled('account-tag')
    assert not manager.enabled

    raw = 'CAP * NAK :echo-message'
    wrapped = triggerfactory.wrapper(mockbot, raw)
    assert manager.handle_nak(wrapped, wrapped._trigger) == ('echo-message',)
    assert not manager.is_available('away-notify')
    assert not manager.is_available('account-tag')
    assert not manager.is_available('echo-message')
    assert not manager.is_enabled('away-notify')
    assert not manager.is_enabled('account-tag')
    assert not manager.is_enabled('echo-message')
    assert not manager.enabled


def test_capabilities_ack_and_nak(mockbot, triggerfactory):
    manager = Capabilities()

    # ACK a single CAP
    raw = 'CAP * ACK :echo-message'
    wrapped = triggerfactory.wrapper(mockbot, raw)
    assert manager.handle_ack(wrapped, wrapped._trigger) == (
        'echo-message',
    )

    # ACK multiple CAPs
    raw = 'CAP * ACK :away-notify account-tag'
    wrapped = triggerfactory.wrapper(mockbot, raw)
    assert manager.handle_ack(wrapped, wrapped._trigger) == (
        'account-tag', 'away-notify',
    )

    # NAK a single CAP
    raw = 'CAP * NAK :batch'
    wrapped = triggerfactory.wrapper(mockbot, raw)
    assert manager.handle_nak(wrapped, wrapped._trigger) == (
        'batch',
    )

    # NAK multiple CAPs
    raw = 'CAP * NAK :batch echo-message'
    wrapped = triggerfactory.wrapper(mockbot, raw)
    assert manager.handle_nak(wrapped, wrapped._trigger) == (
        'batch', 'echo-message',
    )

    # check the result
    assert not manager.available, 'ACK/NAK do not change availability.'
    assert manager.enabled == frozenset({
        'echo-message', 'away-notify', 'account-tag',
    })


def test_capabilities_new(mockbot, triggerfactory):
    manager = Capabilities()

    # NEW CAP
    raw = 'CAP * NEW :echo-message'
    wrapped = triggerfactory.wrapper(mockbot, raw)
    assert manager.handle_new(wrapped, wrapped._trigger) == (
        'echo-message',
    )
    assert manager.is_available('echo-message')
    assert not manager.is_enabled('echo-message')
    assert manager.available == {'echo-message': None}
    assert not manager.enabled

    # NEW CAP again
    raw = 'CAP * NEW :away-notify'
    wrapped = triggerfactory.wrapper(mockbot, raw)
    assert manager.handle_new(wrapped, wrapped._trigger) == (
        'away-notify',
    )
    assert manager.is_available('echo-message')
    assert manager.is_available('away-notify')
    assert not manager.is_enabled('echo-message')
    assert not manager.is_enabled('away-notify')
    assert manager.available == {'echo-message': None, 'away-notify': None}
    assert not manager.enabled


def test_capabilities_new_trailing_space(mockbot, triggerfactory):
    manager = Capabilities()

    # NEW CAP
    raw = 'CAP * NEW :echo-message '
    wrapped = triggerfactory.wrapper(mockbot, raw)
    assert manager.handle_new(wrapped, wrapped._trigger) == (
        'echo-message',
    )
    assert manager.is_available('echo-message')
    assert not manager.is_enabled('echo-message')
    assert manager.available == {'echo-message': None}
    assert not manager.enabled


def test_capabilities_new_multiple(mockbot, triggerfactory):
    manager = Capabilities()

    raw = 'CAP * NEW :echo-message away-notify'
    wrapped = triggerfactory.wrapper(mockbot, raw)
    assert manager.handle_new(wrapped, wrapped._trigger) == (
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
    assert manager.handle_new(wrapped, wrapped._trigger) == (
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
    assert manager.handle_del(wrapped, wrapped._trigger) == (
        'echo-message',
    )
    assert not manager.is_available('echo-message')
    assert not manager.is_enabled('echo-message')
    assert not manager.available
    assert not manager.enabled


def test_capabilities_del_trailing_space(mockbot, triggerfactory):
    manager = Capabilities()

    # DEL CAP
    raw = 'CAP * DEL :echo-message '
    wrapped = triggerfactory.wrapper(mockbot, raw)
    assert manager.handle_del(wrapped, wrapped._trigger) == (
        'echo-message',
    )
    assert not manager.is_available('echo-message')
    assert not manager.is_enabled('echo-message')
    assert not manager.available
    assert not manager.enabled


def test_capabilities_del_available(mockbot, triggerfactory):
    manager = Capabilities()

    # NEW CAP
    raw = 'CAP * NEW :echo-message'
    wrapped = triggerfactory.wrapper(mockbot, raw)
    manager.handle_new(wrapped, wrapped._trigger)

    # DEL CAP
    raw = 'CAP * DEL :echo-message'
    wrapped = triggerfactory.wrapper(mockbot, raw)
    assert manager.handle_del(wrapped, wrapped._trigger) == (
        'echo-message',
    )
    assert not manager.is_available('echo-message')
    assert not manager.is_enabled('echo-message')
    assert not manager.available
    assert not manager.enabled


def test_capabilities_del_enabled(mockbot, triggerfactory):
    manager = Capabilities()

    # NEW CAP
    raw = 'CAP * NEW :echo-message'
    wrapped = triggerfactory.wrapper(mockbot, raw)
    manager.handle_new(wrapped, wrapped._trigger)

    # ACK CAP
    raw = 'CAP * ACK :echo-message'
    wrapped = triggerfactory.wrapper(mockbot, raw)
    manager.handle_ack(wrapped, wrapped._trigger)

    # DEL CAP
    raw = 'CAP * DEL :echo-message'
    wrapped = triggerfactory.wrapper(mockbot, raw)
    assert manager.handle_del(wrapped, wrapped._trigger) == (
        'echo-message',
    )
    assert not manager.is_available('echo-message')
    assert not manager.is_enabled('echo-message')
    assert not manager.available
    assert not manager.enabled
