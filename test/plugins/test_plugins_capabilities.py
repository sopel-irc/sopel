"""Tests for the ``sopel.plugins.handlers`` module."""
from __future__ import annotations

import pytest

from sopel import plugin
from sopel.plugins.capabilities import Manager
from sopel.plugins.rules import Rule
from sopel.tests import rawlist


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


def test_manager_empty():
    req_example = ('example/cap',)
    manager = Manager()
    assert not manager.registered
    assert not manager.acknowledged
    assert not manager.denied
    assert not manager.is_registered(req_example)
    assert not manager.is_requested(req_example)
    assert list(manager.get(req_example)) == []


def test_manager_register():
    manager = Manager()

    req_example = ('example/cap',)
    cap_example = plugin.capability(*req_example)
    manager.register('example', cap_example)

    assert manager.registered == {req_example}
    assert not manager.requested
    assert not manager.acknowledged
    assert not manager.denied
    assert manager.is_registered(req_example)
    assert not manager.is_requested(req_example)
    assert not manager.is_acknowledged(req_example)
    assert not manager.is_denied(req_example)

    expected = [('example', cap_example)]
    assert list(manager.get(req_example)) == expected
    assert list(manager.get(req_example, plugins=['example'])) == expected
    assert list(manager.get(req_example, plugins=['example2'])) == []

    req_example_2 = ('example/cap', 'example/cap2',)
    cap_example_2 = plugin.capability(*req_example_2)
    manager.register('example', cap_example_2)

    # no change in expectation
    assert list(manager.get(req_example)) == expected
    assert list(manager.get(req_example, plugins=['example'])) == expected
    assert list(manager.get(req_example, plugins=['example2'])) == []

    # new expectation
    expected = [('example', cap_example_2)]
    assert list(manager.get(req_example_2)) == expected
    assert list(manager.get(req_example_2, plugins=['example'])) == expected
    assert list(manager.get(req_example_2, plugins=['example2'])) == []

    # registered is now modified
    assert manager.registered == {req_example, req_example_2}

    # but other sets are not
    assert not manager.requested
    assert not manager.acknowledged
    assert not manager.denied

    # let's mess with the size of the capability request
    cap_too_long = plugin.capability('example/cap')
    cap_too_long._cap_req = cap_too_long._cap_req * 50
    with pytest.raises(RuntimeError):
        manager.register('example', cap_too_long)


def test_manager_register_multiple_plugins():
    manager = Manager()

    req_example = ('example/cap',)
    cap_example = plugin.capability(*req_example)
    cap_example_2 = plugin.capability(*req_example)
    manager.register('example', cap_example)
    manager.register('example2', cap_example_2)

    expected_item_1 = ('example', cap_example)
    expected_item_2 = ('example2', cap_example_2)
    expected = [
        expected_item_1,
        expected_item_2,
    ]

    assert list(manager.get(req_example)) == expected
    assert list(manager.get(req_example, plugins=['example'])) == [
        expected_item_1
    ]
    assert list(manager.get(req_example, plugins=['example2'])) == [
        expected_item_2
    ]


def test_manager_request_available(mockbot):
    manager = Manager()

    req_example = ('example/cap',)
    req_example_2 = ('example/cap', 'example/cap2',)
    cap_example = plugin.capability(*req_example)
    cap_example_2 = plugin.capability(*req_example_2)
    manager.register('example', cap_example)
    manager.register('example', cap_example_2)

    assert not manager.is_requested(req_example)
    assert not manager.is_requested(req_example_2)
    assert not manager.requested

    # request available
    manager.request_available(mockbot, req_example)

    assert manager.is_requested(req_example)
    assert not manager.is_requested(req_example_2)
    assert manager.requested == {req_example}

    assert mockbot.backend.message_sent == rawlist(
        'CAP REQ :example/cap'
    )


def test_manager_ack_request(mockbot, triggerfactory):
    manager = Manager()
    req_example = ('example/cap',)
    cap_example = plugin.capability(*req_example)
    manager.register('example', cap_example)
    manager.request_available(mockbot, req_example)

    raw = 'CAP * ACK :example/cap'
    wrapped = triggerfactory.wrapper(mockbot, raw)

    results = manager.acknowledge(wrapped, req_example)
    assert manager.registered == {req_example}
    assert manager.acknowledged == {req_example}
    assert not manager.denied
    assert results == [
        (True, None)  # no handler means no result
    ]


def test_manager_ack_unknown_request(mockbot, triggerfactory):
    manager = Manager()
    req_example = ('example/cap',)
    cap_example = plugin.capability(*req_example)
    manager.register('example', cap_example)
    manager.request_available(mockbot, req_example)

    raw = 'CAP * ACK :example/other'
    wrapped = triggerfactory.wrapper(mockbot, raw)

    results = manager.acknowledge(wrapped, ('example/other',))
    assert manager.registered == {req_example}
    assert not manager.acknowledged
    assert not manager.denied
    assert results is None


def test_manager_ack_nak_request(mockbot, triggerfactory, mockrule):
    manager = Manager()
    req_example = ('example/cap',)
    cap_example = plugin.capability(*req_example)
    manager.register('example', cap_example)
    manager.request_available(mockbot, req_example)

    raw = 'CAP * ACK :example/cap'

    with mockbot.sopel_wrapper(
        triggerfactory(mockbot, raw), mockrule
    ) as wrapped:
        manager.acknowledge(wrapped, req_example)

    raw = 'CAP * NAK :example/cap'

    with mockbot.sopel_wrapper(
        triggerfactory(mockbot, raw), mockrule
    ) as wrapped:
        manager.deny(wrapped, req_example)

    # reversed set
    assert not manager.acknowledged
    assert manager.denied == {req_example}


