"""Sopel's configuration module.

The :class:`~sopel.config.Config` object provides an interface to access Sopel's
configuration file. It exposes the configuration's sections through its
attributes as objects, which in turn expose their directives through *their*
attributes.

For example, this is how to access ``core.nick`` on a :class:`Config` object::

    >>> from sopel import config
    >>> settings = config.Config('/sopel/config.cfg')
    >>> settings.core.nick
    'Sopel'

The configuration file being:

.. code-block:: ini

    [core]
    nick = Sopel
    host = irc.libera.chat
    use_ssl = true
    port = 6697
    owner = dgw
    channels =
        "#sopel"

A section can be represented by a subclass of
:class:`~sopel.config.types.StaticSection`; for example a ``[spam]`` section
with ``eggs`` and ``bacon`` can be defined like this::

    from sopel import config

    class SpamSection(config.types.StaticSection):
        eggs = config.types.ListAttribute('eggs')
        bacon = config.types.ValidatedAttribute('bacon')

The ``[core]`` section itself is represented by the
:class:`~sopel.config.core_section.CoreSection` class, which is a subclass of
:class:`~sopel.config.types.StaticSection`. It is automatically added when
the :class:`Config` object is instantiated; it uses
:meth:`Config.define_section` for that purpose.

.. versionadded:: 6.0.0
"""
# Copyright 2012-2015, Elsie Powell, embolalia.com
# Copyright © 2012, Elad Alfassa <elad@fedoraproject.org>
# Licensed under the Eiffel Forum License 2.

from __future__ import annotations

import configparser
import os

from . import core_section, types


__all__ = [
    'core_section',
    'types',
    'DEFAULT_HOMEDIR',
    'ConfigurationError',
    'ConfigurationNotFound',
    'Config',
]

DEFAULT_HOMEDIR = os.path.join(os.path.expanduser('~'), '.sopel')


class ConfigurationError(Exception):
    """Exception type for configuration errors.

    :param str value: a description of the error that has occurred
    """
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return 'ConfigurationError: %s' % self.value


class ConfigurationNotFound(ConfigurationError):
    """Exception type for use when the configuration file cannot be found.

    :param str filename: file path that could not be found
    """
    def __init__(self, filename):
        super().__init__(None)
        self.filename = filename
        """Path to the configuration file that could not be found."""

    def __str__(self):
        return 'Unable to find the configuration file %s' % self.filename


