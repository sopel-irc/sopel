"""Tests for Sopel's ``find`` plugin"""
from __future__ import annotations

import re

import pytest

from sopel.builtins.find import ELLIPSIS, replace_highlight
from sopel.formatting import bold, plain
from sopel.tests import rawlist


TMP_CONFIG = """
[core]
owner = Admin
nick = Sopel
enable =
    find
host = irc.libera.chat
"""


@pytest.fixture
def bot(botfactory, configfactory):
    settings = configfactory('default.ini', TMP_CONFIG)
    return botfactory.preloaded(settings, ['find'])


@pytest.fixture
def irc(bot, ircfactory):
    return ircfactory(bot)


@pytest.fixture
def user(userfactory):
    return userfactory('User')


@pytest.fixture
def other_user(userfactory):
    return userfactory('other_user')


@pytest.fixture
def channel():
    return '#testing'


REPLACES_THAT_WORK = (
    ("A simple line.", r"s/line/message/", f"A simple {bold('message')}."),
    ("An escaped / line.", r"s/\//slash/", f"An escaped {bold('slash')} line."),
    ("A piped line.", r"s|line|replacement|", f"A piped {bold('replacement')}."),
    ("An escaped | line.", r"s|\||pipe|", f"An escaped {bold('pipe')} line."),
    ("An escaped \\ line.", r"s/\\/backslash/", f"An escaped {bold('backslash')} line."),
    ("abABab", r"s/b/c/g", "abABab".replace('b', bold('c'))),  # g (global) flag
    ("ABabAB", r"s/b/c/i", f"A{bold('c')}abAB"),  # i (case-insensitive) flag
    ("ABabAB", r"s/b/c/ig", f"A{bold('c')}a{bold('c')}A{bold('c')}"),  # both flags
    # /me (CTCP ACTION) lines
    ("\x01ACTION does nothing.\x01", r"s/no/some/", f"does {bold('some')}thing."),
)


@pytest.mark.parametrize('original, command, result', REPLACES_THAT_WORK)
def test_valid_replacements(bot, irc, user, channel, original, command, result):
    """Verify that basic replacement functionality works."""
    irc.channel_joined(channel, [user.nick])

    irc.say(user, channel, original)
    irc.say(user, channel, command)

    assert len(bot.backend.message_sent) == 1, (
        "The bot should respond with exactly one line.")
    assert bot.backend.message_sent == rawlist(
        "PRIVMSG %s :%s meant to say: %s" % (channel, user.nick, result),
    )


def test_multiple_users(bot, irc, user, other_user, channel):
    """Verify that correcting another user's line works."""
    irc.channel_joined(channel, [user.nick, other_user.nick])

    irc.say(other_user, channel, 'Some weather we got yesterday')
    irc.say(user, channel, '%s: s/yester/to/' % other_user.nick)

    assert len(bot.backend.message_sent) == 1, (
        "The bot should respond with exactly one line.")
    assert bot.backend.message_sent == rawlist(
        "PRIVMSG %s :%s thinks %s meant to say: %s" % (
            channel, user.nick, other_user.nick,
            f"Some weather we got {bold('to')}day",
        ),
    )


def test_replace_the_replacement(bot, irc, user, channel):
    """Verify replacing text that was already replaced."""
    irc.channel_joined(channel, [user.nick])

    irc.say(user, channel, 'spam')
    irc.say(user, channel, 's/spam/eggs/')
    irc.say(user, channel, 's/eggs/bacon/')

    assert len(bot.backend.message_sent) == 2, (
        "The bot should respond twice.")
    assert bot.backend.message_sent == rawlist(
        "PRIVMSG %s :%s meant to say: %s" % (
            channel, user.nick, bold('eggs'),
        ),
        "PRIVMSG %s :%s meant to say: %s" % (
            channel, user.nick, bold('bacon'),
        ),
    )