def test_manager_nak_request(mockbot, triggerfactory):
    manager = Manager()
    req_example = ('example/cap',)
    cap_example = plugin.capability(*req_example)
    manager.register('example', cap_example)
    manager.request_available(mockbot, req_example)

    raw = 'CAP * NAK :example/cap'
    wrapped = triggerfactory.wrapper(mockbot, raw)

    results = manager.deny(wrapped, req_example)
    assert manager.registered == {req_example}
    assert not manager.acknowledged
    assert manager.denied == {req_example}
    assert results == [
        (True, None)  # no handler means no result
    ], 'A denied request is still done.'


def test_manager_nak_unknown_request(mockbot, triggerfactory):
    manager = Manager()
    req_example = ('example/cap',)
    cap_example = plugin.capability(*req_example)
    manager.register('example', cap_example)
    manager.request_available(mockbot, req_example)

    raw = 'CAP * NAK :example/other'
    wrapped = triggerfactory.wrapper(mockbot, raw)

    results = manager.deny(wrapped, ('example/other',))
    assert manager.registered == {req_example}
    assert not manager.acknowledged
    assert not manager.denied
    assert results is None


def test_manager_nak_ack_request(mockbot, triggerfactory, mockrule):
    manager = Manager()
    req_example = ('example/cap',)
    cap_example = plugin.capability(*req_example)
    manager.register('example', cap_example)
    manager.request_available(mockbot, req_example)

    raw = 'CAP * NAK :example/cap'
    with mockbot.sopel_wrapper(
        triggerfactory(mockbot, raw), mockrule
    ) as wrapped:
        manager.deny(wrapped, req_example)

    raw = 'CAP * ACK :example/cap'
    with mockbot.sopel_wrapper(
        triggerfactory(mockbot, raw), mockrule
    ) as wrapped:
        manager.acknowledge(wrapped, req_example)

    # reversed set
    assert manager.acknowledged == {req_example}
    assert not manager.denied


def test_manager_complete_requests(mockbot, triggerfactory, mockrule):
    manager = Manager()
    req_example = ('example/cap',)
    req_example_2 = ('example/cap2', 'example/cap3')
    cap_example = plugin.capability(*req_example)
    cap_example_2 = plugin.capability(*req_example_2)
    manager.register('example', cap_example)
    manager.register('example_2', cap_example)
    manager.register('example_2', cap_example_2)
    manager.request_available(mockbot, req_example + req_example_2)

    raw = 'CAP * ACK :example/cap'
    with mockbot.sopel_wrapper(
        triggerfactory(mockbot, raw), mockrule
    ) as wrapped:
        manager.acknowledge(wrapped, req_example)

    raw = 'CAP * NAK :example/cap2 example/cap3'
    with mockbot.sopel_wrapper(
        triggerfactory(mockbot, raw), mockrule
    ) as wrapped:
        manager.deny(wrapped, req_example_2)

    assert manager.acknowledged == {req_example}
    assert manager.denied == {req_example_2}
    assert manager.is_complete

    # resume is not necessary
    assert manager.resume(req_example, 'example') == (True, True)


def test_manager_resume_requests(mockbot, triggerfactory, mockrule):
    manager = Manager()
    req_example = ('example/cap',)
    req_example_2 = ('example/cap2', 'example/cap3')
    cap_example = plugin.capability(*req_example)

    @plugin.capability(*req_example_2)
    def cap_example_2(bot, cap_req, acknowledge):
        return plugin.CapabilityNegotiation.CONTINUE

    manager.register('example', cap_example)
    manager.register('example_2', cap_example)
    manager.register('example_2', cap_example_2)
    manager.request_available(mockbot, req_example + req_example_2)

    raw = 'CAP * ACK :example/cap'
    with mockbot.sopel_wrapper(
        triggerfactory(mockbot, raw), mockrule
    ) as wrapped:
        manager.acknowledge(wrapped, req_example)

    raw = 'CAP * NAK :example/cap2 example/cap3'
    with mockbot.sopel_wrapper(
        triggerfactory(mockbot, raw), mockrule
    ) as wrapped:
        manager.deny(wrapped, req_example_2)

    assert manager.acknowledged == {req_example}
    assert manager.denied == {req_example_2}
    assert not manager.is_complete

    # resume
    was_completed, is_complete = manager.resume(req_example_2, 'example_2')
    assert not was_completed
    assert is_complete


def test_manager_resume_unknown_requests(mockbot, triggerfactory):
    manager = Manager()
    req_example = ('example/cap',)
    cap_example = plugin.capability(*req_example)
    manager.register('example', cap_example)
    manager.request_available(mockbot, req_example)

    # resume non-existing cap
    assert manager.resume(('example/cap2',), 'example') == (False, False)
    # resume non-existing plugin
    assert manager.resume(('example/cap',), 'example_2') == (False, False)

    # ACK
    raw = 'CAP * ACK :example/cap'
    wrapped = triggerfactory.wrapper(mockbot, raw)
    manager.acknowledge(wrapped, req_example)

    # resume non-existing cap
    assert manager.resume(('example/cap2',), 'example') == (True, True)
    # resume non-existing plugin
    assert manager.resume(('example/cap',), 'example_2') == (True, True)
