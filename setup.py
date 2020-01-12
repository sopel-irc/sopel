#!/usr/bin/env python
# coding=utf-8
from __future__ import unicode_literals, absolute_import, print_function, division

import sys
import time

try:
    from setuptools import setup, __version__ as setuptools_version
except ImportError:
    print(
        'You do not have setuptools, and can not install Sopel. The easiest '
        'way to fix this is to install pip by following the instructions at '
        'https://pip.readthedocs.io/en/latest/installing/\n'
        'Alternately, you can run Sopel without installing it by running '
        '"python sopel.py"',
        file=sys.stderr,
    )
    sys.exit(1)
else:
    version_info = setuptools_version.split('.')
    major = int(version_info[0])
    minor = int(version_info[1])

    if major < 30 or (major == 30 and minor < 3):
        print(
            'Your version of setuptools is outdated: version 30.3 or above '
            'is required to install Sopel. You can do that with '
            '"pip install -U setuptools"\n'
            'Alternately, you can run Sopel without installing it by running '
            '"python sopel.py"',
            file=sys.stderr,
        )
        sys.exit(1)

# We check Python's version ourselves in case someone installed Sopel on an
# old version of pip (<9.0.0), which doesn't know about `python_requires`.
if sys.version_info < (2, 7) or (
    sys.version_info.major >= 3 and sys.version_info < (3, 3)
):
    # Maybe not the best way to do this, but this question is tiring.
    raise ImportError('Sopel requires Python 2.7+ or 3.3+.')
# Py2 EOL: https://www.python.org/dev/peps/pep-0373/#maintenance-releases
if sys.version_info.major == 2:
    now = time.time()
    state = "has reached end of life"
    if now >= 1588291200:  # 2020-05-01 00:00:00 UTC
        state += " and will receive no further updates"
    print(
        "Warning: Python 2 %s. Sopel 8.0 will drop support for it." % state,
        file=sys.stderr,
    )


def read_reqs(path):
    with open(path, 'r') as fil:
        return list(fil.readlines())


requires = read_reqs('requirements.txt')
if sys.version_info[0] < 3:
    requires.append('backports.ssl_match_hostname')
dev_requires = requires + read_reqs('dev-requirements.txt')

setup(
    install_requires=requires, extras_require={"dev": dev_requires},
)
