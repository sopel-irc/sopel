"""Sopel Command Line main entrypoint: ``python -m sopel``."""
# Copyright 2025, Florian Strzelecki <florian.strzelecki@gmail.com>
#
# Licensed under the Eiffel Forum License 2.
from __future__ import annotations

import sys

from sopel.cli.run import main


if __name__ == '__main__':
    sys.exit(main())
