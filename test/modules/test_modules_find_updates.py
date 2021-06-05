"""Tests for Sopel's ``find_updates`` plugin"""
from __future__ import generator_stop

import pytest
import requests.exceptions

from sopel.modules import find_updates


TMP_CONFIG = """
[core]
owner = Admin
nick = Sopel
enable =
    find_updates
host = chat.freenode.net
"""


@pytest.fixture
def mockbot(configfactory, botfactory):
    tmpconfig = configfactory('default.ini', TMP_CONFIG)
    return botfactory(tmpconfig)


def test_check_version_request_fails(mockbot, requests_mock):
    """Test normal stable update check."""
    requests_mock.get(
        find_updates.version_url,
        exc=requests.exceptions.RequestException,
    )

    # check as many times as are expected to be silent
    # we're checking *before* it fails, so the failure count here is lower
    # than when check_version() compares with <= afterward
    while mockbot.memory.get('update_failures', 0) < find_updates.max_failures:
        find_updates.check_version(mockbot)

        assert len(mockbot.backend.message_sent) == 0, (
            'check_version() should fail silently until max_failures is reached')

    # this is check number max_failures; *now* it should fail loudly
    find_updates.check_version(mockbot)

    assert len(mockbot.backend.message_sent) == 2, (
        'check_version() is expected to send two lines to IRC if it has been '
        'unable to fetch update info for max_failures tries')
