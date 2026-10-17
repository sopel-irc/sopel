"""Test behavior of CAP management by ``sopel.coretasks``"""
from __future__ import annotations

from typing import Tuple, TYPE_CHECKING

import pytest

from sopel import config, plugin
from sopel.tests import rawlist


if TYPE_CHECKING:
    from sopel.bot import Sopel, SopelWrapper
    from sopel.config import Config
    from sopel.tests.factories import BotFactory, ConfigFactory


TMP_CONFIG = """
[core]
owner = Uowner
nick = TestBot
enable = coretasks
"""


@pytest.fixture
def tmpconfig(configfactory: ConfigFactory) -> Config:
    return configfactory('conf.ini', TMP_CONFIG)


@pytest.fixture
def mockbot(tmpconfig: Config, botfactory: BotFactory) -> Sopel:
    mockbot = botfactory.preloaded(tmpconfig)
    mockbot.backend.connected = True
    return mockbot


def test_cap_ls_ack(mockbot: Sopel):
    mockbot.on_message(
        ':irc.example.com CAP * LS :echo-message multi-prefix example/cap')
    assert mockbot.backend.message_sent == rawlist(
        'CAP REQ :echo-message',
        'CAP REQ :multi-prefix',
    )

    mockbot.on_message(':irc.example.com CAP * ACK :echo-message')
    assert mockbot.backend.message_sent[2:] == []

    mockbot.on_message(':irc.example.com CAP * ACK :example/cap')
    assert mockbot.backend.message_sent[2:] == [], (
        'Unknown cap request must not count for completion of anything.')

    mockbot.on_message(':irc.example.com CAP * ACK :multi-prefix')
    assert mockbot.backend.message_sent[2:] == rawlist(
        'CAP END',
    )

    assert mockbot.capabilities.is_enabled('echo-message')
    assert mockbot.capabilities.is_enabled('example/cap')
    assert mockbot.capabilities.is_enabled('multi-prefix')


def test_cap_ls_nak(mockbot: Sopel):
    mockbot.on_message(':irc.example.com CAP * LS :echo-message multi-prefix')
    assert mockbot.backend.message_sent == rawlist(
        'CAP REQ :echo-message',
        'CAP REQ :multi-prefix',
    )

    mockbot.on_message(':irc.example.com CAP * NAK :echo-message')
    assert mockbot.backend.message_sent[2:] == []

    mockbot.on_message(':irc.example.com CAP * NAK :example/cap')
    assert mockbot.backend.message_sent[2:] == [], (
        'Unknown cap request must not count for completion of anything.')

    mockbot.on_message(':irc.example.com CAP * NAK :multi-prefix')
    assert mockbot.backend.message_sent[2:] == rawlist(
        'CAP END',
    )

    assert not mockbot.capabilities.is_enabled('echo-message')
    assert not mockbot.capabilities.is_enabled('example/cap')
    assert not mockbot.capabilities.is_enabled('multi-prefix')


def test_cap_ls_empty(mockbot: Sopel):
    mockbot.on_message(':irc.example.com CAP * LS :')
    assert mockbot.backend.message_sent == rawlist(
        'CAP END',
    )


def test_cap_ls_unknown(mockbot: Sopel):
    mockbot.on_message(':irc.example.com CAP * LS :example/cap')
    assert mockbot.backend.message_sent == rawlist(
        'CAP END',
    )


def test_cap_ls_multiline(mockbot: Sopel):
    mockbot.on_message(':irc.example.com CAP * LS * :echo-message')
    assert mockbot.backend.message_sent == [], (
        'LS is not done, we must not send request yet.')

    mockbot.on_message(':irc.example.com CAP * LS :multi-prefix')
    assert mockbot.backend.message_sent == rawlist(
        'CAP REQ :echo-message',
        'CAP REQ :multi-prefix',
    )

    mockbot.on_message(':irc.example.com CAP * ACK :echo-message')
    assert mockbot.backend.message_sent[2:] == []

    mockbot.on_message(':irc.example.com CAP * NAK :multi-prefix')
    assert mockbot.backend.message_sent[2:] == rawlist(
        'CAP END',
    )

    assert mockbot.capabilities.is_enabled('echo-message')
    assert not mockbot.capabilities.is_enabled('multi-prefix')