TMP_CONFIG_SNIPPET = """
[core]
owner = Admin
nick = Sopel
enable =
    find
host = irc.libera.chat

[find]
context_words = 2
"""


@pytest.fixture
def snippet_bot(botfactory, configfactory):
    settings = configfactory('snippet.ini', TMP_CONFIG_SNIPPET)
    return botfactory.preloaded(settings, ['find'])


@pytest.fixture
def snippet_irc(snippet_bot, ircfactory):
    return ircfactory(snippet_bot)


LUNCH = (
    "we should grab lunch at the new ramen place near the office "
    "before it gets too crowded around noon and the wait becomes unreasonable"
)


def highlight(line, old, new, count=1, context_words=-1):
    """Call ``replace_highlight()`` the way ``findandreplace()`` does."""
    return replace_highlight(
        re.compile(re.escape(old)), line, new, count, context_words)


SNIPPETS = (
    # context_words, expected display
    # -1 keeps the whole line, which is Sopel's behavior before this option
    (-1, "we should grab lunch at the new %s place near the office "
         "before it gets too crowded around noon and the wait becomes "
         "unreasonable" % bold('sushi')),
    (0, "%s%s%s" % (ELLIPSIS, bold('sushi'), ELLIPSIS)),
    (1, "%snew %s place%s" % (ELLIPSIS, bold('sushi'), ELLIPSIS)),
    (2, "%sthe new %s place near%s" % (ELLIPSIS, bold('sushi'), ELLIPSIS)),
    (3, "%sat the new %s place near the%s" % (ELLIPSIS, bold('sushi'), ELLIPSIS)),
)


@pytest.mark.parametrize('context_words, expected', SNIPPETS)
def test_snippet_context_words(context_words, expected):
    """Each context size keeps that many whole words on either side."""
    new_line, new_display = highlight(
        LUNCH, 'ramen', 'sushi', context_words=context_words)

    assert new_line == LUNCH.replace('ramen', 'sushi')
    assert new_display == expected


def test_snippet_keeps_the_matched_word_whole():
    """A match inside a word keeps the rest of that word, not a fragment."""
    _, new_display = highlight('does nothing.', 'no', 'some', context_words=0)

    assert new_display == "%s%sthing." % (ELLIPSIS, bold('some'))


def test_snippet_no_ellipsis_at_start_of_line():
    """Nothing was trimmed on the left, so there is no leading ellipsis."""
    _, new_display = highlight('ramen is good', 'ramen', 'sushi', context_words=1)

    assert new_display == "%s is%s" % (bold('sushi'), ELLIPSIS)


def test_snippet_no_ellipsis_at_end_of_line():
    """Nothing was trimmed on the right, so there is no trailing ellipsis."""
    _, new_display = highlight('I want ramen', 'ramen', 'sushi', context_words=1)

    assert new_display == "%swant %s" % (ELLIPSIS, bold('sushi'))


def test_snippet_short_line_is_not_trimmed():
    """A line shorter than the context window comes back whole."""
    _, new_display = highlight('a b c', 'b', 'x', context_words=5)

    assert new_display == "a %s c" % bold('x')


def test_snippet_global_flag_makes_one_window_per_match():
    """Each replacement gets its own window when they do not overlap."""
    _, new_display = highlight(
        'the cat sat on the mat and the cat was fat',
        'cat', 'dog', count=0, context_words=1)

    assert new_display == "the %s sat%sthe %s was%s" % (
        bold('dog'), ELLIPSIS, bold('dog'), ELLIPSIS)


def test_snippet_global_flag_merges_overlapping_windows():
    """Windows that run into each other are shown as one."""
    _, new_display = highlight('cat cat', 'cat', 'dog', count=0, context_words=2)

    assert new_display == "%s %s" % (bold('dog'), bold('dog'))


