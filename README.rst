Introduction |build-status| |coverage-status|
---------------------------------------------

Willie is a simple, lightweight, open source, easy-to-use IRC Utility bot,
written in Python. It's designed to be easy to use, run and extend.

Installation
------------

Latest stable release
=====================
If you're on Fedora or Arch, the easiest way to install is through your package
manager. The package is named ``willie`` in both Fedora and the AUR. On other
distros, and pretty much any operating system you can run Python on, you can
install `pip <https://pypi.python.org/pypi/pip/>`_, and do ``pip install
willie``. Failing all that, you can download the latest tarball from
http://willie.dftba.net and follow the steps for installing from the latest
source below.

Latest source
=============
First, either clone the repository with ``git clone
git://github.com/embolalia/willie.git`` or download a tarball from GitHub.

Note: willie requires Python 2.7 or Python 3.3 to run. On Python 2.7,
willie requires ``backports.ssl_match_hostname`` to be installed. Use
``pip install backports.ssl_match_hostname`` or ``yum install python-backports.ssl_match_hostname`` to install it,
or download and install it manually `from PyPi <https://pypi.python.org/pypi/backports.ssl_match_hostname>`.

In the source directory (whether cloned or from the tarball) run
``setup.py install``. You can then run ``willie`` to configure and start the
bot. Alternately, you can just run the ``willie.py`` file in the source
directory.

Adding modules
--------------
The easiest place to put new modules is in ``~/.willie/modules``. You will need
to add a a line to the ``[core]`` section of your config file saying
``extra = /home/yourname/.willie/modules``.

Some extra modules are available in the
`willie-extras <https://github.com/embolalia/willie-extras>`_ repository, but of
course you can also write new modules. A `tutorial <https://github.com/embolalia/willie/wiki/How-To-Create-a-Willie-Module>`_
for creating new modules is available on the wiki.
API documentation can be found online at http://willie.dftba.net/docs, or
you can create a local version by running ``make html`` in the ``doc``
directory.

Further documentation
---------------------

In addition to the `official website <http://willie.dftba.net>`_, there is also a
`wiki <http://github.com/embolalia/willie/wiki>`_ which includes valuable
information including a full listing of
`commands <https://github.com/embolalia/willie/wiki/Commands>`_.

Questions?
----------

Contact us on irc.dftba.net channel #tech

For a list of contributions to the Jenni fork see the file ``CREDITS``.

.. |build-status| image:: https://travis-ci.org/embolalia/willie.png
   :target: https://travis-ci.org/embolalia/willie
.. |coverage-status| image:: https://coveralls.io/repos/embolalia/willie/badge.png
   :target: https://coveralls.io/r/embolalia/willie
