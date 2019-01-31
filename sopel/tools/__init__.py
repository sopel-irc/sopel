# coding=utf-8
"""Useful miscellaneous tools and shortcuts for Sopel modules

*Availability: 3+*
"""

# tools.py - Sopel misc tools
# Copyright 2008, Sean B. Palmer, inamidst.com
# Copyright © 2012, Elad Alfassa <elad@fedoraproject.org>
# Copyright 2012, Elsie Powell, embolalia.com
# Licensed under the Eiffel Forum License 2.

# https://sopel.chat

from __future__ import unicode_literals, absolute_import, print_function, division

import sys
import os
import re
import threading
import codecs
import traceback
from collections import defaultdict

from sopel.tools._events import events  # NOQA

if sys.version_info.major >= 3:
    raw_input = input
    unicode = str
    iteritems = dict.items
    itervalues = dict.values
    iterkeys = dict.keys
else:
    iteritems = dict.iteritems
    itervalues = dict.itervalues
    iterkeys = dict.iterkeys

_channel_prefixes = ('#', '&', '+', '!')

# Can be implementation-dependent
_regex_type = type(re.compile(''))


def get_input(prompt):
    """Get decoded input from the terminal (equivalent to python 3's ``input``).
    """
    if sys.version_info.major >= 3:
        return input(prompt)
    else:
        return raw_input(prompt).decode('utf8')


def get_raising_file_and_line(tb=None):
    """Return the file and line number of the statement that raised the tb.

    Returns: (filename, lineno) tuple

    """
    if not tb:
        tb = sys.exc_info()[2]

    filename, lineno, _context, _line = traceback.extract_tb(tb)[-1]

    return filename, lineno


def compile_rule(nick, pattern, alias_nicks):
    """
    Return a compiled rule regex, replacing placeholders for ``$nick`` and
    ``$nickname`` with the values defined in the bot's config at startup.
    """
    # Not sure why this happens on reloads, but it shouldn't cause problems…
    if isinstance(pattern, _regex_type):
        return pattern

    if alias_nicks:
        nicks = list(alias_nicks)  # alias_nicks.copy() doesn't work in py2
        nicks.append(nick)
        nicks = map(re.escape, nicks)
        nick = '(?:%s)' % '|'.join(nicks)
    else:
        nick = re.escape(nick)

    pattern = pattern.replace('$nickname', nick)
    pattern = pattern.replace('$nick', r'{}[,:]\s+'.format(nick))
    flags = re.IGNORECASE
    if '\n' in pattern:
        flags |= re.VERBOSE
    return re.compile(pattern, flags)


def get_command_regexp(prefix, command):
    """Return a compiled regexp object that implements the command."""
    # Escape all whitespace with a single backslash. This ensures that regexp
    # in the prefix is treated as it was before the actual regexp was changed
    # to use the verbose syntax.
    prefix = re.sub(r"(\s)", r"\\\1", prefix)

    pattern = get_command_pattern(prefix, command)
    return re.compile(pattern, re.IGNORECASE | re.VERBOSE)


def get_command_pattern(prefix, command):
    """Return the uncompiled regex pattern for standard commands."""
    # This regexp matches equivalently and produces the same
    # groups 1 and 2 as the old regexp: r'^%s(%s)(?: +(.*))?$'
    # The only differences should be handling all whitespace
    # like spaces and the addition of groups 3-6.
    return r"""
        (?:{prefix})({command}) # Command as group 1.
        (?:\s+              # Whitespace to end command.
        (                   # Rest of the line as group 2.
        (?:(\S+))?          # Parameters 1-4 as groups 3-6.
        (?:\s+(\S+))?
        (?:\s+(\S+))?
        (?:\s+(\S+))?
        .*                  # Accept anything after the parameters.
                            # Leave it up to the module to parse
                            # the line.
        ))?                 # Group 2 must be None, if there are no
                            # parameters.
        $                   # EoL, so there are no partial matches.
        """.format(prefix=prefix, command=command)


def get_nickname_command_regexp(nick, command, alias_nicks):
    """Return a compiled regexp object that implements the nickname command."""
    if isinstance(alias_nicks, unicode):
        alias_nicks = [alias_nicks]
    elif not isinstance(alias_nicks, list):
        raise ValueError('A list or string is required.')

    return compile_rule(nick, get_nickname_command_pattern(command), alias_nicks)


