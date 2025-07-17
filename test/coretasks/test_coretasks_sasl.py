"""Test behavior of SASL by ``sopel.coretasks``"""
from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from sopel import coretasks
from sopel.tests import rawlist


if TYPE_CHECKING:
    from sopel.config import Config
    from sopel.tests.factories import BotFactory, ConfigFactory


TMP_CONFIG_NO_SASL = """
[core]
owner = Uowner
nick = TestBot
enable = coretasks
"""


TMP_CONFIG_SASL_DEFAULT = """
[core]
owner = Uowner
nick = TestBot
enable = coretasks
auth_method = sasl
auth_password = secret
"""


TMP_CONFIG_SASL_DEFAULT_EXACTLY_400 = """
[core]
owner = Uowner
nick = TestBot
enable = coretasks
auth_method = sasl
auth_password = {}
""".format('a' * 282)


TMP_CONFIG_SASL_DEFAULT_OVER_400 = """
[core]
owner = Uowner
nick = TestBot
enable = coretasks
auth_method = sasl
auth_password = {}
""".format('a' * 286)


TMP_CONFIG_SASL_NO_PASSWORD = """
[core]
owner = Uowner
nick = TestBot
enable = coretasks
auth_method = sasl
"""

TMP_CONFIG_SASL_EXTERNAL = """
[core]
owner = Uowner
nick = TestBot
enable = coretasks
auth_method = sasl
auth_target = EXTERNAL
"""


@pytest.fixture
def tmpconfig(configfactory: ConfigFactory) -> Config:
    return configfactory('conf.ini', TMP_CONFIG_SASL_DEFAULT)


def test_sasl_plain_token_generation() -> None:
    """Make sure SASL PLAIN tokens match the expected format."""
    assert (
        coretasks._make_sasl_plain_token('sopel', 'sasliscool') ==
        'sopel\x00sopel\x00sasliscool')


def test_sasl_not_configured(
    configfactory: ConfigFactory,
    botfactory: BotFactory,
) -> None:
    settings = configfactory('conf.ini', TMP_CONFIG_NO_SASL)
    mockbot = botfactory.preloaded(settings)
    mockbot.backend.connected = True

    # connect
    mockbot.on_connect()
    expected = 3
    assert len(mockbot.backend.message_sent) == expected, 'Sanity check failed'

    # list capabilities
    mockbot.on_message(':irc.example.com CAP * LS :sasl=PLAIN,EXTERNAL')
    assert mockbot.backend.message_sent[expected:] == rawlist(
        'CAP REQ :sasl'
    ), 'Only SASL was listed, only SASL must be requested.'
    n = len(mockbot.backend.message_sent)

    # ACK sasl capability
    mockbot.on_message(':irc.example.com CAP * ACK :sasl')
    assert mockbot.backend.message_sent[n:] == rawlist(
        'CAP END',
    ), 'SASL is requested but not configured, so negotiation must end.'


def test_sasl_plain(botfactory: BotFactory, tmpconfig) -> None:
    mockbot = botfactory.preloaded(tmpconfig, preloads=['coretasks'])
    mockbot.backend.connected = True

    # connect
    mockbot.on_connect()
    expected = 3
    assert len(mockbot.backend.message_sent) == expected, 'Sanity check failed'

    # list capabilities
    mockbot.on_message(':irc.example.com CAP * LS :sasl=PLAIN,EXTERNAL')
    assert mockbot.backend.message_sent[expected:] == rawlist(
        'CAP REQ :sasl'
    ), 'Only SASL was listed, only SASL must be requested.'
    n = len(mockbot.backend.message_sent)

    # ACK sasl capability
    mockbot.on_message(':irc.example.com CAP * ACK :sasl')
    assert mockbot.backend.message_sent[n:] == rawlist(
        'AUTHENTICATE PLAIN',
    )
    n = len(mockbot.backend.message_sent)

    # Server waiting for authentication
    mockbot.on_message(':irc.example.com AUTHENTICATE +')
    assert mockbot.backend.message_sent[n:] == rawlist(
        'AUTHENTICATE VGVzdEJvdABUZXN0Qm90AHNlY3JldA==',
    )
    n = len(mockbot.backend.message_sent)

    # Server accept authentication
    mockbot.on_message(
        ':irc.example.com 900 TestBot TestBot!sopel@example.com sopel '
        ':You are now logged in as TestBot')
    mockbot.on_message(
        ':irc.example.com 903 TestBot :SASL authentication successful')
    assert mockbot.backend.message_sent[n:] == rawlist(
        'CAP END',
    )


