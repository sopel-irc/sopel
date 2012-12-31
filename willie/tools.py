# coding=utf-8
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
        stderr('Function %s is deprecated.' % old.__name__)
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
    ''' A simple multi dimensional dict '''
    def __init__(self, default=None):
        self.default = default

    def __getitem__(self, key):
        if not self.has_key(key):
            self[key] = self.default()
        return dict.__getitem__(self, key)

class OutputRedirect:
    ''' A simple object to replace stdout and stderr '''
    def __init__(self, logpath, stderr=False, quiet = False):
        self.logpath = logpath
        self.stderr = stderr
        self.quiet = quiet
    def write(self,string):
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

def stdout(string):
    ''' Print to stdout '''
    print string
        
def stderr(string):
    ''' Print to stderr '''
    print >> sys.stderr, string
        
def check_pid(pid):
    """ Check if process is running by pid. """
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    else:
        return True

def verify_ssl_cn(server, port):
    if not ssl:
        return None
    cert = None
    for version in (ssl.PROTOCOL_TLSv1, ssl.PROTOCOL_SSLv3, ssl.PROTOCOL_SSLv23):
        try:
            cert = ssl.get_server_certificate((server, port), ssl_version = version)
            break
        except Exception as e:
            pass
    if cert is None:
        return 'NoCertFound'
    valid = False;
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

