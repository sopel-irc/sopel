.. py:module:: sopel.config.core_section

================================
The [core] configuration section
================================

A typical configuration file looks like this::

    [core]
    nick = Sopel
    host = irc.freenode.org
    use_ssl = false
    port = 6667
    owner = dgw
    channels = #sopel

which tells the bot what is its name and its owner, and which server to
connect to and which channels to join.

Everything else is pretty much optional

The :class:`sopel.config.core_section.CoreSection` represents the ``[core]``
section of the configuration file. See each of its attributes for its full
description.

This file can be generated from a :doc:`console wizard<cli>` using
``sopel configure``.

.. contents::
    :local:


Identity & Admins
=================

For the bot:

* :attr:`~CoreSection.nick`
* :attr:`~CoreSection.name`
* :attr:`~CoreSection.user`

For its owners and admins:

* :attr:`~CoreSection.owner`
* :attr:`~CoreSection.owner_account`
* :attr:`~CoreSection.admins`
* :attr:`~CoreSection.admin_accounts`


IRC Server
==========

These directives are used to configure how the bot connect to an IRC server.

For the socket configuration:

* :attr:`~CoreSection.host`
* :attr:`~CoreSection.port`
* :attr:`~CoreSection.bind_host`

For SSL connection:

* :attr:`~CoreSection.use_ssl`
* :attr:`~CoreSection.verify_ssl`
* :attr:`~CoreSection.ca_certs`

For IRC connection:

* :attr:`~CoreSection.channels`
* :attr:`~CoreSection.throttle_join`
* :attr:`~CoreSection.timeout`
* :attr:`~CoreSection.modes`


Authentification
================

To authenticate the bot to the IRC server, the :attr:`~CoreSection.auth_method`
option must be defined, then these options will be used accordingly:

* :attr:`~CoreSection.auth_username`
* :attr:`~CoreSection.auth_password`
* :attr:`~CoreSection.auth_target`


Database
========

* :attr:`~CoreSection.db_type`
* :attr:`~CoreSection.db_driver`
* :attr:`~CoreSection.db_filename`
* :attr:`~CoreSection.db_host`
* :attr:`~CoreSection.db_port`
* :attr:`~CoreSection.db_name`
* :attr:`~CoreSection.db_user`
* :attr:`~CoreSection.db_pass`


Commands & Plugins
==================

To configure commands & triggers options:

* :attr:`~CoreSection.prefix`
* :attr:`~CoreSection.help_prefix`
* :attr:`~CoreSection.alias_nicks`
* :attr:`~CoreSection.auto_url_schemes`

To configure loaded plugins:

* :attr:`~CoreSection.enable`
* :attr:`~CoreSection.exclude`
* :attr:`~CoreSection.extra`

To ignore hosts & nicks:

* :attr:`~CoreSection.host_blocks`
* :attr:`~CoreSection.nick_blocks`

Logging
=======

* :attr:`~CoreSection.logdir`
* :attr:`~CoreSection.logging_level`
* :attr:`~CoreSection.log_raw`
* :attr:`~CoreSection.logging_channel`


Misc
====

* :attr:`~CoreSection.homedir`
* :attr:`~CoreSection.default_time_format`
* :attr:`~CoreSection.default_timezone`
* :attr:`~CoreSection.not_configured`
* :attr:`~CoreSection.reply_errors`
* :attr:`~CoreSection.pid_dir`