def test_sasl_plain_split_exactly_400(
    botfactory: BotFactory,
    configfactory: ConfigFactory,
) -> None:
    tmpconfig = configfactory('conf.ini', TMP_CONFIG_SASL_DEFAULT_EXACTLY_400)
    mockbot = botfactory.preloaded(tmpconfig, preloads=['coretasks'])
    mockbot.backend.connected = True

    # connect
    mockbot.on_connect()
    expected = 3
    assert len(mockbot.backend.message_sent) == expected, 'Sanity check failed'

    # list capabilities
    mockbot.on_message(':irc.example.com CAP * LS :sasl=PLAIN,EXTERNAL')
    assert mockbot.backend.message_sent[expected:] == rawlist(
        'CAP REQ :sasl'
    ), 'Only SASL was listed, only SASL must be requested.'
    n = len(mockbot.backend.message_sent)

    # ACK sasl capability
    mockbot.on_message(':irc.example.com CAP * ACK :sasl')
    assert mockbot.backend.message_sent[n:] == rawlist(
        'AUTHENTICATE PLAIN',
    )
    n = len(mockbot.backend.message_sent)

    # Server waiting for authentication
    mockbot.on_message(':irc.example.com AUTHENTICATE +')
    assert mockbot.backend.message_sent[n:] == rawlist(
        'AUTHENTICATE VGVzdEJvdABUZXN0Qm90AG' +
        ('FhYW' * 93) +
        'FhYQ==',
        'AUTHENTICATE +',
    )
    n = len(mockbot.backend.message_sent)

    # Server accept authentication
    mockbot.on_message(
        ':irc.example.com 900 TestBot TestBot!sopel@example.com sopel '
        ':You are now logged in as TestBot')
    mockbot.on_message(
        ':irc.example.com 903 TestBot :SASL authentication successful')
    assert mockbot.backend.message_sent[n:] == rawlist(
        'CAP END',
    )


def test_sasl_plain_split_over_400(
    botfactory: BotFactory,
    configfactory: ConfigFactory,
) -> None:
    tmpconfig = configfactory('conf.ini', TMP_CONFIG_SASL_DEFAULT_OVER_400)
    mockbot = botfactory.preloaded(tmpconfig, preloads=['coretasks'])
    mockbot.backend.connected = True

    # connect
    mockbot.on_connect()
    expected = 3
    assert len(mockbot.backend.message_sent) == expected, 'Sanity check failed'

    # list capabilities
    mockbot.on_message(':irc.example.com CAP * LS :sasl=PLAIN,EXTERNAL')
    assert mockbot.backend.message_sent[expected:] == rawlist(
        'CAP REQ :sasl'
    ), 'Only SASL was listed, only SASL must be requested.'
    n = len(mockbot.backend.message_sent)

    # ACK sasl capability
    mockbot.on_message(':irc.example.com CAP * ACK :sasl')
    assert mockbot.backend.message_sent[n:] == rawlist(
        'AUTHENTICATE PLAIN',
    )
    n = len(mockbot.backend.message_sent)

    # Server waiting for authentication
    mockbot.on_message(':irc.example.com AUTHENTICATE +')
    assert mockbot.backend.message_sent[n:] == rawlist(
        'AUTHENTICATE VGVzdEJvdABUZXN0Qm90AGFh' + ('YWFh' * 94),
        'AUTHENTICATE YWE=',
    )
    n = len(mockbot.backend.message_sent)

    # Server accept authentication
    mockbot.on_message(
        ':irc.example.com 900 TestBot TestBot!sopel@example.com sopel '
        ':You are now logged in as TestBot')
    mockbot.on_message(
        ':irc.example.com 903 TestBot :SASL authentication successful')
    assert mockbot.backend.message_sent[n:] == rawlist(
        'CAP END',
    )


