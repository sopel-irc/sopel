# coding=utf-8
"""The formatting module includes functions to apply IRC formatting to text.

*Availability: 4.5+*
"""
# Copyright 2014, Elsie Powell, embolalia.com
# Copyright 2019, dgw, technobabbl.es
# Licensed under the Eiffel Forum License 2.
from __future__ import unicode_literals, absolute_import, print_function, division

import string
import sys


__all__ = [
    # control chars
    'CONTROL_NORMAL',
    'CONTROL_COLOR',
    'CONTROL_HEX_COLOR',
    'CONTROL_BOLD',
    'CONTROL_ITALIC',
    'CONTROL_UNDERLINE',
    'CONTROL_STRIKETHROUGH',
    'CONTROL_MONOSPACE',
    'CONTROL_REVERSE',
    # utility functions
    'color',
    'hex_color',
    'bold',
    'italic',
    'underline',
    'strikethrough',
    'monospace',
    'reverse',
    # utility class
    'colors',
]

if sys.version_info.major >= 3:
    unicode = str

# Color names are as specified at http://www.mirc.com/colors.html

CONTROL_NORMAL = '\x0f'
"""The control code to reset formatting."""
CONTROL_COLOR = '\x03'
"""The control code to start or end color formatting."""
CONTROL_HEX_COLOR = '\x04'
"""The control code to start or end hexadecimal color formatting."""
CONTROL_BOLD = '\x02'
"""The control code to start or end bold formatting."""
CONTROL_ITALIC = '\x1d'
"""The control code to start or end italic formatting."""
CONTROL_UNDERLINE = '\x1f'
"""The control code to start or end underlining."""
CONTROL_STRIKETHROUGH = '\x1e'
"""The control code to start or end strikethrough formatting."""
CONTROL_MONOSPACE = '\x11'
"""The control code to start or end monospace formatting."""
CONTROL_REVERSE = '\x16'
"""The control code to start or end reverse-color formatting."""


# TODO when we can move to 3.3+ completely, make this an Enum.
class colors:
    WHITE = '00'
    BLACK = '01'
    BLUE = '02'
    NAVY = BLUE
    GREEN = '03'
    RED = '04'
    BROWN = '05'
    MAROON = BROWN
    PURPLE = '06'
    ORANGE = '07'
    OLIVE = ORANGE
    YELLOW = '08'
    LIGHT_GREEN = '09'
    LIME = LIGHT_GREEN
    TEAL = '10'
    LIGHT_CYAN = '11'
    CYAN = LIGHT_CYAN
    LIGHT_BLUE = '12'
    ROYAL = LIGHT_BLUE
    PINK = '13'
    LIGHT_PURPLE = PINK
    FUCHSIA = PINK
    GREY = '14'
    LIGHT_GREY = '15'
    SILVER = LIGHT_GREY

    # Create aliases.
    GRAY = GREY
    LIGHT_GRAY = LIGHT_GREY


def _get_color(color):
    if color is None:
        return None

    # You can pass an int or string of the code
    try:
        color = int(color)
    except ValueError:
        pass
    if isinstance(color, int):
        if color > 99:
            raise ValueError('Can not specify a color above 99.')
        return unicode(color).rjust(2, '0')

    # You can also pass the name of the color
    color_name = color.upper()
    color_dict = colors.__dict__
    try:
        return color_dict[color_name]
    except KeyError:
        raise ValueError('Unknown color name {}'.format(color))


def color(text, fg=None, bg=None):
    """Return the text, with the given colors applied in IRC formatting.

    :param str text: the text to format
    :param mixed fg: the foreground color
    :param mixed bg: the background color

    The color can be a string of the color name, or an integer in the range
    0-99. The known color names can be found in the :class:`colors` class of
    this module.
    """
    if not fg and not bg:
        return text

    fg = _get_color(fg)
    bg = _get_color(bg)

    if not bg:
        text = ''.join([CONTROL_COLOR, fg, text, CONTROL_COLOR])
    else:
        text = ''.join([CONTROL_COLOR, fg, ',', bg, text, CONTROL_COLOR])
    return text


def _get_hex_color(color):
    if color is None:
        return None

    try:
        color = color.upper()
        if not all(c in string.hexdigits for c in color):
            raise AttributeError
    except AttributeError:
        raise ValueError('Hexadecimal color value must be passed as string.')

    if len(color) == 3:
        return ''.join([c * 2 for c in color])
    elif len(color) == 6:
        return color
    else:  # invalid length
        raise ValueError('Hexadecimal color value must have either 3 or 6 digits.')


def hex_color(text, fg=None, bg=None):
    """Return the text, with the given colors applied in IRC formatting.

    :param str text: the text to format
    :param str fg: the foreground color
    :param str bg: the background color

    The color can be provided with a string of either 3 or 6 hexadecimal digits.
    As in CSS, 3-digit colors will be interpreted as if they were 6-digit colors
    with each digit repeated (e.g. color ``c90`` is identical to ``cc9900``). Do
    not include the leading ``#`` symbol.

    .. note::
        This is a relatively new IRC formatting convention. Use only when you
        can afford to have its meaning lost, as not many clients support it yet.
    """
    if not fg and not bg:
        return text

    fg = _get_hex_color(fg)
    bg = _get_hex_color(bg)

    if not bg:
        text = ''.join([CONTROL_HEX_COLOR, fg, text, CONTROL_HEX_COLOR])
    else:
        text = ''.join([CONTROL_HEX_COLOR, fg, ',', bg, text, CONTROL_HEX_COLOR])
    return text


def bold(text):
    """Return the text, with bold IRC formatting.

    :param str text: the text to format
    """
    return ''.join([CONTROL_BOLD, text, CONTROL_BOLD])


def italic(text):
    """Return the text, with italic IRC formatting.

    :param str text: the text to format
    """
    return ''.join([CONTROL_ITALIC, text, CONTROL_ITALIC])


def underline(text):
    """Return the text, with underline IRC formatting.

    :param str text: the text to format
    """
    return ''.join([CONTROL_UNDERLINE, text, CONTROL_UNDERLINE])


def strikethrough(text):
    """Return the text, with strikethrough IRC formatting.

    :param str text: the text to format

    .. note::
        This is a relatively new IRC formatting convention. Use only when you
        can afford to have its meaning lost, as not many clients support it yet.
    """
    return ''.join([CONTROL_STRIKETHROUGH, text, CONTROL_STRIKETHROUGH])


def monospace(text):
    """Return the text, with monospace IRC formatting.

    :param str text: the text to format

    .. note::
        This is a relatively new IRC formatting convention. Use only when you
        can afford to have its meaning lost, as not many clients support it yet.
    """
    return ''.join([CONTROL_MONOSPACE, text, CONTROL_MONOSPACE])


def reverse(text):
    """Return the text, with reverse-color IRC formatting.

    :param str text: the text to format

    .. note::
        This code isn't super well supported, and its behavior even in clients
        that understand it (e.g. mIRC) can be unpredictable. Use it carefully.
    """
    return ''.join([CONTROL_REVERSE, text, CONTROL_REVERSE])
