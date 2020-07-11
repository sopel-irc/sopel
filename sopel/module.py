# coding=utf-8
"""The :mod:`sopel.module` sub-module is replaced by :mod:`sopel.plugin`.

.. deprecated:: 7.1

    Use :mod:`sopel.plugin` instead. This will be removed in Sopel 9.

"""
from __future__ import absolute_import, division, print_function, unicode_literals

# Import everything from sopel.plugin at the time of replacement.
# Everything new from this point on must *not* leak here.
# Therefore, don't add anything to this import list. Ever.
from sopel.plugin import (  # noqa
    ADMIN,
    action_commands,
    commands,
    echo,
    event,
    example,
    HALFOP,
    intent,
    interval,
    nickname_commands,
    NOLIMIT,
    OP,
    OPER,
    output_prefix,
    OWNER,
    priority,
    rate,
    require_account,
    require_admin,
    require_chanmsg,
    require_owner,
    require_privilege,
    require_privmsg,
    rule,
    thread,
    unblockable,
    url,
    VOICE,
)
