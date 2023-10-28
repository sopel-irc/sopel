=============
Install Guide
=============

.. highlight:: shell

Installation Requirements
=========================

To install Sopel, you will need:

* Python 3.8 or above
* Pip, the official Python package installer

.. important::

    Before installing Sopel, you should know which version of Python, and which
    Python interpreter you are using for that. For instance, it can be named
    ``python3`` or just ``python`` depending on your system and setup. In this
    guide we will refer to the Python interpreter you want to use as
    ``python3``.

Official Release
================

The official release of Sopel is `available at PyPI`__. The
recommended way to install Sopel from pypi.org is to perform the following
command::

    python3 -m pip install sopel

This will ensure that Sopel is installed for the Python interpreter you want to
use. You do not need to have root access to install Sopel. To check that Sopel
is indeed installed, you can run the following line::

    python3 -c "import sopel; print(sopel.__version__)"

This will show the installed version of Sopel for this interpreter.

When a new version of Sopel is released, you can update your install by reusing
the same command with the ``-U`` option (short for ``--upgrade``)::

    python3 -m pip install -U sopel

You must restart Sopel for the update to take effect.

.. __: https://pypi.org/project/sopel/

Installing from Source
======================

For development purposes or to test a future release, you may want to install
Sopel directly from its `source repository`__ on GitHub. To install from
source, first select the version you want to install, and refer to the
``README.rst`` file for instructions.

We strongly recommend to use a virtualenv or other isolation mechanism so as to
prevent any conflicts with your system's Python interpreter and libraries.

.. warning::

    Although possible, source installations are not supported. If you install
    from sources, you may encounter unexpected bugs and unstable behaviors, and
    we fully expect you to either find a solution by yourself, revert to a
    previous version, or wait for a fix without an ETA.

    However, we do appreciate :ref:`bug reports<faq-bug-report>` (with logs and
    configuration details) and feedback. In that case,
    :ref:`reaching out to us on IRC<faq-contact-us>` is the best approach.

.. __: https://github.com/sopel-irc/sopel


First run
=========

Once Sopel is installed, you should have access to a ``sopel`` command, as well
as :doc:`other commands <cli>`.

.. note::

    By default, ``pip`` will install the command in ``~/.local/bin/``, which
    might not be on your ``PATH``. You will need to add this folder to your
    ``PATH`` for your shell to see the command.

    For example, you could add this to your ``~/.profile`` file (works on
    Ubuntu 22.04)::

        # set PATH so it includes user's private bin if it exists
        if [ -d "$HOME/.local/bin" ] ; then
            PATH="$HOME/.local/bin:$PATH"
        fi

    Refer to your operating system's documentation for more information on how
    to configure your ``PATH``.

Initial Configuration
---------------------

To run the bot, you need a :doc:`configuration file <configuration>`, which you
can create with the following command::

    sopel configure

This will run a wizard that helps you create a configuration file. It will
ask you questions to fill in the details. When you see something in ``[square
brackets]``, that's the default setting, and you can just hit :kbd:`Enter` to keep
it. We recommend selecting a custom nick for your bot during configuration.

This wizard doesn't cover every option, only the ones which are needed to get
the bot running. The :doc:`core config settings <configuration>` are all
documented if you want to make other tweaks.

Finally, the wizard will ask you about configuration settings for plugins. This
will automatically detect what plugins you have available, and run their
configuration utility if they have one.

Once you are done, you can always re-run the same command and accept the values
you already set and change only what you need.

Start the Bot
-------------

Once you have properly configured your bot, you are now ready to start it for
the first time. The command to do so is the following::

    sopel start

.. note::

    Some IRC networks require nick registration or special configuration
    for connecting. Refer to your IRC network for more information about
    what steps may be necessary to run your bot there.

Sopel will output log information informing you of its startup progress, such
as loading plugins, connecting to the network, and joining channels.

To stop the bot, simply exit the process (e.g. with :kbd:`Control+c`) and
Sopel will ``QUIT`` IRC, perform its shutdown tasks, and gracefully exit.
