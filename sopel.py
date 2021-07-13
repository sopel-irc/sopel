#!/usr/bin/env python3
from __future__ import generator_stop

import sys

# Different from setuptools script, because we want the one in this dir.
from sopel.cli import run

sys.exit(run.main())
