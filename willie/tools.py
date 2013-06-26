# coding=utf-8
"""
*Availability: 3+*
``tools`` contains a number of useful miscellaneous tools and shortcuts for use
in Willie modules.
"""
"""
tools.py - Willie misc tools
Copyright 2008, Sean B. Palmer, inamidst.com
Copyright © 2012, Elad Alfassa <elad@fedoraproject.org>
Copyright 2012, Edward Powell, embolalia.net
Licensed under the Eiffel Forum License 2.

https://willie.dftba.net
"""
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


def get_command_regexp(prefix, command):
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


# from http://parand.com/say/index.php/2007/07/13/simple-multi-dimensional-dictionaries-in-python/
# A simple class to make mutli dimensional dict easy to use
class Ddict(dict):
    """
    A simple helper class to ease the creation of multi-dimensional ``dict``\s.
    """

    def __init__(self, default=None):
        self.default = default

    def __getitem__(self, key):
        if key not in self:
            self[key] = self.default()
        return dict.__getitem__(self, key)


class Nick(unicode):
    """
    A `unicode` subclass which acts appropriately for an IRC nickname. When used
    as normal `unicode` objects, case will be preserved. However, when comparing
    two Nick objects, or comparing a Nick object with a `unicode` object, the
    comparison will be case insensitive. This case insensitivity includes the
    case convention conventions regarding ``[]``, ``{}``, ``|``, ``\\``, ``^``
    and ``~`` described in RFC 2812.
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
        """Return `nick`, converted to lower-case per RFC 2812"""
        return self._lowered

    @staticmethod
    def _lower(nick):
        """Returns `nick` in lower case per RFC 2812"""
        # The tilde replacement isn't needed for nicks, but is for channels,
        # which may be useful at some point in the future.
        low = nick.lower().replace('{', '[').replace('}', ']')
        low = low.replace('|', '\\').replace('^', '~')
        return low

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
    """
    A simplified object used to write to both the terminal and a log file.
    """

    def __init__(self, logpath, stderr=False, quiet=False):
        """
        Create an object which will log to the file at ``logpath`` as well as
        the terminal. If ``stderr`` is given and true, it will write to stderr
        rather than stdout. If ``quiet`` is given and True, data will be
        written to the log file only, but not the terminal.
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
    """
    Print the given ``string`` to stderr. This is equivalent to ``print >>
    sys.stderr, string``
    """
    print >> sys.stderr, string


def check_pid(pid):
    """
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
    """
    *Availability: Must have the OpenSSL Python module installed.*

    Verify the SSL certificate given by the ``server`` when connecting on the
    given ``port``. This returns ``None`` if OpenSSL is not available or
    'NoCertFound' if there was no certificate given. Otherwise, a two-tuple
    containing a boolean of whether the certificate is valid and the
    certificate information is returned.
    """
    if not ssl:
        return None
    cert = None
    for version in (ssl.PROTOCOL_TLSv1, ssl.PROTOCOL_SSLv3, ssl.PROTOCOL_SSLv23):
        try:
            cert = ssl.get_server_certificate((server, port), ssl_version=version)
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
    """
    *Availability: 4.0; available as ``Willie.WillieMemory`` in 3.1.0 - 3.2.0*

    A simple thread-safe dict implementation. In order to prevent
    exceptions when iterating over the values and changing them at the same
    time from different threads, we use a blocking lock on ``__setitem__``
    and ``contains``.
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
        """
        Check if a key is in the dict, locking it for writes when doing so.
        """
        self.lock.acquire()
        result = dict.__contains__(self, key)
        self.lock.release()
        return result

    def contains(self, key):
        """ Backwards compatability with 3.x, use `in` operator instead """
        return self.__contains__(key)

    def lock():
        """ Lock this instance from writes. Useful if you want to iterate """
        return self.lock.acquire()

    def unlock():
        """ Release the write lock """
        return self.lock.release()
