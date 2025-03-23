"""Utility functions to manage plugin callables from a Python module.

.. important::

    Its usage and documentation is for Sopel core development and advanced
    developers. It is subject to rapid changes between versions without much
    (or any) warning.

    Do **not** build your plugin based on what is here, you do **not** need to.

"""
from __future__ import annotations

import logging

from sopel.config.core_section import COMMAND_DEFAULT_HELP_PREFIX  # noqa
from sopel.lifecycle import deprecated
from sopel.plugins.callables import (  # noqa
    clean_callable,
    clean_module,
    is_limitable,
    is_triggerable,
    is_url_callback,
)


LOGGER = logging.getLogger(__name__)


deprecated(
    'sopel.loader has been replaced by the plugin internal machinery',
    version='8.1',
    removed_in='9.0',
    func=lambda *args: ...,
)()
