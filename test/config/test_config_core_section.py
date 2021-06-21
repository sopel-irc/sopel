# coding=utf-8
from __future__ import absolute_import, division, print_function, unicode_literals

import pytest

from sopel import config


FAKE_OWNER_CONFIG = """
[core]
owner=dgw
"""

FAKE_OWNER_ACCOUNT_CONFIG = """
[core]
owner_account=dgw
"""

FAKE_NO_OWNER_CONFIG = """
[core]
"""

FAKE_EMPTY_OWNER_CONFIG = """
[core]
owner=
"""

FAKE_EMPTY_OWNER_ACCOUNT_CONFIG = """
[core]
owner_account=
"""


@pytest.fixture
def tmphomedir(tmpdir):
    sopel_homedir = tmpdir.join('.sopel')
    sopel_homedir.mkdir()
    sopel_homedir.join('test.tmp').write('')
    sopel_homedir.join('test.d').mkdir()
    return sopel_homedir


def get_fake_config(contents, tmphomedir):
    conf_file = tmphomedir.join('conf.cfg')
    conf_file.write(contents)

    test_settings = config.Config(conf_file.strpath)
    return test_settings


@pytest.mark.parametrize('contents', [
    FAKE_OWNER_CONFIG,
    FAKE_OWNER_ACCOUNT_CONFIG,
])
def test_core_section_owner_present(contents, tmphomedir):
    get_fake_config(contents, tmphomedir)


@pytest.mark.parametrize('contents', [
    FAKE_NO_OWNER_CONFIG,
    FAKE_EMPTY_OWNER_CONFIG,
    FAKE_EMPTY_OWNER_ACCOUNT_CONFIG,
])
def test_core_section_owner_missing(contents, tmphomedir):
    with pytest.raises(ValueError):
        get_fake_config(contents, tmphomedir)
