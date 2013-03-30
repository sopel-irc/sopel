#Introduction

Willie is a simple, lightweight, open source, easy-to-use IRC Utility bot,
written in Python. It's designed to be easy to use, run and extend.

#Installation

The easiest way is to simply run ``setup.py install``. Willie can also be run
by copying ``scripts/willie`` to ``willie.py`` in the root of the source
directory (i.e, the one with the ``scripts`` folder in it), and running that.
You can also install the latest stable release of Willie through the Python
Package Index by installing ``pip``, and then running ``pip install willie``.
Willie is also available in the package repositories for Fedora 17 and 18.

#Adding modules

The easiest place to put new modules is in ``~/.willie/modules``. You will need
to add a a line to the ``[core]`` section of your config file saying
``extra = /home/yourname/.willie/modules``.

Some extra modules are available in the
[willie-extras](https://github.com/embolalia/willie-extras) repository, but of
course you can also write new modules. A tutorial for creating new modules is
available on the
[wiki](https://github.com/embolalia/willie/wiki/How-To-Create-a-Willie-Module).
API documentation can be found online at [http://willie.dftba.net/docs](), or
you can create a local version by running ``make html`` in the ``doc``
directory.

#Further documentation

In addition to the [official website](http://willie.dftba.net), there is also a
[wiki](http://github.com/embolalia/willie/wiki) which includes valuable
infomration including a full listing of
[commands](https://github.com/embolalia/willie/wiki/Commands).

#Questions?

Contact us on irc.dftba.net channel #tech

For a list of contributions to the Jenni fork see the file ``CREDITS``.