def test_snippet_deletion_has_no_empty_bold():
    """Deleting text leaves no zero-width bold sequence in the output.

    A deletion sits between words rather than inside one, so it takes
    ``context_words`` words on each side and keeps no word of its own.
    """
    new_line, new_display = highlight(
        LUNCH, 'ramen ', '', context_words=2)

    assert new_line == LUNCH.replace('ramen ', '')
    assert bold('') not in new_display
    assert new_display == "%sthe new place near%s" % (ELLIPSIS, ELLIPSIS)


def test_replace_highlight_returns_none_when_nothing_matches():
    """No match means no display string, and the line is untouched."""
    new_line, new_display = highlight('a simple line', 'zzz', 'yyy')

    assert new_line == 'a simple line'
    assert new_display is None


def test_snippet_in_channel(snippet_bot, snippet_irc, user, channel):
    """The configured context size reaches the message the bot sends."""
    snippet_irc.channel_joined(channel, [user.nick])

    snippet_irc.say(user, channel, LUNCH)
    snippet_irc.say(user, channel, 's/ramen/sushi/')

    assert snippet_bot.backend.message_sent == rawlist(
        "PRIVMSG %s :%s meant to say: %sthe new %s place near%s" % (
            channel, user.nick, ELLIPSIS, bold('sushi'), ELLIPSIS),
    )


def test_snippet_honors_case_insensitive_flag():
    """Snippets are built from the same matches the i flag produces."""
    _, new_display = highlight(
        'The CAT sat on the mat', 'cat', 'dog', context_words=1)
    assert new_display is None

    regex = re.compile(re.escape('cat'), re.U | re.I)
    _, new_display = replace_highlight(regex, 'The CAT sat on the mat', 'dog', 1, 1)

    assert new_display == "The %s sat%s" % (bold('dog'), ELLIPSIS)


def test_snippet_me_line(snippet_bot, snippet_irc, user, channel):
    """A corrected /me line is trimmed like any other.

    Sopel strips the CTCP wrapper before a plugin sees the message, so an
    ACTION reaches ``find`` as ordinary text and takes the same path.
    """
    snippet_irc.channel_joined(channel, [user.nick])

    snippet_irc.say(
        user, channel,
        '\x01ACTION wanders off to the new ramen place near the office '
        'to think about it\x01')
    snippet_irc.say(user, channel, 's/ramen/sushi/')

    assert snippet_bot.backend.message_sent == rawlist(
        "PRIVMSG %s :%s meant to say: %sthe new %s place near%s" % (
            channel, user.nick, ELLIPSIS, bold('sushi'), ELLIPSIS),
    )


def test_snippet_keeps_the_start_of_a_matched_word():
    """A match partway into a word keeps the letters before it."""
    _, new_display = highlight(
        'I said something yesterday', 'thing', 'body', context_words=1)

    assert new_display == "%ssaid some%s yesterday" % (ELLIPSIS, bold('body'))


def test_snippet_ignores_surrounding_whitespace():
    """Trimming only whitespace does not earn an ellipsis."""
    _, new_display = highlight(
        '   the ramen place   ', 'ramen', 'sushi', context_words=5)

    assert new_display == "the %s place" % bold('sushi')


def test_snippet_no_ellipsis_between_adjacent_windows():
    """Nothing but a space between two windows is not worth an ellipsis."""
    _, new_display = highlight('cat cat', 'cat', 'dog', count=0, context_words=0)

    assert new_display == "%s %s" % (bold('dog'), bold('dog'))


def test_snippet_ellipsis_between_windows_with_a_word_between():
    """A word dropped between two windows does earn an ellipsis."""
    _, new_display = highlight(
        'cat x cat', 'cat', 'dog', count=0, context_words=0)

    assert new_display == "%s%s%s" % (bold('dog'), ELLIPSIS, bold('dog'))


def test_replace_highlight_ignores_a_substitution_that_changes_nothing():
    """Replacing a word with itself is not a correction.

    The line has to actually change. Matching alone is not enough, or
    ``s/word/word/`` would "correct" a line to exactly what it already said.
    """
    new_line, new_display = highlight('a simple line', 'simple', 'simple')

    assert new_line == 'a simple line'
    assert new_display is None


