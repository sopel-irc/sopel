#!/usr/bin/env python
# coding=utf8
from __future__ import unicode_literals

from distutils.core import setup
from willie import __version__
import tempfile
import sys
import os
import shutil

requires = ['feedparser', 'pytz', 'lxml', 'praw', 'enchant', 'pygeoip']
if sys.version_info.major < 3:
    requires.append('backports.ssl_match_hostname')


def do_setup():
    try:
        # This special screwing is to make willie.py get installed to PATH as
        # willie, not willie.py. Don't remove it, or you'll break it.
        tmp_dir = tempfile.mkdtemp()
        tmp_main_script = os.path.join(tmp_dir, 'willie')
        shutil.copy('willie.py', tmp_main_script)

        setup(
            name='willie',
            version=__version__,
            description='Simple and extendible IRC bot',
            author='Edward Powell',
            author_email='powell.518@gmail.com',
            url='http://willie.dftba.net/',
            long_description="""Willie is a simple, lightweight, open source, easy-to-use IRC Utility bot, written in Python. It's designed to be easy to use, easy to run, and easy to make new features for. """,
            # Distutils is shit, and doesn't check if it's a list of basestring
            # but instead requires str.
            packages=[str('willie'), str('willie.modules')],
            scripts=[tmp_main_script],
            license='Eiffel Forum License, version 2',
            platforms='Linux x86, x86-64',
            requires=requires
        )
    finally:
        try:
            shutil.rmtree(tmp_dir)
        except OSError as e:
            if e.errno != 2:  # The directory is already gone, so ignore it
                raise


if __name__ == "__main__":
    do_setup()
