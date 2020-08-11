=====================
Plugin for Developers
=====================

.. toctree::
   :titlesonly:

   plugin/what
   plugin/anatomy
   plugin/decorators
   plugin/internals

Plugin glossary
===============

.. glossary::
   :sorted:

   Sopel Plugin
      A Sopel plugin is a plugin made for Sopel. It contains rule handlers
      and can have a ``setup`` and a ``shutdown`` functions. It is of one
      of the possible plugin types, preferably :term:`Single file plugin`, or
      :term:`Entry point plugin`. The other two types are :term:`Folder plugin`
      and :term:`Namespace package plugin`.

   Single file plugin
      A :term:`Sopel Plugin` composed of a single Python file. Can be loaded by
      Sopel even when it's not available from ``sys.path``.

   Folder plugin
      A plugin composed of a directory that contains a ``__init__.py`` file.
      It is not considered as a proper Python package unless it's parent
      directory is in ``sys.path``. As it can create confusion, they are not
      recommended, and either :term:`Single file plugin` or
      :term:`Entry point plugin` should be used instead.

   Namespace package plugin
      A plugin that is a Python namespace package, i.e. a package within a
      specific namespace (``sopel_modules.<name>``, where ``sopel_modules`` is
      the namespace, and ``<name>`` is the Plugin's name). This is the old way
      to distribute plugins and is not recommended; :term:`Entry point plugin`
      should be used instead.

   Entry point plugin
      A plugin that is an installed Python package and exposed through the
      ``sopel.plugins`` Python setup entry point named.
