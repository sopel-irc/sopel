#!/usr/bin/env python3
# coding=utf-8
from __future__ import absolute_import, division, print_function, unicode_literals

import sys

# Different from setuptools script, because we want the one in this dir.
from sopel.cli import run

sys.exit(run.main())
