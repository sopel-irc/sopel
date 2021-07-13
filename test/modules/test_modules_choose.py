"""Tests for Sopel's ``choose`` plugin"""
from __future__ import generator_stop

import pytest

from sopel import formatting
from sopel.modules import choose


UNICODE_ZS_CATEGORY = [
    '\u0020',  # SPACE
    '\u00A0',  # NO-BREAK SPACE
    '\u1680',  # OGHAM SPACE MARK
    '\u2000',  # EN QUAD
    '\u2001',  # EM QUAD
    '\u2002',  # EN SPACE
    '\u2003',  # EM SPACE
    '\u2004',  # THREE-PER-EM SPACE
    '\u2005',  # FOUR-PER-EM SPACE
    '\u2006',  # SIX-PER-EM SPACE
    '\u2007',  # FIGURE SPACE
    '\u2008',  # PUNCTUATION SPACE
    '\u2009',  # THIN SPACE
    '\u200A',  # HAIR SPACE
    '\u202F',  # NARROW NO-BREAK SPACE
    '\u205F',  # MEDIUM MATHEMATICAL SPACE
    '\u3000',  # IDEOGRAPHIC SPACE
]

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


def test_format_safe_basic():
    """Test handling of basic whitespace."""
    assert choose._format_safe(
        ''.join(UNICODE_ZS_CATEGORY)) == ''


def test_format_safe_control():
    """Test handling of non-printing control characters."""
    all_formatting = ''.join(formatting.CONTROL_FORMATTING)

    # no formatting chars should be stripped,
    # but a reset should be added to the end
    assert choose._format_safe(all_formatting) == all_formatting + '\x0f'

    # control characters not recognized as formatting should be stripped
    assert choose._format_safe(
        ''.join(
            c
            for c in formatting.CONTROL_NON_PRINTING
            if c not in formatting.CONTROL_FORMATTING
        )) == ''


def test_format_safe_invalid_arg():
    """Test for correct exception if non-string is passed."""
    with pytest.raises(TypeError):
        choose._format_safe(None)


@pytest.mark.parametrize('text, cleaned', SAFE_PAIRS)
def test_format_safe_pairs(text, cleaned):
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
