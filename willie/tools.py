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
try:
    import ssl
    import OpenSSL
    import re
except:
    #no SSL support
    ssl = False
import traceback


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
if __name__ == '__main__':
    print __doc__.strip()
