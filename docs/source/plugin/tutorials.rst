=========
Tutorials
=========

The key feature of Sopel is its plugin system: *everything* Sopel does is
through a plugin. Combining some basic Python knowledge with reading Sopel's
documentation, you can write a plugin too!

These tutorials will guide and help you to begin your journey as a plugin
author, i.e. someone who can write plugins for Sopel. Not every plugin is
easy however, and you will probably need to hone your Python skills, learn more
about the IRC protocol, and learn more about software programming in general.
But let's not get ahead of ourselves; you are here for the basics.

.. toctree::
    :titlesonly:

    tutorials/first-plugin
    tutorials/playing-with-commands
    tutorials/configuration-and-setup


Requirements
============

Before you can dive into these tutorials, you will need the following:

* to install and run Sopel on your development environment
* to have write access to Sopel's configuration and plugin directory
* a beginner level in Python (e.g. how to write a function, what is a variable,
  how to perform string formatting, how to access an object's attributes, how
  to import a module, etc.)

Since you'll be running Sopel, we invite you to create a configuration file
that connects to a friendly IRC server and joins a private testing channel.
That way, when you restart your bot or run your command for the hundredth
time, you won't spam other users.
