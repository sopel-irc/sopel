=================
What is a Plugin?
=================

Before writing your first plugin, you may want to know what is a plugin, how is
it made, and what are the best solutions for your need. In this chapter we'll
cover what is a plugin, what you can do with them, and some vocabulary.

You may want to skip ahead to :doc:`anatomy` if you already know what a plugin
is and what types of plugin there are.

.. contents::
    :local:
    :depth: 2

Plugin Types
============

There are four types of plugins: :term:`Single file plugin`,
:term:`Folder plugin`, :term:`Namespace package plugin`, and
:term:`Entry point plugin`.

Single file
-----------

A **Single file** plugin is the most basic form a Sopel plugin can take. It is
composed of a single file available to Sopel from its plugins directory (or
from one of its
:attr:`extra directories <sopel.config.core_section.CoreSection.extra>`). You
should write a single file plugin when:

* everything is in a single file
* you don't have any dependencies other than Sopel and the Python's built-in
  library

This type of plugin is easy to install and share: copy its file into the right
location, and Sopel will load it on startup.

Folder
------

A **Folder** plugin is a folder that contains a ``__init__.py`` file. It is
available to Sopel the same way a :ref:`Single file` plugin is, and shares the
same limitation: Everything that is not available in this ``__init__.py`` file
won't be visible to Sopel.

By default, Sopel's plugin directories are **not** available in ``sys.path``,
so it is not possible to do ``from my_plugin_dir import some_module`` without
a specific configuration from the bot's owner.

When a plugin author wants to split code into different files, and/or share it
between multiple plugins, the best option is to use an :ref:`Entry point`
plugin instead.

Namespace package
-----------------

A **Namespace package** plugin is a Python :term:`namespace package`, using
the namespace ``sopel_modules``. It must be installed in the Python environment
to be used by Sopel, and can require Python dependencies.

Given a ``sopel_modules.plugin`` plugin, Sopel will load everything that is
available from the ``sopel_modules/plugin/__init__.py`` file.

It is the initial version of Sopel's packaged plugins: it can be packaged and
uploaded to `PyPI`_ then installed using ``pip install``.

When a plugin author wants to distribute a Sopel plugin, the best option is to
use an :ref:`Entry point` plugin instead.

Entry point
-----------

.. versionadded:: 7.0.0

An **Entry point** plugin is a Python module or package distributed via a
``setup.py`` script, and it is available to Sopel via Sopel's ``sopel.plugins``
`setup entry point`__.

Given this definition of an entry point from a ``setup.cfg`` file::

   [options.entry_points]
   sopel.plugins =
       my_plugin = package_name.my_plugin_file

Sopel will load everything available from the ``package_name.my_plugin_file``
Python module under the plugin name ``my_plugin``. It means that you can have
any package name and any module name as long as it is a valid Python module
and as long as you properly define the entry point.

You should write an entry point plugin when:

* you want to distribute your plugin on `PyPI`_
* you want to split the code in multiple files
* you have dependencies beyond Sopel and Python's standard library
* you want a modern and reliable way to package your Sopel plugin
* you want to distribute more than one Sopel plugin per distributed package

An entry point plugin is the best way to package and distribute a Sopel plugin
or collection of plugins in a clean and easy-to-update manner.

Note that a single Python distributed package can expose more than one Sopel
entry point plugin, which is great to bundle multiple plugins at once.

.. seealso::

   The PyPA specification explains in its `Entry points specification`_ what
   entry points are and how to use them.

.. __: `Entry points specification`_


Naming plugins
==============

Sopel plugins conventionally have all-lowercase names, usually one word.
However, sometimes multiple words are needed for clarity or disambiguation;
``snake_case`` is normally used for these.

How Sopel determines a plugin's name depends on what kind of plugin it is:

Single file
   The file's basename (e.g. ``plugin`` in ``plugin.py``)

Folder
   The folder name (e.g. ``plugin`` in ``~/.sopel/plugins/plugin/__init__.py``)

Namespace package
   The submodule name (e.g. ``plugin`` in ``sopel_modules.plugin``)

Entry point
   The entry point name (e.g. ``plugin`` in ``plugin = my_plugin.module.path``)

.. _PyPI: https://pypi.org/
.. _Entry points specification: https://packaging.python.org/specifications/entry-points/
