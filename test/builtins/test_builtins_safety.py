"""Tests for Sopel's ``safety`` plugin"""

from __future__ import annotations

import pytest

from sopel.builtins.safety import safeify_url


URL_TESTS = (
    # Valid URLs
    ("http://example.com", ("hxxp://example[.]com")),
    ("http://1.2.3.4/mgr.cgi", ("hxxp://1[.]2[.]3[.]4/mgr.cgi")),
    ("http://[fd00:1234::4321]/", ("hxxp://[fd00[:]1234[:][:]4321]/")),
    ("ftp://1.2.3.4/", ("fxp://1[.]2[.]3[.]4/")),
    # Invalid, but parsed anyway
    ("http://<placeholder>/", ("hxxp://<placeholder>/")),
    ("http://1.2.3.4.5/", ("hxxp://1[.]2[.]3[.]4[.]5/")),
    ("http://555.555.555.555/", ("hxxp://555[.]555[.]555[.]555/")),
    # urllib.urlparse() works on these in python <=3.10 but fails in 3.11
    ("http://[fd00:::]/", ("hxxp://[fd00[:][:][:]]/", "http[:]//[fd00[:][:][:]]/")),
    ("http://[placeholder]/", ("hxxp://[placeholder]/", "http[:]//[placeholder]/")),
)


@pytest.mark.parametrize("original, safed_options", URL_TESTS)
def test_safeify_url(original, safed_options):
    assert safeify_url(original) in safed_options