def get_nickname_command_pattern(command):
    """Return the uncompiled regex pattern for nickname commands."""
    return r"""
        ^
        $nickname[:,]? # Nickname.
        \s+({command}) # Command as group 1.
        (?:\s+         # Whitespace to end command.
        (              # Rest of the line as group 2.
        (?:(\S+))?     # Parameters 1-4 as groups 3-6.
        (?:\s+(\S+))?
        (?:\s+(\S+))?
        (?:\s+(\S+))?
        .*             # Accept anything after the parameters. Leave it up to
                       # the module to parse the line.
        ))?            # Group 1 must be None, if there are no parameters.
        $              # EoL, so there are no partial matches.
        """.format(command=command)


def get_sendable_message(text, max_length=400):
    """Get a sendable ``text`` message, with its excess when needed.

    :param str txt: unicode string of text to send
    :param int max_length: maximum length of the message to be sendable
    :return: a tuple of two values, the sendable text and its excess text

    We're arbitrarily saying that the max is 400 bytes of text when
    messages will be split. Otherwise, we'd have to account for the bot's
    hostmask, which is hard.

    The `max_length` is the max length of text in **bytes**, but we take
    care of unicode 2-bytes characters, by working on the unicode string,
    then making sure the bytes version is smaller than the max length.
    """
    unicode_max_length = max_length
    excess = ''

    while len(text.encode('utf-8')) > max_length:
        last_space = text.rfind(' ', 0, unicode_max_length)
        if last_space == -1:
            # No last space, just split where it is possible
            excess = text[unicode_max_length:] + excess
            text = text[:unicode_max_length]
            # Decrease max length for the unicode string
            unicode_max_length = unicode_max_length - 1
        else:
            # Split at the last best space found
            excess = text[last_space:]
            text = text[:last_space]

    return text, excess.lstrip()


def deprecated(old):
    def new(*args, **kwargs):
        print('Function %s is deprecated.' % old.__name__, file=sys.stderr)
        trace = traceback.extract_stack()
        for line in traceback.format_list(trace[:-1]):
            stderr(line[:-1])
        return old(*args, **kwargs)
    new.__doc__ = old.__doc__
    new.__name__ = old.__name__
    return new


# from
# http://parand.com/say/index.php/2007/07/13/simple-multi-dimensional-dictionaries-in-python/
# A simple class to make mutli dimensional dict easy to use
class Ddict(dict):

    """Class for multi-dimensional ``dict``.

    A simple helper class to ease the creation of multi-dimensional ``dict``\\s.

    """

    def __init__(self, default=None):
        self.default = default

    def __getitem__(self, key):
        if key not in self:
            self[key] = self.default()
        return dict.__getitem__(self, key)


class Identifier(unicode):
    """A `unicode` subclass which acts appropriately for IRC identifiers.

    When used as normal `unicode` objects, case will be preserved.
    However, when comparing two Identifier objects, or comparing a Identifier
    object with a `unicode` object, the comparison will be case insensitive.
    This case insensitivity includes the case convention conventions regarding
    ``[]``, ``{}``, ``|``, ``\\``, ``^`` and ``~`` described in RFC 2812.
    """

    def __new__(cls, identifier):
        # According to RFC2812, identifiers have to be in the ASCII range.
        # However, I think it's best to let the IRCd determine that, and we'll
        # just assume unicode. It won't hurt anything, and is more internally
        # consistent. And who knows, maybe there's another use case for this
        # weird case convention.
        s = unicode.__new__(cls, identifier)
        s._lowered = Identifier._lower(identifier)
        return s

    def lower(self):
        """Return the identifier converted to lower-case per RFC 2812."""
        return self._lowered

    @staticmethod
    def _lower(identifier):
        """Returns `identifier` in lower case per RFC 2812."""
        if isinstance(identifier, Identifier):
            return identifier._lowered
        # The tilde replacement isn't needed for identifiers, but is for
        # channels, which may be useful at some point in the future.
        low = identifier.lower().replace('{', '[').replace('}', ']')
        low = low.replace('|', '\\').replace('^', '~')
        return low

    def __repr__(self):
        return "%s(%r)" % (
            self.__class__.__name__,
            self.__str__()
        )

    def __hash__(self):
        return self._lowered.__hash__()

    def __lt__(self, other):
        if isinstance(other, unicode):
            other = Identifier._lower(other)
        return unicode.__lt__(self._lowered, other)

    def __le__(self, other):
        if isinstance(other, unicode):
            other = Identifier._lower(other)
        return unicode.__le__(self._lowered, other)

    def __gt__(self, other):
        if isinstance(other, unicode):
            other = Identifier._lower(other)
        return unicode.__gt__(self._lowered, other)

    def __ge__(self, other):
        if isinstance(other, unicode):
            other = Identifier._lower(other)
        return unicode.__ge__(self._lowered, other)

    def __eq__(self, other):
        if isinstance(other, unicode):
            other = Identifier._lower(other)
        return unicode.__eq__(self._lowered, other)

    def __ne__(self, other):
        return not (self == other)

    def is_nick(self):
        """Returns True if the Identifier is a nickname (as opposed to channel)
        """
        return self and not self.startswith(_channel_prefixes)


