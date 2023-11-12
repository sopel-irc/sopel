"""Test behavior of SASL by ``sopel.coretasks``"""
from __future__ import annotations

from base64 import b64decode, b64encode
from logging import ERROR
from typing import TYPE_CHECKING

import pytest
from scramp import ScramMechanism

from sopel import coretasks
from sopel.tests import rawlist

if TYPE_CHECKING:
    from sopel.bot import Sopel
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


@pytest.fixture
def tmpconfig(configfactory: ConfigFactory) -> Config:
    return configfactory('conf.ini', TMP_CONFIG_SASL_DEFAULT)


@pytest.fixture
def mockbot(tmpconfig, botfactory):
    return botfactory.preloaded(tmpconfig)


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


def test_sasl_bad_method(mockbot: Sopel, caplog: pytest.LogCaptureFixture):
    """Verify the bot behaves when configured with an unsupported SASL method."""
    mockbot.settings.core.auth_method = "sasl"
    mockbot.settings.core.auth_target = "SCRAM-MD4"
    mockbot.on_message("CAP * LS :sasl")
    mockbot.on_message("CAP TestBot ACK :sasl")
    assert mockbot.backend.message_sent == rawlist(
        "CAP REQ :sasl",
        "CAP END",
    )
    with caplog.at_level(ERROR):
        mockbot.on_message("AUTHENTICATE +")
    assert '"SCRAM-MD4" is not supported' in caplog.text


def test_sasl_plain_auth(mockbot: Sopel):
    """Verify the bot performs SASL PLAIN auth correctly."""
    mockbot.settings.core.auth_method = "sasl"
    mockbot.settings.core.auth_target = "PLAIN"
    mockbot.on_message("CAP * LS :sasl")
    mockbot.on_message("CAP TestBot ACK :sasl")
    assert mockbot.backend.message_sent == rawlist(
        "CAP REQ :sasl",
        "AUTHENTICATE PLAIN",
    )
    mockbot.on_message("AUTHENTICATE +")
    assert (
        len(mockbot.backend.message_sent) == 3
        and mockbot.backend.message_sent[-1]
        == rawlist("AUTHENTICATE VGVzdEJvdABUZXN0Qm90AHNlY3JldA==")[0]
    )
    mockbot.on_message(
        "900 TestBot test!test@test TestBot :You are now logged in as TestBot"
    )
    mockbot.on_message("903 TestBot :SASL authentication succeeded")
    assert (
        len(mockbot.backend.message_sent) == 4
        and mockbot.backend.message_sent[-1] == rawlist("CAP END")[0]
    )


def test_sasl_scram_sha_256_auth(mockbot: Sopel):
    """Verify the bot performs SASL SCRAM-SHA-256 auth correctly."""
    mech = ScramMechanism()
    salt, stored_key, server_key, iter_count = mech.make_auth_info(
        "secret", iteration_count=5000
    )
    scram_server = mech.make_server(
        lambda x: (salt, stored_key, server_key, iter_count)
    )

    mockbot.settings.core.auth_method = "sasl"
    mockbot.settings.core.auth_target = "SCRAM-SHA-256"
    mockbot.on_message("CAP * LS :sasl")
    mockbot.on_message("CAP TestBot ACK :sasl")
    assert mockbot.backend.message_sent == rawlist(
        "CAP REQ :sasl",
        "AUTHENTICATE SCRAM-SHA-256",
    )
    mockbot.on_message("AUTHENTICATE +")

    scram_server.set_client_first(
        b64decode(mockbot.backend.message_sent[-1].split(b" ")[-1]).decode("utf-8")
    )
    mockbot.on_message(
        "AUTHENTICATE "
        + b64encode(scram_server.get_server_first().encode("utf-8")).decode("utf-8")
    )
    scram_server.set_client_final(
        b64decode(mockbot.backend.message_sent[-1].split(b" ")[-1]).decode("utf-8")
    )
    mockbot.on_message(
        "AUTHENTICATE "
        + b64encode(scram_server.get_server_final().encode("utf-8")).decode("utf-8")
    )
    assert (
        len(mockbot.backend.message_sent) == 5
        and mockbot.backend.message_sent[-1] == rawlist("AUTHENTICATE +")[0]
    )

    mockbot.on_message(
        "900 TestBot test!test@test TestBot :You are now logged in as TestBot"
    )
    mockbot.on_message("903 TestBot :SASL authentication succeeded")
    assert (
        len(mockbot.backend.message_sent) == 6
        and mockbot.backend.message_sent[-1] == rawlist("CAP END")[0]
    )