def test_sasl_plain_no_password(
    botfactory: BotFactory,
    configfactory: ConfigFactory,
) -> None:
    tmpconfig = configfactory('conf.ini', TMP_CONFIG_SASL_NO_PASSWORD)
    mockbot = botfactory.preloaded(tmpconfig, preloads=['coretasks'])
    mockbot.backend.connected = True

    # connect and capability negotiation
    mockbot.on_connect()
    mockbot.on_message(':irc.example.com CAP * LS :sasl=PLAIN,EXTERNAL')
    n = len(mockbot.backend.message_sent)
    mockbot.on_message(':irc.example.com CAP * ACK :sasl')
    assert mockbot.backend.message_sent[n:] == rawlist(
        'CAP END',
        'QUIT :Configuration error.',
    ), 'No password is a configuration error and the bot must quit.'


def test_sasl_external_no_password(
    botfactory: BotFactory,
    configfactory: ConfigFactory,
) -> None:
    tmpconfig = configfactory("conf.ini", TMP_CONFIG_SASL_EXTERNAL)
    mockbot = botfactory.preloaded(tmpconfig, preloads=["coretasks"])
    mockbot.backend.connected = True

    # connect and capability negotiation
    mockbot.on_connect()
    mockbot.on_message(":irc.example.com CAP * LS :sasl=PLAIN,EXTERNAL")
    n = len(mockbot.backend.message_sent)
    mockbot.on_message(":irc.example.com CAP * ACK :sasl")
    assert mockbot.backend.message_sent[n:] == rawlist(
        "AUTHENTICATE EXTERNAL",
    ), "The bot should initiate SASL EXTERNAL authentication without a password set."
    n += 1
    mockbot.on_message("AUTHENTICATE +")
    assert mockbot.backend.message_sent[n:] == rawlist(
        "AUTHENTICATE +",
    ), "SASL EXTERNAL authentication should continue without a password set."
    n += 1

    mockbot.on_message(":irc.example.com 903 SopelTest :SASL authentication successful")
    assert mockbot.backend.message_sent[n:] == rawlist(
        "CAP END",
    ), "SASL success must resume capability negotiation."


def test_sasl_external_fail(
    botfactory: BotFactory,
    configfactory: ConfigFactory,
) -> None:
    tmpconfig = configfactory("conf.ini", TMP_CONFIG_SASL_EXTERNAL)
    mockbot = botfactory.preloaded(tmpconfig, preloads=["coretasks"])
    mockbot.backend.connected = True

    # connect and capability negotiation
    mockbot.on_connect()
    mockbot.on_message(":irc.example.com CAP * LS :sasl=PLAIN,EXTERNAL")
    n = len(mockbot.backend.message_sent)

    mockbot.on_message(":irc.example.com CAP * ACK :sasl")
    assert mockbot.backend.message_sent[n:] == rawlist(
        "AUTHENTICATE EXTERNAL",
    ), "The bot should initiate SASL EXTERNAL authentication without a password set."
    n += 1

    mockbot.on_message("AUTHENTICATE +")
    assert mockbot.backend.message_sent[n:] == rawlist(
        "AUTHENTICATE +",
    ), "SASL EXTERNAL authentication should continue without a password set."
    n += 1

    mockbot.on_message(":irc.example.com 904 SopelTest :SASL authentication failed")
    assert mockbot.backend.message_sent[n:] == rawlist(
        "CAP END",
        "QUIT :SASL Auth Failed",
    ), "SASL EXTERNAL failure should trigger CAP END and QUIT."


