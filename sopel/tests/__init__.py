"""Test tools, factories, pytest fixtures, and mocks.

.. versionadded:: 7.0
"""
from __future__ import annotations

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from sopel.bot import Sopel


def rawlist(*args: str) -> list[bytes]:
    """Build a list of raw IRC messages from the lines given as ``*args``.

    :return: a list of raw IRC messages as seen by the bot
    :rtype: list

    This is a helper function to build a list of messages without having to
    care about encoding or this pesky carriage return::

        >>> rawlist('PRIVMSG :Hello!')
        [b'PRIVMSG :Hello!\\r\\n']
    """
    return ['{0}\r\n'.format(arg).encode('utf-8') for arg in args]


def on_message(bot: Sopel, message: str) -> None:
    """Send the message and wait for all running threads to end.

    When triggering plugin callables with
    :meth:`bot.on_message <sopel.irc.AbstractBot.on_message>` Sopel may execute
    them in their own threads. This is the normal and expected behavior, but it
    isn't practical for testing purposes.

    This helper function can be used to replace this::

        bot.on_message(message)

    By this::

        from sopel.tests import on_message

        on_message(bot, message)

    It will automatically join all threads resulting from calling
    ``bot.on_message``, including potential echo messages.

    .. versionadded:: 8.1
    """
    bot.on_message(message)

    while threads := bot.running_triggers:
        for t in threads:
            t.join()