class Config:
    """The bot's configuration.

    :param str filename: the configuration file to load and use to populate this
                         ``Config`` instance
    :param bool validate: if ``True``, validate values in the ``[core]`` section
                          when it is loaded (optional; ``True`` by default)

    The configuration object will load sections (see :class:`ConfigSection`)
    from the file at ``filename`` during initialization. Calling :meth:`save`
    writes any runtime changes to the loaded settings back to the same file.

    Only the ``[core]`` section (see :class:`~.core_section.CoreSection`) is
    added and made available by default; it is the only section required for
    Sopel to run. All other sections must be defined later, by the code that
    needs them, using :meth:`define_section`.
    """
    def __init__(self, filename, validate=True):
        self.filename = filename
        """The config object's associated file."""
        basename, _ = os.path.splitext(os.path.basename(filename))
        self.basename = basename
        """The config's base filename, i.e. the filename without the extension.

        If the filename is ``libera.config.cfg``, then the ``basename`` will
        be ``libera.config``.

        The config's ``basename`` is useful as a component :ref:`of log file
        names <logging-basename>`, for example.
        """
        self.parser = configparser.RawConfigParser(allow_no_value=True)
        """The configuration parser object that does the heavy lifting.

        .. seealso::

            Python's built-in :mod:`configparser` module and its
            :class:`~configparser.RawConfigParser` class.

        """
        self.parser.read(self.filename)
        self.define_section('core', core_section.CoreSection,
                            validate=validate)
        self.get = self.parser.get
        """Shortcut to :meth:`parser.get <configparser.ConfigParser.get>`."""

    @property
    def homedir(self):
        """The config file's home directory.

        If the :attr:`core.homedir <.core_section.CoreSection.homedir>` setting
        is available, that value is used. Otherwise, the default ``homedir`` is
        the directory portion of the :class:`Config`'s :attr:`filename`.
        """
        configured = None
        if self.parser.has_option('core', 'homedir'):
            configured = self.parser.get('core', 'homedir')
        if configured:
            return configured
        else:
            return os.path.dirname(self.filename)

    def get_defined_sections(self):
        """Retrieve all defined static sections of this configuration.

        :return: all instances of :class:`~sopel.config.types.StaticSection`
                 defined for this configuration file
        :rtype: list

        When a plugin defines a section (using :meth:`define_section`), it
        associates a :class:`~sopel.config.types.StaticSection` for the section.
        This method allows to retrieve these instances of ``StaticSection``,
        and only these.

        .. versionadded:: 7.1
        """
        sections = (
            (name, getattr(self, name))
            for name in self.parser.sections()
        )
        return [
            (name, section)
            for name, section in sections
            if isinstance(section, types.StaticSection)
        ]

    def save(self):
        """Write all changes to the config file.

        .. note::

            Saving the config file will remove any comments that might have
            existed, as Python's :mod:`configparser` ignores them when parsing.

            This will become less and less important as we continue to improve
            Sopel's tools for making automated changes to config files and
            eliminate most users' need to ever manually edit the text, but it's
            still worth keeping in mind.

        """
        with open(self.filename, 'w') as cfgfile:
            self.parser.write(cfgfile)
            cfgfile.flush()

    def add_section(self, name):
        """Add a new, empty section to the config file.

        :param str name: name of the new section
        :return: ``None`` if successful; ``False`` if a section named ``name``
                 already exists

        .. note::

            Plugin authors very rarely want or need to use this method.

            You will almost always want to define (and optionally validate
            values within) a section with specific attributes using
            :meth:`define_section` and a child class of
            :class:`~.types.StaticSection`.

        .. important::

            The section's ``name`` SHOULD follow *snake_case* naming rules:

            * use only lowercase letters, digits, and underscore (``_``)
            * SHOULD NOT start with a digit

            Deviations from *snake_case* can break the following operations:

            * :ref:`accessing the section <sopel.config>` from Python code
              using the :class:`~.Config` object's attributes
            * :ref:`overriding the section's values <Overriding individual
              settings>` using environment variables

        """
        try:
            return self.parser.add_section(name)
        except configparser.DuplicateSectionError:
            return False

    def define_section(self, name, cls_, validate=True):
        """Define the available settings in a section.

        :param str name: name of the new section
        :param cls\\_: :term:`class` defining the settings within the section
        :type cls\\_: subclass of :class:`~.types.StaticSection`
        :param bool validate: whether to validate the section's values
                              (optional; defaults to ``True``)
        :raise ValueError: if the section ``name`` has been defined already with
                           a different ``cls_``

        When a plugin needs to add a section to the config file, either in
        their ``configure(settings)`` hook or in their ``setup(bot)`` hook,
        they must use this method::

            def setup(bot):
                bot.settings.define_section(MyPluginSection, 'myplugin')

        If ``validate`` is ``True``, the section's values will be validated,
        and an exception (usually :class:`ValueError` or
        :class:`AttributeError`) raised if they are invalid. This is desirable
        in a plugin's :func:`setup` function, for example, but might not be in
        the :func:`configure` function.

        .. important::

            The section's ``name`` SHOULD follow *snake_case* naming rules:

            * use only lowercase letters, digits, and underscore (``_``)
            * SHOULD NOT start with a digit

            Deviations from *snake_case* can break the following operations:

            * :ref:`accessing the section <sopel.config>` from Python code
              using the :class:`~.Config` object's attributes
            * :ref:`overriding the section's values <Overriding individual
              settings>` using environment variables

        .. seealso::

            The definition of a :class:`~.types.StaticSection`.

        """
        if not issubclass(cls_, types.StaticSection):
            raise ValueError("Class must be a subclass of StaticSection.")
        current = getattr(self, name, None)
        current_name = str(current.__class__)
        new_name = str(cls_)
        if (current is not None and not isinstance(current, self.ConfigSection) and
                not current_name == new_name):
            raise ValueError(
                "Can not re-define class for section from {} to {}.".format(
                    current_name, new_name)
            )
        setattr(self, name, cls_(self, name, validate=validate))

    class ConfigSection:
        """Represents a section of the config file.

        :param str name: name of this section
        :param items: key-value pairs
        :type items: :term:`iterable` of two-item :class:`tuple`\\s
        :param parent: this section's containing object
        :type parent: :class:`Config`

        Contains all keys in the section as attributes.
        """
        def __init__(self, name, items, parent):
            object.__setattr__(self, '_name', name)
            object.__setattr__(self, '_parent', parent)
            for item in items:
                value = item[1].strip()
                if not value.lower() == 'none':
                    if value.lower() == 'false':
                        value = False
                    object.__setattr__(self, item[0], value)

        def __getattr__(self, name):
            return None

        def __contains__(self, name):
            return name in vars(self)

        def __setattr__(self, name, value):
            object.__setattr__(self, name, value)
            if type(value) is list:
                value = ','.join(value)
            self._parent.parser.set(self._name, name, value)

    def __getattr__(self, name):
        if name in self.parser.sections():
            items = self.parser.items(name)
            section = self.ConfigSection(name, items, self)  # Return a section
            setattr(self, name, section)
            return section
        else:
            raise AttributeError("%r object has no attribute %r"
                                 % (type(self).__name__, name))

    def __getitem__(self, name):
        return self.__getattr__(name)

    def __contains__(self, name):
        return name in self.parser.sections()

    def option(self, question, default=False):
        """Ask the user a "y/n" question.

        :param str question: the question to ask the user
        :param bool default: ``True`` to show ``[y]`` as the default choice;
                             ``False`` to show ``[n]`` (optional; defaults to
                             ``False``)
        :return: the Boolean value corresponding to the user's choice
        :rtype: bool

        This will show a "y/n" prompt in the user's terminal, and return
        ``True`` or ``False`` based on the response. ``question`` should be
        phrased as a question, but without a question mark at the end.
        """
        d = 'n'
        if default:
            d = 'y'
        ans = input(question + ' (y/n)? [' + d + '] ')
        if not ans:
            ans = d
        return ans.lower() == 'y'
