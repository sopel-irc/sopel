# coding=utf-8
"""Test tools, factories, pytest fixtures, and mocks.

.. versionadded:: 7.0
"""
from __future__ import unicode_literals, absolute_import, print_function, division


def rawlist(*args):
    """Build a list of raw IRC messages from the lines given as ``*args``.

    :return: a list of raw IRC messages as seen by the bot
    :rtype: list

    This is a helper function to build a list of messages without having to
    care about encoding or this pesky carriage return::

        >>> rawlist('PRIVMSG :Hello!')
        [b'PRIVMSG :Hello!\\r\\n']
    """
    return ['{0}\r\n'.format(arg).encode('utf-8') for arg in args]
