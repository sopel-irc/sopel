"""Utility functions to manage plugin callables from a Python module.

.. deprecated:: 8.1

    Plugin loading has been replaced by the plugin internal machinery.
    This will be removed in Sopel 9.

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
