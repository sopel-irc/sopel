# coding=utf-8
"""Tests for Sopel's ``choose`` plugin"""
from __future__ import absolute_import, division, print_function, unicode_literals

import pytest

from sopel.modules import choose


SAFE_PAIRS = (
    # regression checks vs. old string.strip()
    ('',
     ''),
    ('a',  # one iteration of this code returned '' for one-char strings
     'a'),
    ('aa',
     'aa'),
    ('\x02',  # special case of 'a', one-char string that needs reset
     '\x02\x0f'),
    # basic whitespace (dropped)
    ('  leading space',
     'leading space'),
    ('trailing space ',
     'trailing space'),
    (' leading AND trailing space  ',
     'leading AND trailing space'),
    # advanced whitespace (dropped)
    ('\tleading tab',
     'leading tab'),
    ('trailing tab\t',
     'trailing tab'),
    # whitespace inside formatting (kept)
    ('\x02  leading space inside formatting\x02',
     '\x02  leading space inside formatting\x02\x0f'),
    ('\x02trailing space inside formatting  \x02',
     '\x02trailing space inside formatting  \x02\x0f'),
    ('\x02  leading AND trailing inside formatting  \x02',
     '\x02  leading AND trailing inside formatting  \x02\x0f'),
    # whitespace outside formatting (dropped)
    ('  \x02leading space outside formatting\x02',
     '\x02leading space outside formatting\x02\x0f'),
    ('\x02trailing space outside formatting\x02  ',
     '\x02trailing space outside formatting\x02\x0f'),
    # whitespace both inside and outside formatting
    # (respectively kept and dropped)
    ('  \x02  leading space inside AND outside\x02',
     '\x02  leading space inside AND outside\x02\x0f'),
    ('\x02trailing space inside AND outside  \x02  ',
     '\x02trailing space inside AND outside  \x02\x0f'),
    ('  \x02  leading AND trailing inside AND outside  \x02  ',
     '\x02  leading AND trailing inside AND outside  \x02\x0f'),
    # unmatched formatting
    ('\x02unterminated bold',
     '\x02unterminated bold\x0f'),
    ('only last word \x02bold',
     'only last word \x02bold\x0f'),
    (' leading space, \x03italic\x03, and \x02bold with extra spaces  ',
     'leading space, \x03italic\x03, and \x02bold with extra spaces\x0f'),
)


@pytest.mark.parametrize('text, cleaned', SAFE_PAIRS)
def test_format_safe(text, cleaned):
    """Test expected formatting-safe string sanitization."""
    assert choose._format_safe(text) == cleaned


# --- Insert reset only when necessary | Expected to fail --- #

EFFICIENT_PAIRS = (
    # whitespace inside formatting (kept)
    ('\x02  leading space inside formatting\x02',
     '\x02  leading space inside formatting\x02'),
    ('\x02trailing space inside formatting  \x02',
     '\x02trailing space inside formatting  \x02'),
    ('\x02  leading AND trailing inside formatting  \x02',
     '\x02  leading AND trailing inside formatting  \x02'),
    # whitespace outside formatting (dropped)
    ('  \x02leading space outside formatting\x02',
     '\x02leading space outside formatting\x02'),
    ('\x02trailing space outside formatting\x02  ',
     '\x02trailing space outside formatting\x02'),
    # whitespace both inside and outside formatting
    # (respectively kept and dropped)
    ('  \x02  leading space inside AND outside\x02',
     '\x02  leading space inside AND outside\x02'),
    ('\x02trailing space inside AND outside  \x02  ',
     '\x02trailing space inside AND outside  \x02'),
    ('  \x02  leading AND trailing inside AND outside  \x02  ',
     '\x02  leading AND trailing inside AND outside  \x02'),
)


@pytest.mark.parametrize('text, cleaned', EFFICIENT_PAIRS)
@pytest.mark.xfail(strict=True)
def test_format_safe_future(text, cleaned):
    """Test future aspirations of efficiency."""
    assert choose._format_safe(text) == cleaned
