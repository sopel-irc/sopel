# coding=utf-8
"""
*Availability: 3+*
``tools`` contains a number of useful miscellaneous tools and shortcuts for use
in Willie modules.

tools.py - Willie misc tools
Copyright 2008, Sean B. Palmer, inamidst.com
Copyright © 2012, Elad Alfassa <elad@fedoraproject.org>
Copyright 2012, Edward Powell, embolalia.net
Licensed under the Eiffel Forum License 2.

https://willie.dftba.net
"""
from __future__ import division

import sys
import os
import re
import threading
try:
    import ssl
    import OpenSSL
except ImportError:
    #no SSL support
    ssl = False
import traceback
import Queue
import copy
import ast
import operator


class ExpressionEvaluator:

    """A generic class for evaluating limited forms of Python expressions.

    Instances can overwrite binary_ops and unary_ops attributes with dicts of
    the form {ast.Node, function}. When the ast.Node being used as key is
    found, it will be evaluated using the given function.

    """

    class Error(Exception):
        pass

    def __init__(self, bin_ops=None, unary_ops=None):
        self.binary_ops = bin_ops or {}
        self.unary_ops = unary_ops or {}

    def __call__(self, expression_str):
        """Evaluate a python expression and return the result.

        Raises:
            SyntaxError: If the given expression_str is not a valid python
                statement.
            ExpressionEvaluator.Error: If the instance of ExpressionEvaluator
                does not have a handler for the ast.Node.

        """
        ast_expression = ast.parse(expression_str, mode='eval')
        return self._eval_node(ast_expression.body)

    def _eval_node(self, node):
        """Recursively evaluate the given ast.Node.

        Uses self.binary_ops and self.unary_ops for the implementation.

        A subclass could overwrite this to handle more nodes, calling it only
        for nodes it does not implement it self.

        Raises:
            ExpressionEvaluator.Error: If it can't handle the ast.Node.

        """
        if isinstance(node, ast.Num):
            return node.n

        elif (isinstance(node, ast.BinOp) and
                type(node.op) in self.binary_ops):
            left = self._eval_node(node.left)
            right = self._eval_node(node.right)
            return self.binary_ops[type(node.op)](left, right)

        elif (isinstance(node, ast.UnaryOp) and
                type(node.op) in self.unary_ops):
            operand = self._eval_node(node.operand)
            return self.unary_ops[type(node.op)](operand)

        raise ExpressionEvaluator.Error(
            "Ast.Node '%s' not implemented." % (type(node).__name__,)
        )

_bin_ops = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.Mod: operator.mod,
    ast.FloorDiv: operator.floordiv,
}
_unary_ops = {
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}
eval_equation = ExpressionEvaluator(_bin_ops, _unary_ops)
"""Evaluates a Python equation expression and returns the result.

Supports addition (+), subtraction (-), multiplication (*), division (/),
power (**) and modulo (%).
"""


def get_raising_file_and_line(tb=None):
    """Return the file and line number of the statement that raised the tb.

    Returns: (filename, lineno) tuple

    """
    if not tb:
        tb = sys.exc_info()[2]

    filename, lineno, _context, _line = traceback.extract_tb(tb)[-1]

    return filename, lineno


