"""The :mod:`sopel.module` sub-module is replaced by :mod:`sopel.plugin`.

.. deprecated:: 7.1

    Use :mod:`sopel.plugin` instead. This will be removed in Sopel 9.

"""
from __future__ import annotations

from sopel.lifecycle import deprecated

# Import everything from sopel.plugin at the time of replacement.
# Everything new from this point on must *not* leak here.
# Therefore, don't add anything to this import list. Ever.
from sopel.plugin import (  # noqa
    action_commands,
    ADMIN,
    commands,
    ctcp as _future_ctcp,
    echo,
    event,
    example,
    HALFOP,
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


deprecated(
    'sopel.module has been replaced by sopel.plugin',
    version='8.0',
    removed_in='9.0',
    func=lambda *args: ...,
)()


@deprecated(
    '`@intent` is replaced by `sopel.plugin.ctcp`',
    version='7.1',
    removed_in='9.0',
    warning_in='8.0',
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
