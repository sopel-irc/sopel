=======
 Sopel
=======

|version| |build| |issues| |alerts| |coverage-status| |license|

Introduction
------------

Sopel is a simple, lightweight, open source, easy-to-use IRC Utility bot,
written in Python. It's designed to be easy to use, run and extend.

Installation
------------

Latest stable release
=====================
On most systems where you can run Python, the best way to install Sopel is to
install `pip <https://pypi.org/project/pip/>`_ and then ``pip install sopel``.

Arch users can install the ``sopel`` package from the [community] repository,
though new versions might take slightly longer to become available.

Failing both of those options, you can grab the latest tarball `from GitHub
<https://github.com/sopel-irc/sopel/releases/latest>`_  and follow the steps
for installing from the latest source below.

Latest source
=============
First, either clone the repository with ``git clone
git://github.com/sopel-irc/sopel.git`` or download a tarball `from GitHub
<https://github.com/sopel-irc/sopel/releases/latest>`_.

Note: Sopel requires Python 2.7.x or Python 3.3+ to run. On Python 2.7,
Sopel requires ``backports.ssl_match_hostname`` to be installed. Use
``pip install backports.ssl_match_hostname`` or
``yum install python-backports.ssl_match_hostname`` to install it, or download
and install it manually `from PyPI <https://pypi.org/project/backports.ssl_match_hostname>`_.

Note: Python 2.x is near end of life. Sopel will drop support in version 8.0.

In the source directory (whether cloned or from the tarball) run ``pip install
-e .``. You can then run ``sopel`` to configure and start the bot.

Database support
----------------
Sopel leverages SQLAlchemy to support the following database types: SQLite,
MySQL, PostgreSQL, MSSQL, Oracle, Firebird, and Sybase. By default Sopel will
use a SQLite database in the current configuration directory, but alternative
databases can be configured with the following config options: ``db_type``,
``db_filename`` (SQLite only), ``db_driver``, ``db_user``, ``db_pass``,
``db_host``, ``db_port``, and ``db_name``. You will need to manually install
any packages (system or ``pip``) needed to make your chosen database work.

**Note:** Plugins not updated since Sopel 7.0 was released *might* have
problems with database types other than SQLite (but many will work just fine).

Adding plugins
--------------
The easiest place to put new plugins is in ``~/.sopel/plugins``. Some newer
plugins are installable as packages; `search PyPI
<https://pypi.org/search/?q=%22sopel%22>`_ for these. Many more plugins
written by other users can be found using your favorite search engine.

Some older, unmaintained plugins are available in the
`sopel-extras <https://github.com/sopel-irc/sopel-extras>`_ repository, but of
course you can also write your own. A `tutorial <https://sopel.chat/tutorials/part-1-writing-plugins/>`_
for creating new plugins is available on Sopel's website.
API documentation can be found online at https://sopel.chat/docs/, or
you can create a local version by running ``make docs``.

Further documentation
---------------------

The `official website <https://sopel.chat/>`_ includes such valuable information
as a full listing of built-in `commands <https://sopel.chat/usage/commands/>`_,
`tutorials <https://sopel.chat/tutorials/>`_, `API documentation <https://sopel.chat/docs/>`_,
and other `usage information <https://sopel.chat/usage/>`_.

Questions?
----------

Join us in `#sopel <irc://irc.freenode.net/#sopel>`_ on Freenode.

Financial support
-----------------

We're thrilled that you want to support the project!

We have applied for access to organization-level sponsorship from GitHub. In
the interim, if you wish to contribute sooner, you are welcome to do so
through `Open Collective <https://opencollective.com/sopel>`_ or sponsor
Sopel's maintainer, `dgw <https://github.com/sponsors/dgw>`_, individually.

Any donations received will be used to cover infrastructure costs, such as our
domain name and hosting services. Our main project site is easily hosted by
`Netlify <https://www.netlify.com/>`_, but we are considering building a few
new features that would require more than static hosting. All project-related
`expenses <https://opencollective.com/sopel/expenses>`_ are tracked on our
Open Collective profile, for transparency.

.. |version| image:: https://img.shields.io/pypi/v/sopel.svg
   :target: https://pypi.python.org/pypi/sopel
.. |build| image:: https://travis-ci.org/sopel-irc/sopel.svg?branch=master
   :target: https://travis-ci.org/sopel-irc/sopel
.. |issues| image:: https://img.shields.io/github/issues/sopel-irc/sopel.svg
   :target: https://github.com/sopel-irc/sopel/issues
.. |alerts| image:: https://img.shields.io/lgtm/alerts/g/sopel-irc/sopel.svg
   :target: https://lgtm.com/projects/g/sopel-irc/sopel/alerts/
.. |coverage-status| image:: https://coveralls.io/repos/github/sopel-irc/sopel/badge.svg?branch=master
   :target: https://coveralls.io/github/sopel-irc/sopel?branch=master
.. |license| image:: https://img.shields.io/pypi/l/sopel.svg
   :target: https://github.com/sopel-irc/sopel/blob/master/COPYING