def get_command_regexp(prefix, command):
    """Return a compiled regexp object that implements the command."""
    # Escape all whitespace with a single backslash. This ensures that regexp
    # in the prefix is treated as it was before the actual regexp was changed
    # to use the verbose syntax.
    prefix = re.sub(r"(\s)", r"\\\1", prefix)

    # This regexp match equivalently and produce the same
    # groups 1 and 2 as the old regexp: r'^%s(%s)(?: +(.*))?$'
    # The only differences should be handling all whitespace
    # like spaces and the addition of groups 3-6.
    pattern = r"""
        {prefix}({command}) # Command as group 1.
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
    return re.compile(pattern, re.IGNORECASE | re.VERBOSE)


def deprecated(old):
    def new(*args, **kwargs):
        print >> sys.stderr, 'Function %s is deprecated.' % old.__name__
        trace = traceback.extract_stack()
        for line in traceback.format_list(trace[:-1]):
            stderr(line[:-1])
        return old(*args, **kwargs)
    new.__doc__ = old.__doc__
    new.__name__ = old.__name__
    return new


class PriorityQueue(Queue.PriorityQueue):
    """A priority queue with a peek method."""
    def peek(self):
        """Return a copy of the first element without removing it."""
        self.not_empty.acquire()
        try:
            while not self._qsize():
                self.not_empty.wait()
            # Return a copy to avoid corrupting the heap. This is important
            # for thread safety if the object is mutable.
            return copy.deepcopy(self.queue[0])
        finally:
            self.not_empty.release()


class released(object):
    """A context manager that releases a lock temporarily."""
    def __init__(self, lock):
        self.lock = lock

    def __enter__(self):
        self.lock.release()

    def __exit__(self, _type, _value, _traceback):
        self.lock.acquire()


# from
# http://parand.com/say/index.php/2007/07/13/simple-multi-dimensional-dictionaries-in-python/
# A simple class to make mutli dimensional dict easy to use
class Ddict(dict):

    """Class for multi-dimensional ``dict``.

    A simple helper class to ease the creation of multi-dimensional ``dict``\s.

    """

    def __init__(self, default=None):
        self.default = default

    def __getitem__(self, key):
        if key not in self:
            self[key] = self.default()
        return dict.__getitem__(self, key)


class Nick(unicode):

    """A `unicode` subclass which acts appropriately for an IRC nickname.
    
    When used as normal `unicode` objects, case will be preserved.
    However, when comparing two Nick objects, or comparing a Nick object with a
    `unicode` object, the comparison will be case insensitive. This case
    insensitivity includes the case convention conventions regarding ``[]``,
    ``{}``, ``|``, ``\\``, ``^`` and ``~`` described in RFC 2812.

    """

    def __new__(cls, nick):
        # According to RFC2812, nicks have to be in the ASCII range. However,
        # I think it's best to let the IRCd determine that, and we'll just
        # assume unicode. It won't hurt anything, and is more internally
        # consistent. And who knows, maybe there's another use case for this
        # weird case convention.
        s = unicode.__new__(cls, nick)
        s._lowered = Nick._lower(nick)
        return s

    def lower(self):
        """Return `nick`, converted to lower-case per RFC 2812."""
        return self._lowered

    @staticmethod
    def _lower(nick):
        """Returns `nick` in lower case per RFC 2812."""
        # The tilde replacement isn't needed for nicks, but is for channels,
        # which may be useful at some point in the future.
        low = nick.lower().replace('{', '[').replace('}', ']')
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
        if isinstance(other, Nick):
            return self._lowered < other._lowered
        return self._lowered < Nick._lower(other)

    def __le__(self, other):
        if isinstance(other, Nick):
            return self._lowered <= other._lowered
        return self._lowered <= Nick._lower(other)

    def __gt__(self, other):
        if isinstance(other, Nick):
            return self._lowered > other._lowered
        return self._lowered > Nick._lower(other)

    def __ge__(self, other):
        if isinstance(other, Nick):
            return self._lowered >= other._lowered
        return self._lowered >= Nick._lower(other)

    def __eq__(self, other):
        if isinstance(other, Nick):
            return self._lowered == other._lowered
        return self._lowered == Nick._lower(other)

    def __ne__(self, other):
        return not (self == other)


class OutputRedirect:

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
            except:
                pass
        logfile = open(self.logpath, 'a')
        logfile.write(string.encode('utf8'))
        logfile.close()


#These seems to trace back to when we thought we needed a try/except on prints,
#because it looked like that was why we were having problems. We'll drop it in
#4.0
@deprecated
def stdout(string):
    print string


def stderr(string):
    """Print the given ``string`` to stderr.
    
    This is equivalent to ``print >> sys.stderr, string``

    """
    print >> sys.stderr, string


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


def verify_ssl_cn(server, port):
    """Verify the SSL certificate.

    *Availability: Must have the OpenSSL Python module installed.*

    Verify the SSL certificate given by the ``server`` when connecting on the
    given ``port``.

    This returns ``None`` if OpenSSL is not available or 'NoCertFound' if there
    was no certificate given.
    Otherwise, a two-tuple containing a boolean of whether the certificate is
    valid and the certificate information is returned.

    """
    if not ssl:
        return None
    cert = None
    for version in (
        ssl.PROTOCOL_TLSv1, ssl.PROTOCOL_SSLv3, ssl.PROTOCOL_SSLv23
    ):
        try:
            cert = ssl.get_server_certificate(
                (server, port), ssl_version=version
            )
            break
        except Exception as e:
            pass
    if cert is None:
        return 'NoCertFound'
    valid = False

    x509 = OpenSSL.crypto.load_certificate(OpenSSL.crypto.FILETYPE_PEM, cert)
    cret_info = x509.get_subject().get_components()
    cn = x509.get_subject().commonName
    if cn == server:
        valid = True
    elif '*' in cn:
        cn = cn.replace('*.', '')
        if re.match('(.*)%s' % cn, server, re.IGNORECASE) is not None:
            valid = True
    return (valid, cret_info)


class WillieMemory(dict):

    """A simple thread-safe dict implementation.

    *Availability: 4.0; available as ``Willie.WillieMemory`` in 3.1.0 - 3.2.0*

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

    def lock(self):
        """Lock this instance from writes. Useful if you want to iterate."""
        return self.lock.acquire()

    def unlock(self):
        """Release the write lock."""
        return self.lock.release()
