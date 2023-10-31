"""help.py - Obsolete Sopel Help Plugin

Install ``sopel-help`` with ``pip install sopel-help`` to get the official
help plugin for Sopel.
"""
from __future__ import annotations

import logging


LOGGER = logging.getLogger(__name__)


def setup(bot):
    LOGGER.warning(
        'Sopel\'s built-in help plugin is obsolete. '
        'Install sopel-help as the official help plugin for Sopel.\n'
        'You can install sopel-help with "pip install sopel-help".')