def test_sasl_plain_bad_password(botfactory: BotFactory, tmpconfig) -> None:
    mockbot = botfactory.preloaded(tmpconfig, preloads=['coretasks'])
    mockbot.backend.connected = True

    # connect and capability negotiation
    mockbot.on_connect()
    mockbot.on_message(':irc.example.com CAP * LS :sasl=PLAIN,EXTERNAL')
    mockbot.on_message(':irc.example.com CAP * ACK :sasl')
    mockbot.on_message(':irc.example.com AUTHENTICATE +')
    n = len(mockbot.backend.message_sent)

    # upon receiving the password, let's say it's invalid
    mockbot.on_message(
        ':irc.example.com 904 TestBot :SASL authentication failed')
    assert mockbot.backend.message_sent[n:] == rawlist(
        'CAP END',
        'QUIT :SASL Auth Failed'
    ), 'Upon failure, corestaks must end capability negotiation.'


def test_sasl_plain_not_supported(botfactory: BotFactory, tmpconfig) -> None:
    mockbot = botfactory.preloaded(tmpconfig, preloads=['coretasks'])
    mockbot.backend.connected = True

    # connect
    mockbot.on_connect()

    # capability negotiation
    mockbot.on_message(':irc.example.com CAP * LS :sasl=EXTERNAL')
    n = len(mockbot.backend.message_sent)

    # ACK sasl
    mockbot.on_message(':irc.example.com CAP * ACK :sasl')

    assert mockbot.backend.message_sent[n:] == rawlist(
        'CAP END',
        'QUIT :Configuration error.',
    ), 'SASL mech is not available so we must stop here.'


def test_sasl_plain_nonempty_server_message(
    botfactory: BotFactory,
    tmpconfig,
) -> None:
    mockbot = botfactory.preloaded(tmpconfig, preloads=['coretasks'])
    mockbot.backend.connected = True

    # connect and capability negotiation
    mockbot.on_connect()
    mockbot.on_message(':irc.example.com CAP * LS :sasl=PLAIN,EXTERNAL')
    n = len(mockbot.backend.message_sent)
    mockbot.on_message(':irc.example.com CAP * ACK :sasl')

    # sanity check
    assert mockbot.backend.message_sent[n:] == rawlist(
        'AUTHENTICATE PLAIN',
    )

    # server acknowledges PLAIN auth request in an unexpected way
    n = len(mockbot.backend.message_sent)
    mockbot.on_message(':irc.example.com AUTHENTICATE VGVzdEJvdABUZXN0Qm90AG')
    assert mockbot.backend.message_sent[n:] == rawlist(
        'AUTHENTICATE *',
    ), ('Bot must abort SASL PLAIN auth if server reply to starting '
        'AUTHENTICATE PLAIN is not as expected per SASL spec')

    # per spec, server should send ERR_SASLABORTED
    n = len(mockbot.backend.message_sent)
    mockbot.on_message(
        ':irc.example.com 906 TestBot :SASL authentication aborted')
    assert mockbot.backend.message_sent[n:] == rawlist(
        'CAP END',
        'QUIT :SASL Auth Failed',
    ), ('Sopel must finish capability negotiation after SASL even if aborted, '
        'and then QUIT because auth failed')


def test_sasl_nak(botfactory: BotFactory, tmpconfig) -> None:
    mockbot = botfactory.preloaded(tmpconfig, preloads=['coretasks'])
    mockbot.backend.connected = True

    # connect and capability negotiation
    mockbot.on_connect()
    mockbot.on_message(':irc.example.com CAP * LS :sasl=PLAIN,EXTERNAL')
    n = len(mockbot.backend.message_sent)
    mockbot.on_message(':irc.example.com CAP * NAK :sasl')

    assert mockbot.backend.message_sent[n:] == rawlist(
        'CAP END',
        'QUIT :Error negotiating capabilities.',
    )