def test_cap_ls_all(mockbot: Sopel):
    capabilities = (
        'account-notify',
        'account-tag',
        'away-notify',
        'cap-notify',
        'chghost',
        'echo-message',
        'extended-join',
        'message-tags',
        'multi-prefix',
        'sasl=PLAIN,EXTERNAL',
        'server-time',
        'userhost-in-names',
    )
    part1 = ' '.join(capabilities[:4])
    part2 = ' '.join(capabilities[4:])
    unrequested_part = ' '.join(('chathistory', 'metadata'))
    mockbot.on_message(':irc.example.com CAP * LS * :%s' % part1)
    mockbot.on_message(':irc.example.com CAP * LS * :%s' % unrequested_part)
    mockbot.on_message(':irc.example.com CAP * LS :%s' % part2)

    assert mockbot.backend.message_sent == rawlist(
        'CAP REQ :echo-message',
        'CAP REQ :multi-prefix',
        'CAP REQ :away-notify',
        'CAP REQ :chghost',
        'CAP REQ :cap-notify',
        'CAP REQ :server-time',
        'CAP REQ :userhost-in-names',
        'CAP REQ :message-tags',
        'CAP REQ :account-notify',
        'CAP REQ :extended-join',
        'CAP REQ :account-tag',
        'CAP REQ :sasl',
    )
    n = len(mockbot.backend.message_sent)

    # now we have to ACK or NAK capabilities for the negotiation to end
    mockbot.on_message(':irc.example.com CAP * ACK :echo-message')
    mockbot.on_message(':irc.example.com CAP * ACK :multi-prefix')
    mockbot.on_message(':irc.example.com CAP * ACK :away-notify')
    mockbot.on_message(':irc.example.com CAP * ACK :chghost')
    mockbot.on_message(':irc.example.com CAP * ACK :cap-notify')
    mockbot.on_message(':irc.example.com CAP * ACK :server-time')
    mockbot.on_message(':irc.example.com CAP * ACK :userhost-in-names')
    mockbot.on_message(':irc.example.com CAP * ACK :message-tags')
    mockbot.on_message(':irc.example.com CAP * ACK :account-notify')
    mockbot.on_message(':irc.example.com CAP * ACK :extended-join')
    mockbot.on_message(':irc.example.com CAP * ACK :account-tag')
    assert mockbot.backend.message_sent[n:] == [], 'No CAP END yet!'

    # final capability to ACK
    mockbot.on_message(':irc.example.com CAP * ACK :sasl')
    assert mockbot.backend.message_sent[n:] == rawlist(
        'CAP END'
    )


def test_cap_ack_auth_related_cap(mockbot: Sopel):
    mockbot.on_message(
        ':irc.example.com CAP * LS :account-notify extended-join account-tag')

    assert mockbot.backend.message_sent == rawlist(
        'CAP REQ :account-notify',
        'CAP REQ :extended-join',
        'CAP REQ :account-tag',
    )

    mockbot.on_message(':irc.example.com CAP * ACK :account-notify')
    assert mockbot.backend.message_sent[3:] == []
    mockbot.on_message(':irc.example.com CAP * ACK :extended-join')
    assert mockbot.backend.message_sent[3:] == []
    mockbot.on_message(':irc.example.com CAP * ACK :account-tag')

    assert mockbot.capabilities.is_enabled('account-notify')
    assert mockbot.capabilities.is_enabled('extended-join')
    assert mockbot.capabilities.is_enabled('account-tag')
    assert mockbot.cap_requests.is_complete
    assert mockbot.backend.message_sent[3:] == rawlist(
        'CAP END',
    )


def test_cap_nak_auth_related_cap(mockbot: Sopel):
    mockbot.on_message(
        ':irc.example.com CAP * LS :account-notify extended-join account-tag')

    assert mockbot.backend.message_sent == rawlist(
        'CAP REQ :account-notify',
        'CAP REQ :extended-join',
        'CAP REQ :account-tag',
    )

    mockbot.on_message(':irc.example.com CAP * NAK :account-notify')
    assert mockbot.backend.message_sent[3:] == []
    mockbot.on_message(':irc.example.com CAP * NAK :extended-join')
    assert mockbot.backend.message_sent[3:] == []
    mockbot.on_message(':irc.example.com CAP * NAK :account-tag')

    assert not mockbot.capabilities.is_enabled('account-notify')
    assert not mockbot.capabilities.is_enabled('extended-join')
    assert not mockbot.capabilities.is_enabled('account-tag')
    assert mockbot.cap_requests.is_complete
    assert mockbot.backend.message_sent[3:] == rawlist(
        'CAP END',
    )


