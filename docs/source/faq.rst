==========================
Frequently Asked Questions
==========================

.. _faq-contact-us:

How to contact us?
==================

You can contact us by joining the development and community channel on IRC:

* connect to the `libera.chat`__ network
* and join the ``#sopel`` channel

We talk about the bot's development, and we answer questions from bot owners &
plugin authors as much as we can. We try to keep it as friendly as possible;
sometimes we also just chat about about non-development topics.

If you're coming to IRC with a question, you can often help us help you faster
by :ref:`having your logs ready <faq-logging>`.

All conversations are in English (except when someone swears in French).

.. __: https://libera.chat/guides/connect


.. _faq-bug-report:

How to report a bug?
====================

The best place to report a bug is to `open an issue on GitHub`__. We have
configured some templates to help and guide you through the process and
hopefully to make it easier for you.

Before submitting your bug, you can `search existing issues`__ to see if there
is one open already. If no existing issue covers your bug, please :ref:`have log
excerpts ready <faq-logging>` that demonstrate the problem, if possible.

Do not hesitate to :ref:`contact us <faq-contact-us>` if you are unsure about
your bug report.

.. __: https://github.com/sopel-irc/sopel/issues/new/choose
.. __: https://github.com/sopel-irc/sopel/issues


.. _faq-logging:

How to obtain logs?
===================

When requesting help, you'll probably be asked to provide logs illustrating the
problem. If you :ref:`report a bug <faq-bug-report>`, the form includes a field
for "Relevant logs" that you should fill in if possible.

By default you will find Sopel's logs in the ``~/.sopel/logs`` folder. If
:attr:`~.config.core_section.CoreSection.homedir` and/or
:attr:`~.config.core_section.CoreSection.logdir` is specified in Sopel's config
file, logs will be found in ``/path/to/homedir/logdir`` if ``logdir`` is a
relative path, or at ``/path/to/logdir`` if ``logdir`` is an absolute path. (If
Sopel is :doc:`being run as a service <run/service>`, the ``logdir`` should be
an absolute path.)

Log files' names start with :ref:`their associated config file's name
<logging-basename>`, i.e. the :option:`--config <sopel start --config>`
argument's value.

There are two main log types you might be asked to provide: ``sopel`` logs and
``raw`` logs.

Obtaining ``sopel`` logs
------------------------

``<configname>.sopel.log`` files contain everything Sopel does from startup to
shutdown.

In normal operation, the ``INFO`` (default) or ``WARNING``
:attr:`~.config.core_section.CoreSection.logging_level` is usually sufficient.
For ambiguous or particularly gnarly problems, you might be asked to enable
``DEBUG`` logging and reproduce your issue to help Sopel's developers understand
what's happening.

Obtaining ``raw`` logs
----------------------

For certain problem types, a developer might ask for ``raw`` logs to examine
exactly what Sopel and the IRC server are saying to each other.

These ``<configname>.raw.log`` files are not enabled by default. If requested
by the person helping you in our issue tracker or IRC channel, you can turn
``raw`` logs on using the :attr:`~.config.core_section.CoreSection.log_raw`
setting in your config file.

.. warning::

    The ``raw`` log may contain sensitive information, e.g. your bot's NickServ
    account credentials, its IP address, or channel keys.

    Always check the portion of your ``raw`` log that you are sharing for
    secrets, and censor any you find!

.. seealso::

    More information about configuring Sopel's logging is available in the
    :ref:`Logging` section.