class OutputRedirect(object):

    """Redirect te output to the terminal and a log file.

    A simplified object used to write to both the terminal and a log file.

    """

    def __init__(self, logpath, stderr=False, quiet=False):
        """Create an object which will to to a file and the terminal.

        Create an object which will log to the file at ``logpath`` as well as
        the terminal.
        If ``stderr`` is given and true, it will write to stderr rather than
        stdout.
        If ``quiet`` is given and True, data will be written to the log file
        only, but not the terminal.

        """
        self.logpath = logpath
        self.stderr = stderr
        self.quiet = quiet

    def write(self, string):
        """Write the given ``string`` to the logfile and terminal."""
        if not self.quiet:
            try:
                if self.stderr:
                    sys.__stderr__.write(string)
                else:
                    sys.__stdout__.write(string)
            except Exception:  # TODO: Be specific
                pass

        with codecs.open(self.logpath, 'ab', encoding="utf8",
                         errors='xmlcharrefreplace') as logfile:
            try:
                logfile.write(string)
            except UnicodeDecodeError:
                # we got an invalid string, safely encode it to utf-8
                logfile.write(unicode(string, 'utf8', errors="replace"))

    def flush(self):
        if self.stderr:
            sys.__stderr__.flush()
        else:
            sys.__stdout__.flush()


# These seems to trace back to when we thought we needed a try/except on prints,
# because it looked like that was why we were having problems. We'll drop it in
# 4.0^H^H^H5.0^H^H^H6.0^H^H^Hsome version when someone can be bothered.
@deprecated
def stdout(string):
    print(string)


def stderr(string):
    """Print the given ``string`` to stderr.

    This is equivalent to ``print >> sys.stderr, string``

    """
    print(string, file=sys.stderr)


def check_pid(pid):
    """Check if a process is running with the given ``PID``.

    *Availability: Only on POSIX systems*

    Return ``True`` if there is a process running with the given ``PID``.

    """
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    else:
        return True


def get_hostmask_regex(mask):
    """Return a compiled `re.RegexObject` for an IRC hostmask"""
    mask = re.escape(mask)
    mask = mask.replace(r'\*', '.*')
    return re.compile(mask + '$', re.I)


class SopelMemory(dict):

    """A simple thread-safe dict implementation.

    *Availability: 4.0; available as ``Sopel.SopelMemory`` in 3.1.0 - 3.2.0*

    In order to prevent exceptions when iterating over the values and changing
    them at the same time from different threads, we use a blocking lock on
    ``__setitem__`` and ``contains``.

    """
    def __init__(self, *args):
        dict.__init__(self, *args)
        self.lock = threading.Lock()

    def __setitem__(self, key, value):
        self.lock.acquire()
        result = dict.__setitem__(self, key, value)
        self.lock.release()
        return result

    def __contains__(self, key):
        """Check if a key is in the dict.

        It locks it for writes when doing so.

        """
        self.lock.acquire()
        result = dict.__contains__(self, key)
        self.lock.release()
        return result

    def contains(self, key):
        """Backwards compatability with 3.x, use `in` operator instead."""
        return self.__contains__(key)


class SopelMemoryWithDefault(defaultdict):
    """Same as SopelMemory, but subclasses from collections.defaultdict."""
    def __init__(self, *args):
        defaultdict.__init__(self, *args)
        self.lock = threading.Lock()

    def __setitem__(self, key, value):
        self.lock.acquire()
        result = defaultdict.__setitem__(self, key, value)
        self.lock.release()
        return result

    def __contains__(self, key):
        """Check if a key is in the dict.

        It locks it for writes when doing so.

        """
        self.lock.acquire()
        result = defaultdict.__contains__(self, key)
        self.lock.release()
        return result

    def contains(self, key):
        """Backwards compatability with 3.x, use `in` operator instead."""
        return self.__contains__(key)
