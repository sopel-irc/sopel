"""
find.py - Sopel Spelling Correction Plugin
This plugin will fix spelling errors if someone corrects them
using the sed notation (s///) commonly found in vi/vim.

Copyright 2011, Michael Yanovich, yanovich.net
Copyright 2013, Elsie Powell, embolalia.com
Copyright 2020, dgw, technobabbl.es
Includes contributions from: Matt Meinwald, and Morgan Goose
Licensed under the Eiffel Forum License 2.

https://sopel.chat
"""
from __future__ import annotations

from collections import deque
import re
from typing import TYPE_CHECKING

from sopel import plugin
from sopel.config import types
from sopel.formatting import bold, plain


if TYPE_CHECKING:
    from collections.abc import Iterable


ELLIPSIS = '…'
"""Marker shown where a snippet had content trimmed off."""


class FindSection(types.StaticSection):
    context_words = types.ValidatedAttribute(
        'context_words', parse=int, default=-1)
    """How many words to keep on each side of a correction.

    A negative value reposts the whole corrected line, which is what Sopel
    did before this option existed. ``0`` shows only the corrected word.

    If trimming would leave nothing a reader can see, the whole line is shown
    instead.
    """


def configure(config):
    """
    | name | example | purpose |
    | ---- | ------- | ------- |
    | context_words | 2 | Words kept around a correction; negative reposts the line |
    """
    config.define_section('find', FindSection)
    config.find.configure_setting(
        'context_words',
        'How many words should Sopel keep around a correction? '
        '(any negative value reposts the whole corrected line)')


def _word_window(
    text: str,
    start: int,
    end: int,
    context_words: int,
) -> tuple[int, int]:
    """Find the slice of ``text`` to show around the ``start:end`` replacement.

    :param str text: the corrected line
    :param int start: where the replacement starts in ``text``
    :param int end: where the replacement ends in ``text``
    :param int context_words: how many words to keep on each side
    :return: a ``(left, right)`` pair of offsets into ``text``

    The word the replacement landed in is kept whole, so a correction inside a
    word does not come back as a fragment. Deleting text leaves nothing to keep
    whole, so a deletion between two words takes ``context_words`` words on each
    side, while one inside a word still shows the word it changed.
    """
    left = start
    right = end

    inside_word = (
        0 < start and end < len(text)
        and not text[start - 1].isspace()
        and not text[end].isspace()
    )

    if end > start or inside_word:
        # keep the rest of the word the replacement landed in
        while left > 0 and not text[left - 1].isspace():
            left -= 1
        while right < len(text) and not text[right].isspace():
            right += 1

    for _ in range(context_words):
        stop = left
        while stop > 0 and text[stop - 1].isspace():
            stop -= 1
        while stop > 0 and not text[stop - 1].isspace():
            stop -= 1
        if stop == left:
            break
        left = stop

    for _ in range(context_words):
        stop = right
        while stop < len(text) and text[stop].isspace():
            stop += 1
        while stop < len(text) and not text[stop].isspace():
            stop += 1
        if stop == right:
            break
        right = stop

    # trim whitespace off the edges, but never into the replacement itself
    while left < start and text[left].isspace():
        left += 1
    while right > end and text[right - 1].isspace():
        right -= 1

    return left, right


def _build_snippet(
    text: str,
    spans: Iterable[tuple[int, int]],
    context_words: int,
) -> str:
    """Bold the replacements in ``text``, trimming to the context around them.

    :param str text: the corrected line
    :param spans: ``(start, end)`` offsets of each replacement in ``text``
    :param int context_words: words to keep on each side of a replacement
    :rtype: str

    Each replacement gets its own window. Windows with nothing but whitespace
    between them are shown as one, and an :data:`ELLIPSIS` marks every place a
    word was cut.
    """
    windows: list[list[int]] = []
    for start, end in spans:
        left, right = _word_window(text, start, end, context_words)
        if windows and not text[windows[-1][1]:left].strip():
            # nothing but whitespace was dropped, so keep it as one window
            windows[-1][1] = max(windows[-1][1], right)
        else:
            windows.append([left, right])

    parts = []
    for index, (left, right) in enumerate(windows):
        if index > 0 or text[:left].strip():
            parts.append(ELLIPSIS)
        cursor = left
        for start, end in spans:
            if start < left or end > right:
                continue
            parts.append(text[cursor:start])
            if end > start:
                parts.append(bold(text[start:end]))
            cursor = end
        parts.append(text[cursor:right])

    if text[windows[-1][1]:].strip():
        parts.append(ELLIPSIS)

    return ''.join(parts)


