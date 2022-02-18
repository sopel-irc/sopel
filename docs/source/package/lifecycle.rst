====================
Lifecycle Management
====================

As Sopel grows and evolves, sometimes it needs to say goodbye to obsolete code
and replace it. The solution can be new (and hopefully better) code, switching
to an external library, or maybe putting the feature into an external plugin.

In any case, Sopel will always try to mark as deprecated what will be removed,
indicating when it was deprecated, and when it should be removed. The goal is
to help Sopel developers and plugin authors understand what must be done to
adapt their code to a future version of Sopel::

    Deprecated since 8.0, will be removed in 9.0: sopel.module has been
    replaced by sopel.plugin
      File "/home/exirel/dev/sopel/sopel/module.py", line 46, in <module>
        deprecated(

This example above shows a deprecation warning for the ``sopel.module`` module
that is deprecated: it shows when it was deprecated (Sopel 8.0), when it will
be removed (Sopel 9.0), and how to fix that warning (use :mod:`sopel.plugin`).

Although this feature is primarily for use by Sopel developers, plugin authors
can also take advantage of it with the :func:`sopel.lifecycle.deprecated`
function documented below.

sopel.lifecycle
===============

.. automodule:: sopel.lifecycle
   :members:
