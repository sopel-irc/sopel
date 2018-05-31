Introduction |version| |build| |issues| |coverage-status| |license|
-------------------------------------------------------------------

Sopel is a simple, lightweight, open source, easy-to-use IRC Utility bot,
written in Python. It's designed to be easy to use, run and extend.

Installation
------------

Latest stable release
=====================
If you're on Arch, the easiest way to install is through your package
manager. The package is named ``sopel`` in [community] repository. On other
distros, and pretty much any operating system you can run Python on, you can
install `pip <https://pypi.python.org/pypi/pip/>`_, and do ``pip install
sopel``. Failing all that, you can download the latest tarball from
https://sopel.chat and follow the steps for installing from the latest
source below.

Latest source
=============
First, either clone the repository with ``git clone
git://github.com/sopel-irc/sopel.git`` or download a tarball from GitHub.

Note: sopel requires Python 2.7.x or Python 3.3+ to run. On Python 2.7,
sopel requires ``backports.ssl_match_hostname`` to be installed. Use
``pip install backports.ssl_match_hostname`` or ``yum install python-backports.ssl_match_hostname`` to install it,
or download and install it manually `from PyPi <https://pypi.python.org/pypi/backports.ssl_match_hostname>`.

In the source directory (whether cloned or from the tarball) run
``setup.py install``. You can then run ``sopel`` to configure and start the
bot. Alternately, you can just run the ``sopel.py`` file in the source
directory.

Adding modules
--------------
The easiest place to put new modules is in ``~/.sopel/modules``.

Some extra modules are available in the
`sopel-extras <https://github.com/sopel-irc/sopel-extras>`_ repository, but of
course you can also write new modules. A `tutorial <https://github.com/sopel-irc/sopel/wiki/Sopel-tutorial,-Part-2>`_
for creating new modules is available on the wiki.
API documentation can be found online at https://sopel.chat/docs, or
you can create a local version by running ``make html`` in the ``doc``
directory.

Further documentation
---------------------

In addition to the `official website <https://sopel.chat>`_, there is also a
`wiki <http://github.com/sopel-irc/sopel/wiki>`_ which includes valuable
information including a full listing of
`commands <https://github.com/sopel-irc/sopel/wiki/Commands>`_.

Questions?
----------

Join us in `#sopel <irc://irc.freenode.net/#sopel>`_ on Freenode.

.. |version| image:: https://img.shields.io/pypi/v/sopel.svg
   :target: https://pypi.python.org/pypi/sopel
.. |build| image:: https://travis-ci.org/sopel-irc/sopel.svg?branch=master
   :target: https://travis-ci.org/sopel-irc/sopel
.. |issues| image:: https://img.shields.io/github/issues/sopel-irc/sopel.svg
   :target: https://github.com/sopel-irc/issues
.. |coverage-status| image:: https://coveralls.io/repos/github/sopel-irc/sopel/badge.svg?branch=master
   :target: https://coveralls.io/github/sopel-irc/sopel?branch=master
.. |license| image:: https://img.shields.io/pypi/l/sopel.svg
   :target: https://github.com/sopel-irc/sopel/blob/master/COPYING