def _replacement_spans(
    regex: re.Pattern,
    line: str,
    subst: str,
    count: int,
) -> list[tuple[int, int]]:
    """Locate where each replacement lands in the corrected line.

    :param regex: compiled pattern being replaced
    :param str line: the line being corrected
    :param str subst: the replacement text
    :param int count: how many matches to replace; ``0`` replaces all of them
    :return: a list of ``(start, end)`` offsets into the corrected line

    :func:`re.sub` throws away the positions a snippet needs, so walk the
    matches and track the offsets as the corrected line is assembled.
    """
    spans: list[tuple[int, int]] = []
    length = 0
    position = 0

    for number, match in enumerate(regex.finditer(line), start=1):
        length += match.start() - position
        replacement = match.expand(subst)
        spans.append((length, length + len(replacement)))
        length += len(replacement)
        position = match.end()
        if count and number >= count:
            break

    return spans


def replace_highlight(
    regex: re.Pattern,
    line: str,
    subst: str,
    count: int = 1,
    context_words: int = -1,
) -> tuple[str, str | None]:
    """Apply a substitution to ``line`` and build the version to show.

    :param regex: compiled pattern to replace
    :param str line: the line being corrected
    :param str subst: the replacement text
    :param int count: how many matches to replace; ``0`` replaces all of them
    :param int context_words: words to keep on each side of a replacement, or a
                             negative value to repost the whole line
    :return: a ``(new_line, new_display)`` pair, where ``new_display`` is
             ``None`` if the substitution changed nothing
    """
    new_line = regex.sub(subst, line, count=count)
    if new_line == line:
        return new_line, None

    if context_words < 0:
        return new_line, regex.sub(bold(subst), line, count=count)

    spans = _replacement_spans(regex, line, subst, count)
    snippet = _build_snippet(new_line, spans, context_words)

    if not plain(snippet).replace(ELLIPSIS, '').strip():
        # the window has nothing a reader can see, so show the whole line
        return new_line, regex.sub(bold(subst), line, count=count)

    return new_line, snippet


def setup(bot):
    bot.settings.define_section('find', FindSection)
    if 'find_lines' not in bot.memory:
        bot.memory['find_lines'] = bot.make_identifier_memory()


def shutdown(bot):
    try:
        del bot.memory['find_lines']
    except KeyError:
        pass


@plugin.echo
@plugin.rule('.*')
@plugin.priority('low')
@plugin.require_chanmsg
@plugin.unblockable
def collectlines(bot, trigger):
    """Create a temporary log of what people say"""
    line = trigger.group()
    if line.startswith('s/') or line.startswith('s|'):
        # Don't remember substitutions
        return

    # Add a log for the channel and nick, if there isn't already one
    if trigger.sender not in bot.memory['find_lines']:
        bot.memory['find_lines'][trigger.sender] = bot.make_identifier_memory()
    if trigger.nick not in bot.memory['find_lines'][trigger.sender]:
        bot.memory['find_lines'][trigger.sender][trigger.nick] = deque(maxlen=10)

    # Update in-memory list of the user's lines in the channel
    line_list = bot.memory['find_lines'][trigger.sender][trigger.nick]

    # Messages are stored in reverse order (most recent first)
    if line.startswith('\x01ACTION'):
        line_list.appendleft(line[:-1])
    else:
        line_list.appendleft(line)


def _cleanup_channel(bot, channel):
    bot.memory['find_lines'].pop(channel, None)


def _cleanup_nickname(bot, nick, channel=None):
    if channel:
        bot.memory['find_lines'].get(channel, {}).pop(nick, None)
    else:
        for channel in bot.memory['find_lines'].keys():
            bot.memory['find_lines'][channel].pop(nick, None)


@plugin.echo
@plugin.event('PART')
@plugin.priority('low')
@plugin.unblockable
def part_cleanup(bot, trigger):
    """Clean up cached data when a user leaves a channel."""
    if trigger.nick == bot.nick:
        # Nuke the whole channel cache, boys, we're outta here!
        _cleanup_channel(bot, trigger.sender)
    else:
        # Someone else left; clean up after them
        _cleanup_nickname(bot, trigger.nick, trigger.sender)


@plugin.echo
@plugin.event('QUIT')
@plugin.priority('low')
@plugin.unblockable
def quit_cleanup(bot, trigger):
    """Clean up cached data after a user quits IRC."""
    # If Sopel itself quits, shutdown() will handle the cleanup.
    _cleanup_nickname(bot, trigger.nick)