def test_sasl_scram_sha_256_nonsense_server_first(mockbot: Sopel):
    """Verify the bot handles a nonsense SCRAM-SHA-256 server_first correctly."""
    mech = ScramMechanism()
    salt, stored_key, server_key, iter_count = mech.make_auth_info(
        "secret", iteration_count=5000
    )
    scram_server = mech.make_server(
        lambda x: (salt, stored_key, server_key, iter_count)
    )

    mockbot.settings.core.auth_method = "sasl"
    mockbot.settings.core.auth_target = "SCRAM-SHA-256"
    mockbot.on_message("CAP * LS :sasl")
    mockbot.on_message("CAP TestBot ACK :sasl")
    mockbot.on_message("AUTHENTICATE +")

    scram_server.set_client_first(
        b64decode(mockbot.backend.message_sent[-1].split(b" ")[-1]).decode("utf-8")
    )
    mockbot.on_message("AUTHENTICATE " + b64encode(b"junk").decode("utf-8"))
    assert (
        len(mockbot.backend.message_sent) == 4
        and mockbot.backend.message_sent[-1] == rawlist("AUTHENTICATE *")[0]
    )


def test_sasl_scram_sha_256_nonsense_server_final(mockbot: Sopel):
    """Verify the bot handles a nonsense SCRAM-SHA-256 server_final correctly."""
    mech = ScramMechanism()
    salt, stored_key, server_key, iter_count = mech.make_auth_info(
        "secret", iteration_count=5000
    )
    scram_server = mech.make_server(
        lambda x: (salt, stored_key, server_key, iter_count)
    )

    mockbot.settings.core.auth_method = "sasl"
    mockbot.settings.core.auth_target = "SCRAM-SHA-256"
    mockbot.on_message("CAP * LS :sasl")
    mockbot.on_message("CAP TestBot ACK :sasl")
    mockbot.on_message("AUTHENTICATE +")

    scram_server.set_client_first(
        b64decode(mockbot.backend.message_sent[-1].split(b" ")[-1]).decode("utf-8")
    )
    mockbot.on_message(
        "AUTHENTICATE "
        + b64encode(scram_server.get_server_first().encode("utf-8")).decode("utf-8")
    )
    scram_server.set_client_final(
        b64decode(mockbot.backend.message_sent[-1].split(b" ")[-1]).decode("utf-8")
    )
    mockbot.on_message("AUTHENTICATE " + b64encode(b"junk").decode("utf-8"))
    assert (
        len(mockbot.backend.message_sent) == 5
        and mockbot.backend.message_sent[-1] == rawlist("AUTHENTICATE *")[0]
    )


def test_sasl_scram_sha_256_error_server_first(mockbot: Sopel):
    """Verify the bot handles an error SCRAM-SHA-256 server_first correctly."""

    mockbot.settings.core.auth_method = "sasl"
    mockbot.settings.core.auth_target = "SCRAM-SHA-256"
    mockbot.on_message("CAP * LS :sasl")
    mockbot.on_message("CAP TestBot ACK :sasl")
    mockbot.on_message("AUTHENTICATE +")

    mockbot.on_message("AUTHENTICATE " + b64encode(b"e=some-error").decode("utf-8"))
    assert (
        len(mockbot.backend.message_sent) == 4
        and mockbot.backend.message_sent[-1] == rawlist("AUTHENTICATE *")[0]
    )


def test_sasl_scram_sha_256_error_server_final(mockbot: Sopel):
    """Verify the bot handles an error SCRAM-SHA-256 server_final correctly."""
    mech = ScramMechanism()
    salt, stored_key, server_key, iter_count = mech.make_auth_info(
        "secret", iteration_count=5000
    )
    scram_server = mech.make_server(
        lambda x: (salt, stored_key, server_key, iter_count)
    )

    mockbot.settings.core.auth_method = "sasl"
    mockbot.settings.core.auth_target = "SCRAM-SHA-256"
    mockbot.on_message("CAP * LS :sasl")
    mockbot.on_message("CAP TestBot ACK :sasl")
    mockbot.on_message("AUTHENTICATE +")

    scram_server.set_client_first(
        b64decode(mockbot.backend.message_sent[-1].split(b" ")[-1]).decode("utf-8")
    )
    mockbot.on_message(
        "AUTHENTICATE "
        + b64encode(scram_server.get_server_first().encode("utf-8")).decode("utf-8")
    )
    scram_server.set_client_final(
        b64decode(mockbot.backend.message_sent[-1].split(b" ")[-1]).decode("utf-8")
    )
    mockbot.on_message("AUTHENTICATE " + b64encode(b"e=some-error").decode("utf-8"))
    assert (
        len(mockbot.backend.message_sent) == 5
        and mockbot.backend.message_sent[-1] == rawlist("AUTHENTICATE *")[0]
    )