def test_no_reply_when_the_correction_changes_nothing(bot, irc, user, channel):
    """The bot keeps quiet rather than repeating the line back unchanged."""
    irc.channel_joined(channel, [user.nick])

    irc.say(user, channel, 'a simple line')
    irc.say(user, channel, 's/simple/simple/')

    assert bot.backend.message_sent == []


def whole_line_display(line, old, new, count=1):
    """The display string the whole-line (default) path produces."""
    return re.compile(re.escape(old)).sub(bold(new), line, count=count)


WHITESPACE_EDGED = (
    # a replacement that starts or ends with whitespace keeps its bold
    ('the cat', 'cat', 'dog ', 0, "%s%s" % (ELLIPSIS, bold('dog '))),
    ('the cat', 'cat', ' dog', 0, "%s%s" % (ELLIPSIS, bold(' dog'))),
    ('the cat', 'cat', 'dog ', 1, "the %s" % bold('dog ')),
)


@pytest.mark.parametrize('line, old, new, context_words, expected', WHITESPACE_EDGED)
def test_snippet_keeps_bold_on_whitespace_edged_replacement(
        line, old, new, context_words, expected):
    """Trimming whitespace at a window edge must not eat the replacement.

    ``s/cat/dog /`` is reachable: the plugin's rule captures the trailing
    space into the replacement.
    """
    _, new_display = highlight(line, old, new, context_words=context_words)

    assert new_display == expected


def test_snippet_mid_word_deletion_shows_the_changed_word():
    """Deleting inside a word shows that word, not a pair of ellipses."""
    _, new_display = highlight('does nothing.', 'th', '', context_words=0)

    assert new_display == "%snoing." % ELLIPSIS


def test_snippet_mid_word_deletion_with_context():
    """The same deletion picks up surrounding words as context is raised."""
    _, new_display = highlight('does nothing.', 'th', '', context_words=1)

    assert new_display == "does noing."


def test_snippet_between_word_deletion_stays_symmetric():
    """A deletion that takes its own separator claims no word of its own."""
    _, new_display = highlight(LUNCH, 'ramen ', '', context_words=2)

    assert new_display == "%sthe new place near%s" % (ELLIPSIS, ELLIPSIS)


DEGENERATE = (
    # cases where a snippet would be nothing but ellipses or empty
    ('the cat', 'cat', ' ', 1, 0),
    ('the cat', 'cat', '\n', 1, 0),
    ('ramen is good', 'ramen', '', 1, 0),
    ('ramen', 'ramen', '', 1, 0),
)


@pytest.mark.parametrize('line, old, new, count, context_words', DEGENERATE)
def test_snippet_falls_back_when_nothing_visible_would_remain(
        line, old, new, count, context_words):
    """A snippet that would show no content falls back to the whole line."""
    _, new_display = highlight(
        line, old, new, count=count, context_words=context_words)

    assert new_display == whole_line_display(line, old, new, count)


def test_snippet_never_renders_as_only_ellipses():
    """No input should produce a correction the reader cannot read."""
    cases = [
        ('the cat', 'cat', ' ', 1), ('the cat', 'cat', '\n', 1),
        ('ramen is good', 'ramen', '', 1), ('ramen', 'ramen', '', 1),
        ('a b c', ' ', '', 0), ('does nothing.', 'th', '', 1),
        ('   ', ' ', '', 0), ('a', 'a', '', 1),
    ]
    for context_words in (0, 1, 2):
        for line, old, new, count in cases:
            _, display = highlight(
                line, old, new, count=count, context_words=context_words)
            if display is None:
                continue
            visible = plain(display).replace(ELLIPSIS, '').strip()
            assert visible or display == whole_line_display(
                line, old, new, count), (
                    "%r s/%s/%s/ ctx %d gave unreadable %r"
                    % (line, old, new, context_words, display))
