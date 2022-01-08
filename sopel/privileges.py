"""Constants for user privileges in channels.

Privilege levels
================

Historically, there were two user privileges in channels:

* :data:`OP`: channel operator, or chanop, set and unset by ``+o`` and ``-o``
* :data:`VOICE`: the privilege to send messages to a channel with the
  ``+m`` mode, set and unset by ``+v`` and ``-v``

Since then, other privileges have been adopted by IRC servers and clients:

* :data:`HALFOP`: intermediate level between Voiced and OP, set and unset by
  ``+h`` and ``-h``
* :data:`ADMIN`: channel admin, above OP and below OWNER, set and unset by
  ``+a`` and ``-a``
* :data:`OWNER`: channel owner, above ADMIN and OP, set and unset by ``+q`` and
  ``-q``

.. important::

    Not all IRC networks support these added privilege modes. If you are
    writing a plugin for public distribution, ensure your code behaves sensibly
    if only +v (voice) and +o (op) modes exist.

Compare privileges
==================

This module represents privileges as powers of two, with higher values assigned
to higher-level privileges::

    >>> from sopel.privileges import VOICE, HALFOP, OP, ADMIN, OWNER
    >>> VOICE < HALFOP < OP < ADMIN < OWNER
    True

Then a user's privileges are represented as a sum of privilege levels::

    >>> VOICE
    1
    >>> OP
    4
    >>> priv = VOICE | OP
    >>> priv
    5

This allows to use comparators and bitwise operators to compare privileges::

    >>> priv >= OP
    True
    >>> bool(priv & HALFOP)
    False

In that case, ``priv`` contains both VOICE and OP privileges, but not HALFOP.
"""
from __future__ import annotations


VOICE = 1
"""Privilege level for the +v channel permission

.. versionadded:: 4.1
.. versionchanged:: 8.0
   Moved into :mod:`sopel.privileges`.
"""

HALFOP = 2
"""Privilege level for the +h channel permission

.. versionadded:: 4.1
.. versionchanged:: 8.0
   Moved into :mod:`sopel.privileges`.

.. important::

    Not all IRC networks support this privilege mode. If you are writing a
    plugin for public distribution, ensure your code behaves sensibly if only
    ``+v`` (voice) and ``+o`` (op) modes exist.

"""

OP = 4
"""Privilege level for the +o channel permission

.. versionadded:: 4.1
.. versionchanged:: 8.0
   Moved into :mod:`sopel.privileges`.
"""

ADMIN = 8
"""Privilege level for the +a channel permission

.. versionadded:: 4.1
.. versionchanged:: 8.0
   Moved into :mod:`sopel.privileges`.

.. important::

    Not all IRC networks support this privilege mode. If you are writing a
    plugin for public distribution, ensure your code behaves sensibly if only
    ``+v`` (voice) and ``+o`` (op) modes exist.

"""

OWNER = 16
"""Privilege level for the +q channel permission

.. versionadded:: 4.1
.. versionchanged:: 8.0
   Moved into :mod:`sopel.privileges`.

.. important::

    Not all IRC networks support this privilege mode. If you are writing a
    plugin for public distribution, ensure your code behaves sensibly if only
    ``+v`` (voice) and ``+o`` (op) modes exist.

"""

OPER = 32
"""Privilege level for the +y/+Y channel permissions

Note: Except for these (non-standard) channel modes, Sopel does not monitor or
store any user's OPER status.

.. versionadded:: 7.0
.. versionchanged:: 8.0
   Moved into :mod:`sopel.privileges`.

.. important::

    Not all IRC networks support this privilege mode. If you are writing a
    plugin for public distribution, ensure your code behaves sensibly if only
    ``+v`` (voice) and ``+o`` (op) modes exist.

"""
