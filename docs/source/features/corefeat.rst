============
Key features
============

Sopel is an IRC Bot: it can connect to and interract with an IRC server of your
choosing. And for that purpose, it has several key features, such as
authentication and owner administration. Some features are for
:ref:`bot owners<feat-owner>`, some are for :ref:`end-users<feat-user>`, and
others are for :ref:`plugin authors<feat-plugin>`.


.. _feat-owner:

Sopel for bot owner
===================

.. _feat-owner-cli:

Command Lines
-------------

Sopel, as a software, runs in your terminal as a
:ref:`command line <run-cli-sopel>` aptly named ``sopel``, and it comes with
several other command lines to manage plugins and setup your bot:

* :ref:`run-cli-sopel-config` allows you to setup your bot and list all your
  configuration files
* :ref:`run-cli-sopel-plugins` can list your plugins, and allows you to enable
  or disable your installed plugins

You can read more about the command line tools in the :doc:`/run/cli`
documentation.

.. _feat-owner-conf:

Configuration
-------------

Sopel is highly configurable, from its :ref:`name, owner, and admins
<config-identity-admins>`, its :ref:`connection configuration
<config-irc-server>` (including options for SSL), to its list of :ref:`channels
<config-channels>`, :ref:`plugins <config-plugins>`, and several other
configurable features.

All this can be done in a configuration file written using the
:ref:`INI file format <config-ini>` as supported by Python's standar library.

Plus, Sopel comes with a configuration wizard that will help you initialize
your configuration file for the first time for a quick setup!

You can read more about the configuration in the :doc:`/run/configuration`
documentation.

.. _feat-owner-auth:

Authentication
--------------

Sopel provides two ways to authenticate: a simple method, and multi-stage
authentication. You can take advantage of network services and more advanced
authentication methods with servers that support it.

You can read more about both simple and multi-stage authentication in the
:ref:`dedicated configuration section <config-authentication>`.

.. _feat-owner-plugins:

Plugin management
-----------------

Sopel implements user interactions through a set of plugins, some are builtins,
others can be installed through PyPI, and all can be enabled or disabled by
configuration or by using the command line (see :ref:`run/cli:sopel-plugins`).

You can always ask on the official IRC Libera.chat channel ``#sopel`` where to
find plugins!

.. _feat-owner-service:

Run as a service
----------------

Running Sopel as a service on a server is fully documented for systemd: example
of Sopel configuration file, advice on where to put your files, and a template
for a systemd service unit ready for you to copy, edit, and run on your server.

You can read more about :doc:`/run/service` in the dedicated chapter.


.. _feat-user:

Sopel for end-user
==================

Sopel, through plugins, exposes a bunch of commands and can react to events
and messages, such as a key word used to trigger a funny reply.

One of the most important command is ``.help``, available through the
official `sopel-help`__ plugin.

Other :doc:`plugins</features/all-plugins>` are available out of the box such
as the :doc:`/features/plugins/dice` plugin to roll dice, or the
:doc:`/features/plugins/tell` plugin to leave a message to your friends when
they come back.

And if a plugin isn't available out of the box, bot owner can
:ref:`find new plugins<feat-owner-plugins>` to install from PYPI—the Sopel
developers have some in stock for you, :ref:`ask them on IRC<faq-contact-us>`!

.. __: https://pypi.org/project/sopel-help/


.. _feat-plugin:

Sopel for plugin author
=======================

Sopel doesn't do anything without plugins, but the project can't develop every
ideas into a builtin plugin: that's why there is a public API for developers
to make their own.

You can read the :doc:`/plugin` documentation, including:

* An introduction to :doc:`what is a plugin</plugin/what>` and its
  :doc:`anatomy</plugin/anatomy>`
* :doc:`Tutorials</plugin/tutorials>` to learn your first plugin
* A complete list of all the :doc:`decorators</plugin/decorators>` you can use
* And the complete :doc:`Sopel package API</package>`