def test_cap_ack_config_error(mockbot: Sopel):
    @plugin.capability('example/cap')
    def cap_req(
            cap_req: Tuple[str, ...],
            bot: SopelWrapper,
            acknowledged: bool,
    ) -> None:
        raise config.ConfigurationError('Improperly configured.')

    mockbot.cap_requests.register('test', cap_req)
    mockbot.on_message(':irc.example.com CAP * LS :example/cap')
    assert mockbot.backend.message_sent == rawlist(
        'CAP REQ :example/cap',
    )

    mockbot.on_message(':irc.example.com CAP * ACK :example/cap')
    assert mockbot.backend.message_sent[1:] == rawlist(
        'CAP END',
        'QUIT :Configuration error.',
    )


def test_cap_ack_error(mockbot: Sopel):
    @plugin.capability('example/cap')
    def cap_req(
            cap_req: Tuple[str, ...],
            bot: SopelWrapper,
            acknowledged: bool,
    ) -> None:
        raise Exception('Random error.')

    mockbot.cap_requests.register('test', cap_req)
    mockbot.on_message(':irc.example.com CAP * LS :example/cap')
    assert mockbot.backend.message_sent == rawlist(
        'CAP REQ :example/cap',
    )

    mockbot.on_message(':irc.example.com CAP * ACK :example/cap')
    assert mockbot.backend.message_sent[1:] == rawlist(
        'CAP END',
        'QUIT :Error negotiating capabilities.',
    )


def test_cap_nak_config_error(mockbot: Sopel):
    @plugin.capability('example/cap')
    def cap_req(
            cap_req: Tuple[str, ...],
            bot: SopelWrapper,
            acknowledged: bool,
    ) -> None:
        raise config.ConfigurationError('Improperly configured.')

    mockbot.cap_requests.register('test', cap_req)
    mockbot.on_message(':irc.example.com CAP * LS :example/cap')
    assert mockbot.backend.message_sent == rawlist(
        'CAP REQ :example/cap',
    )

    mockbot.on_message(':irc.example.com CAP * NAK :example/cap')
    assert mockbot.backend.message_sent[1:] == rawlist(
        'CAP END',
        'QUIT :Configuration error.',
    )


def test_cap_nak_error(mockbot: Sopel):
    @plugin.capability('example/cap')
    def cap_req(
            cap_req: Tuple[str, ...],
            bot: SopelWrapper,
            acknowledged: bool,
    ) -> None:
        raise Exception('Random error.')

    mockbot.cap_requests.register('test', cap_req)
    mockbot.on_message(':irc.example.com CAP * LS :example/cap')
    assert mockbot.backend.message_sent == rawlist(
        'CAP REQ :example/cap',
    )

    mockbot.on_message(':irc.example.com CAP * NAK :example/cap')
    assert mockbot.backend.message_sent[1:] == rawlist(
        'CAP END',
        'QUIT :Error negotiating capabilities.',
    )


def test_cap_list(mockbot: Sopel):
    mockbot.on_message(':irc.example.com CAP * LIST :example/cap')
    assert mockbot.backend.message_sent == [], 'Nothing sent after a LIST'
    assert not mockbot.capabilities.is_enabled('example/cap'), (
        'LIST is not supported yet.')


def test_cap_new(mockbot: Sopel):
    assert not mockbot.capabilities.is_available('example/cap')
    mockbot.on_message(':irc.example.com CAP * NEW :example/cap')
    assert mockbot.backend.message_sent == [], 'Nothing sent after a NEW'
    assert mockbot.capabilities.is_available('example/cap')
    assert not mockbot.capabilities.is_enabled('example/cap')


def test_cap_del(mockbot: Sopel):
    mockbot.on_message(':irc.example.com CAP * LS :example/cap')
    mockbot.on_message(':irc.example.com CAP * ACK :example/cap')
    assert mockbot.backend.message_sent == rawlist(
        'CAP END'
    ), 'Capability negotiation must have ended.'
    assert mockbot.capabilities.is_available('example/cap')
    assert mockbot.capabilities.is_enabled('example/cap')

    mockbot.on_message(':irc.example.com CAP * DEL :example/cap')
    assert mockbot.backend.message_sent[1:] == [], 'Nothing sent after a DEL'
    assert not mockbot.capabilities.is_available('example/cap')
    assert not mockbot.capabilities.is_enabled('example/cap')
