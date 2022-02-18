===================
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
