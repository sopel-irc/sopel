===========================
Plugins: Developer Overview
===========================

.. toctree::
   :titlesonly:

   plugin/what
   plugin/anatomy
   plugin/bot
   plugin/decorators
   plugin/advanced
   plugin/internals

Plugin glossary
===============

.. glossary::
   :sorted:

   Sopel plugin
      A Sopel plugin is a plugin made for Sopel. It contains
      :term:`rules <Rule>`, it has a setup/shutdown cycle, and it can extend
      the bot's configuration with its own
      :class:`section <sopel.config.types.StaticSection>`.

      It is of one of the possible plugin types, preferably
      a :term:`Single file plugin`, or an :term:`Entry point plugin`. The other
      two types are :term:`Folder plugin` and :term:`Namespace package plugin`.

   Rule
      A rule defines how to match a specific message from the IRC server,
      usually with a regular expression. It also defines how to react to these
      messages. For that it can execute a :term:`callable <Plugin callable>`.

   Rule system
      The rule system is how Sopel manages and handles :term:`rules <Rule>`.

   Generic rule
      A generic rule matches any message using a regular expression. It doesn't
      use any specific format, unlike a :term:`Named rule`. It can match the
      whole message (:term:`Match rule`), or any part of it
      (:term:`Search rule`), or it may trigger for every match in the message
      (:term:`Find rule`).

   Match rule
      A match rule is a :term:`Generic rule` that triggers when the regex
      matches the whole message.

   Search rule
      A search rule is a :term:`Generic rule` that triggers when the regex
      matches any part of the message.

   Find rule
      A find rule is a :term:`Generic rule` that triggers for every time the
      regex matches a part of the message.

   Named rule
      A named rule is a rule that uses a regular expression with a specific
      format: with a name, and usually with a prefix, or a set of specific
      conditions. See :term:`Command`, :term:`Action command`, and
      :term:`Nick command`. A named rule always matches the message from its
      start, and it accepts any number of arguments::

         [nick] <prefix><name> [<arg1> <arg2> <...> <argN>]

      A named rule can have aliases, i.e. alternative names used to trigger
      the rule.

   Command
      A command is a :term:`Named rule` that reacts to a :term:`Command prefix`
      and a name.

   Command prefix
      The command prefix is a regular expression joined to a :term:`Command`'s
      name as its prefix. It is defined by configuration using
      :attr:`core.prefix <sopel.config.core_section.CoreSection.prefix>`.

   Action command
      An action command is a :term:`Named rule` that reacts to a name in a
      message sent with the ``ACTION`` CTCP command.

   Nick command
      A nick command (or nickname command) is a :term:`Named rule` that reacts
      to a name prefixed by the bot's nickname in a message.

   URL callback
      A URL callback is a rule that triggers for every URL in a message.

   Rate limiting
      How often a :term:`rule <Rule>` can be triggered on a per-user basis, in
      a channel, or across the IRC network.

   Plugin callable
      A plugin callable is a Python callable, that handles a specific message
      from the IRC server matching a :term:`Rule`. See also the
      :ref:`Plugin Anatomy: callables <plugin-anatomy-callables>` section for
      the plugin callable signature.

   Plugin job
      A plugin job is a Python callable, that executes periodically on a
      schedule. See also the :ref:`Plugin Anatomy: jobs <plugin-anatomy-jobs>`
      section for the plugin job signature.

   Single file plugin
      A :term:`Sopel plugin` composed of a single Python file. Can be loaded by
      Sopel even when it's not available from ``sys.path``.

   Folder plugin
      A plugin composed of a directory that contains a ``__init__.py`` file.
      It is not considered as a proper Python package unless its parent
      directory is in ``sys.path``. As they can create problems, they are not
      recommended, and either :term:`Single file plugin` or
      :term:`Entry point plugin` should be used instead.

   Namespace package plugin
      A plugin that is a Python namespace package, i.e. a package within a
      specific namespace (``sopel_modules.<name>``, where ``sopel_modules`` is
      the namespace, and ``<name>`` is the plugin's name). This is the old way
      to distribute plugins and is not recommended; :term:`Entry point plugin`
      should be used instead.

   Entry point plugin
      A plugin that is an installed Python package and exposed through the
      ``sopel.plugins`` setuptools entry point.

   Sopelunking
      Action performed by a :term:`Sopelunker`.

   Sopelunker
      A person who does :term:`Sopelunking`.
