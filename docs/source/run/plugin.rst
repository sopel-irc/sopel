================
Managing plugins
================

.. highlight:: shell

Sopel is designed with plugins in mind: they add features/commands and can do
many things to make Sopel more useful or more fun to interact with on IRC.

There are two main types of plugins you can add:

* single file plugins that you drop into a folder
* packaged plugins that you install with ``pip``

A plugin can have its own configuration section, and may generate files or use
the database.

.. note::

    Make sure to read the documentation for the plugins you install and use.


Adding plugins
==============

Install single file plugins
---------------------------

To add a single file plugin to your Sopel instance, copy the file into the
bot's ``plugins`` directory under the
:attr:`~sopel.config.core_section.CoreSection.homedir` directory. By default,
the plugin file should be copied into ``~/.sopel/plugins``.

.. note::

    Following the :doc:`systemd service example <service>`, if your homedir is
    ``/var/lib/sopel`` then your plugin directory is
    ``/var/lib/sopel/plugins``.

Start (or restart) your bot and Sopel will load the plugin automatically.

Install packaged plugins
------------------------

Plugin authors might also publish their works as packages; you can find them by
searching PyPI, or by using your favorite search engine to search for
e.g. "sopel reminder plugin".

You can install these packages with ``pip``, the same way it is recommended to
install Sopel. All you need is to install the plugin for the same Python
interpreter.

For example, you can install the "remind" plugin from the ``sopel-remind``
package::

    python3 -m pip install sopel-remind

This will install the plugin from PyPI where you can see `all the releases`__
of this package.

.. note::

    Each plugin can have specific system dependencies or other requirements
    that you need to take care of when installing it. Refer to the plugin's
    documentation for more details.

.. __: https://pypi.org/project/sopel-remind/


Enabling or disabling plugins
=============================

By default, any plugins that Sopel can load will be automatically enabled: it
is true for all types of plugins (built-in, single file, or packaged plugins).
You can control this behavior by disabling some plugins, or enabling only some
plugins.

You can disable a plugin by using the ``sopel-plugins disable`` command line,
e.g. to disable the remind plugin mentioned before::

    sopel-plugins disable remind

This will add the plugin to the
:attr:`~sopel.config.core_section.CoreSection.exclude` list. The next time the
bot starts (or restarts), the plugin won't be loaded.

You can re-enable a plugin by using the ``sopel-plugins enable`` command line,
e.g. to re-enable the remind plugin::

    sopel-plugins enable remind

Which will remove the plugin from the ``exclude`` list. The plugin will be
loaded as before the next time the bot starts (or restarts).

Enable-only plugins
-------------------

By default, all plugins are enabled, and you disable plugins one by one.
However, you may want to enable only a set of plugins, and disable every other
one by default.

The ``enable`` command has an ``--allow-only`` option. For example, to add the
``remind`` plugin to the :attr:`~sopel.config.core_section.CoreSection.enable`
list, you would use this command line::

    sopel-plugins enable --allow-only remind

When you start the bot (or restart), the bot will load the plugins from the
``enable`` list, and **only these plugins**.

.. note::

    You only need to use the ``--enable-only`` option once. If the ``enable``
    list is not empty, ``sopel-plugins enable`` and ``sopel-plugins disable``
    will add and remove plugins in that list.


Configuring plugins
===================

Some (but not all!) plugins define their own configuration sections so you can
configure their behavior. If a plugin supports it, you may be able to use the
configuration wizard to do this::

    sopel-plugins configure remind

Alternatively, you can edit your configuration file and follow the plugin's
documentation to set the appropriate options and values. Here's an
example configuration of the `sopel-remind plugin`__, which defines the
``[remind]`` section for its own use:

.. __: https://pypi.org/project/sopel-remind/


.. code-block:: INI

    [core]
    # Sopel core's section

    [remind]
    # remind's section
    location = /path/to/remind/location

.. important::

    Sopel must be restarted after making changes to the configuration file.

