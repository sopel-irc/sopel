# coding=utf8
"""
certs.py - Willie certificates module
Copyright 2014, Michael Sverdlik

Licensed under the Eiffel Forum License 2.

http://willie.dftba.net/

This module provides simple method to discover Root CA certificate collection.
It will try using http://certifi.io at first, and if not found fall back to
searching in hard coded paths.
"""
from os.path import isfile

# possible candidates for system root certificate store
CA_PATHS = ['/etc/ssl/certs/ca-certificates.crt',
            '/etc/pki/tls/certs/ca-bundle.crt']


try:
    from certifi import where as get_cacert
except ImportError:
    def get_cacert():
        """
        Return first found certificate bundle
        """
        for path in CA_PATHS:
            if isfile(path):
                return path
