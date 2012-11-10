#!/usr/bin/env python

from distutils.core import setup

setup(name = 'willie',
      version = '3.1',
      description = 'Simple and extendible IRC bot',
      author = 'Edward Powell',
      author_email = 'powell.518@gmail.com',
      url = 'http://willie.dftba.net/',
      long_description = """Willie is a simple, lightweight, open source, easy-to-use IRC Utility bot, written in Python. It's designed to be easy to use, easy to run, and easy to make new features for. """,
      packages = ['willie', 'willie.modules'],
      scripts = ['willie.py']
     )
