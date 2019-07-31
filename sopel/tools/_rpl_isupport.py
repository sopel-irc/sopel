# coding=utf-8
from __future__ import unicode_literals, absolute_import, print_function, division


class isupport(object):
    """Constants used for various ``RPL_ISUPPORT`` functionality.

    .. versionadded:: 7.0
    """

    DEFAULT_VALUES = {  # Default values for RPL_ISUPPORT parameters
        'EXCEPTS': 'e',
        'INVEX': 'I',
        'METADATA': None,  # indicates there is no limit
        'SILENCE': None,  # indicates the server does not support the command
    }

    VALUES_CAST_TO = {  # RPL_ISUPPORT parameter (non-string) value types
        'ACCEPT': int,
        'AWAYLEN': int,
        'CHANNELLEN': int,
        'CLIENTVER': float,     # Deprecated
        'HOSTLEN': int,
        'KEYLEN': int,
        'KICKLEN': int,
        'LINELEN': int,         # Proposed
        'MAXBANS': int,         # Deprecated
        'MAXCHANNELS': int,     # Deprecated
        'MAXNICKLEN': int,
        'MAXPARA': int,         # Deprecated
        'MAXTARGETS': int,
        'METADATA': int,
        'MODES': int,
        'MONITOR': int,
        'NICKLEN': int,
        'SILENCE': int,
        'TOPICLEN': int,
        'USERLEN': int,         # Proposed
        'WATCH': int,
    }
