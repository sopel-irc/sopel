#!/usr/bin/env python3
# coding=utf-8
from __future__ import unicode_literals, absolute_import, print_function, division
import sys
# Different from setuptools script, because we want the one in this dir.
from sopel.cli import run
sys.exit(run.main())