@plugin.echo
@plugin.event('KICK')
@plugin.priority('low')
@plugin.unblockable
def kick_cleanup(bot, trigger):
    """Clean up cached data when a user is kicked from a channel."""
    nick = bot.make_identifier(trigger.args[1])
    if nick == bot.nick:
        # We got kicked! Nuke the whole channel.
        _cleanup_channel(bot, trigger.sender)
    else:
        # Clean up after the poor sod (or more likely, spammer) who got the boot
        _cleanup_nickname(bot, nick, trigger.sender)


# Match nick, s/find/replace/flags. Flags and nick are optional, nick can be
# followed by comma or colon, anything after the first space after the third
# slash is ignored, and you can use either a slash or a pipe.
# If you want to search for an actual slash AND a pipe in the same message,
# you can escape your separator, in old and/or new.
@plugin.rule(r"""(?:
             (?P<nick>\S+)     # Catch a nick in group 1
             [:,]\s+)?         # Followed by optional colon/comma and whitespace
             s(?P<sep>/)       # The literal s and a separator / as group 2
             (?P<old>          # Group 3 is the thing to find
               (?:\\\\|\\/|[^/])+   # One or more non-slashes or escaped slashes
             )
             /                 # The separator again
             (?P<new>          # Group 4 is what to replace with
               (?:\\\\|\\/|[^/])*   # One or more non-slashes or escaped slashes
             )
             (?:/              # Optional separator followed by group 5 (flags)
                (?P<flags>\S+)
             )?
            """)
@plugin.rule(r"""(?:
             (?P<nick>\S+)     # Catch a nick in group 1
             [:,]\s+)?         # Followed by optional colon/comma and whitespace
             s(?P<sep>\|)      # The literal s and a separator | as group 2
             (?P<old>          # Group 3 is the thing to find
               (?:\\\\|\\\||[^|])+  # One or more non-pipe or escaped pipe
             )
             \|                # The separator again
             (?P<new>          # Group 4 is what to replace with
               (?:\\\\|\\\||[^|])*  # One or more non-pipe or escaped pipe
             )
             (?:\|             # Optional separator followed by group 5 (flags)
                (?P<flags>\S+)
             )?
            """)
@plugin.priority('high')
@plugin.require_chanmsg
def findandreplace(bot, trigger):
    # Correcting other person vs self.
    correcting_self = True
    rnick = trigger.nick
    if trigger.group('nick'):
        correcting_self = False
        rnick = bot.make_identifier(trigger.group('nick'))

    history = bot.memory['find_lines'].get(trigger.sender, {}).get(rnick, None)
    if not history:
        # No conversation history to potentially correct; bail out.
        return

    sep = trigger.group('sep')
    escape_sequence_pattern = re.compile(r'\\[\\%s]' % sep)

    old = escape_sequence_pattern.sub(decode_escape, trigger.group('old'))
    new = trigger.group('new')
    flags = trigger.group('flags') or ''

    # only clean/format the new string if it's non-empty
    if new:
        new = escape_sequence_pattern.sub(decode_escape, new)

    # If g flag is given, replace all. Otherwise, replace once.
    count = 0 if 'g' in flags else 1

    # If i flag is given, ignore case when replacing.
    regex_flags = re.U
    if 'i' in flags:
        regex_flags |= re.I

    # Precompile the regex with its flags
    regex = re.compile(re.escape(old), regex_flags)

    context_words = bot.settings.find.context_words

    is_action = False  # /me command
    for line in history:
        # Look back through the user's lines in the channel for one where the
        # replacement works
        if line.startswith("\x01ACTION"):
            is_action = True
            line = line[8:]
        else:
            is_action = False
        new_line, new_display = replace_highlight(
            regex, line, new, count, context_words)
        if new_display is not None:
            # we are done
            break
    else:
        # No matching line; nothing to do
        return

    # Save the new "edited" message.
    action = '\x01ACTION ' if is_action else ''
    history.appendleft(action + new_line)  # history is in most-recent-first order

    # output
    if not is_action:
        new_display = 'meant to say: %s' % new_display
    if correcting_self:
        msg = '%s %s' % (trigger.nick, new_display)
    else:
        msg = '%s thinks %s %s' % (trigger.nick, rnick, new_display)

    bot.say(msg)


def decode_escape(match):
    print("Substituting %s" % match.group(0))
    return {
        r'\\': '\\',
        r'\|': '|',
        r'\/': '/',
    }[match.group(0)]
