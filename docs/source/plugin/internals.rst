==================
Internal machinery
==================

.. important::

   This section contains modules and classes used by Sopel internally. They are
   subject to rapid changes between versions. They are documented here for
   completeness, and for the aid of Sopel’s core development.


sopel.loader
============

.. automodule:: sopel.loader
   :members:

sopel.plugins
=============

.. automodule:: sopel.plugins
   :members:

sopel.plugins.exceptions
========================

.. automodule:: sopel.plugins.exceptions
   :members:

sopel.plugins.handlers
======================

.. automodule:: sopel.plugins.handlers
   :members:

sopel.plugins.jobs
==================

.. automodule:: sopel.plugins.jobs
   :members:
   :show-inheritance:

sopel.plugins.rules
===================

.. automodule:: sopel.plugins.rules
   :members:
   :show-inheritance:

   .. autoclass:: AbstractRule
      :members:
      :undoc-members:

   .. autoclass:: AbstractNamedRule
      :members:
      :undoc-members:

   .. class:: TypedRule

      A :class:`~typing.TypeVar` bound to :class:`AbstractRule`. When used in
      the :meth:`AbstractRule.from_callable` class method, it means the return
      value must be an instance of the class used to call that method and not a
      different subclass of ``AbstractRule``.

      .. versionadded:: 8.0

         This ``TypeVar`` was added as part of a goal to start type-checking
         Sopel and is not used at runtime.

      .. TODO remove when sphinx-autodoc can manage TypeVar properly.
