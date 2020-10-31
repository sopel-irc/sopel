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
    ctcp as _future_ctcp,
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


def intent(*intent_list):
    """Decorate a callable to trigger on intent messages.

    :param str intent_list: one or more intent(s) on which to trigger (really,
                            the only useful value is ``ACTION``)

    .. versionadded:: 5.2.0

    .. deprecated:: 7.1

    .. important::

        This will be removed in Sopel 9, as the IRCv3 intent specification is
        long dead. You can use :func:`@ctcp <sopel.plugin.ctcp>` instead.
    """
    return _future_ctcp(*intent_list)
