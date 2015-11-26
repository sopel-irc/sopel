# coding=utf-8
"""*Availability: 4.5+*

The formatting module includes functions to apply IRC formatting to text."""
# Copyright 2014, Edward D. Powell, embolalia.net
# Licensed under the Eiffel Forum License 2.
from __future__ import unicode_literals, absolute_import, print_function, division
import sys
if sys.version_info.major >= 3:
    unicode = str

# Color names are as specified at http://www.mirc.com/colors.html

CONTROL_NORMAL = '\x0f'
"""The control code to reset formatting"""
CONTROL_COLOR = '\x03'
"""The control code to start or end color formatting"""
CONTROL_UNDERLINE = '\x1f'
"""The control code to start or end underlining"""
CONTROL_BOLD = '\x02'
"""The control code to start or end bold formatting"""


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

    #Create aliases.
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

    The color can be a string of the color name, or an integer between 0 and
    99. The known color names can be found in the `colors` class of this
    module."""
    if not fg and not bg:
        return text

    fg = _get_color(fg)
    bg = _get_color(bg)

    if not bg:
        text = ''.join([CONTROL_COLOR, fg, text, CONTROL_COLOR])
    else:
        text = ''.join([CONTROL_COLOR, fg, ',', bg, text, CONTROL_COLOR])
    return text


def bold(text):
    """Return the text, with bold IRC formatting."""
    return ''.join([CONTROL_BOLD, text, CONTROL_BOLD])


def underline(text):
    """Return the text, with underline IRC formatting."""
    return ''.join([CONTROL_UNDERLINE, text, CONTROL_UNDERLINE])
