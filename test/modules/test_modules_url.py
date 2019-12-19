# coding=utf-8
"""Tests for Sopel's ``url`` plugin"""
from __future__ import unicode_literals, absolute_import, print_function, division

import pytest

from sopel.modules import url


INVALID_URLS = (
    "http://.example.com/",  # empty label
    "http://example..com/",  # empty label
    "http://?",  # no host
)


@pytest.mark.parametrize("site", INVALID_URLS)
def test_find_title_invalid(site):
    # All local for invalid ones
    assert url.find_title(site) is None
