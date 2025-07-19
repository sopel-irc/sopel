"""Types for creating section definitions.

A section definition consists of a subclass of :class:`StaticSection`, on which
any number of subclasses of :class:`BaseValidated` (a few common ones of which
are available in this module) are assigned as attributes. These descriptors
define how to read values from, and write values to, the config file.

As an example, if one wanted to define the ``[spam]`` section as having an
``eggs`` option, which contains a list of values, they could do this:

    >>> class SpamSection(StaticSection):
    ...     eggs = ListAttribute('eggs')
    ...
    >>> SpamSection(config, 'spam')
    >>> print(config.spam.eggs)
    []
    >>> config.spam.eggs = ['goose', 'turkey', 'duck', 'chicken', 'quail']
    >>> print(config.spam.eggs)
    ['goose', 'turkey', 'duck', 'chicken', 'quail']
    >>> config.spam.eggs = 'herring'
    Traceback (most recent call last):
        ...
    ValueError: ListAttribute value must be a list.
"""

from __future__ import annotations

import abc
import getpass
import logging
import os.path
import re

from sopel.lifecycle import deprecated


LOGGER = logging.getLogger(__name__)


class NO_DEFAULT:
    """A special value to indicate that there should be no default."""


class StaticSection:
    """A configuration section with parsed and validated settings.

    This class is intended to be subclassed and customized with added
    attributes containing :class:`BaseValidated`-based objects.

    .. note::

        By convention, subclasses of ``StaticSection`` are named with the
        plugin's name in CamelCase, plus the suffix ``Section``. For example, a
        plugin named ``editor`` might name its subclass ``EditorSection``; a
        ``do_stuff`` plugin might name its subclass ``DoStuffSection`` (its
        name converted from ``snake_case`` to ``CamelCase``).

        However, this is *only* a convention. Any class name that is legal in
        Python will work just fine.

    """
    def __init__(self, config, section_name, validate=True):
        if not config.parser.has_section(section_name):
            config.parser.add_section(section_name)
        self._parent = config
        self._parser = config.parser
        self._section_name = section_name

        for value in dir(self):
            if value in ('_parent', '_parser', '_section_name'):
                # ignore internal attributes
                continue

            try:
                getattr(self, value)
            except ValueError as e:
                raise ValueError(
                    'Invalid value for {}.{}: {}'.format(
                        section_name, value, str(e)))
            except AttributeError:
                if validate:
                    raise ValueError(
                        'Missing required value for {}.{}'.format(
                            section_name, value))

    def configure_setting(self, name, prompt, default=NO_DEFAULT):
        """Return a validated value for this attribute from the terminal.

        :param str name: the name of the attribute to configure
        :param str prompt: the prompt text to display in the terminal
        :param default: the value to be used if the user does not enter one
        :type default: depends on subclass

        If ``default`` is passed, it will be used if no value is given by the
        user. If it is not passed, the current value of the setting, or the
        default value if it's unset, will be used. Note that if ``default`` is
        passed, the current value of the setting will be ignored, even if it is
        not the attribute's default.
        """
        attribute = getattr(self.__class__, name)
        if default is NO_DEFAULT and not attribute.is_secret:
            try:
                # get current value of this setting to use as prompt default
                default = getattr(self, name)
            except AttributeError:
                # there is no current value; that's OK
                pass
            except ValueError:
                print('The configured value for this option was invalid.')
                if attribute.default is not NO_DEFAULT:
                    default = attribute.default
        while True:
            try:
                value = attribute.configure(
                    prompt, default, self._parent, self._section_name)
            except ValueError as exc:
                print(exc)
            else:
                break
        setattr(self, name, value)


class BaseValidated(abc.ABC):
    """The base type for a setting descriptor in a :class:`StaticSection`.

    :param str name: the attribute name to use in the config file
    :param default: the value to be returned if the setting has no value
                    (optional; defaults to :obj:`None`)
    :type default: mixed
    :param bool is_secret: tell if the attribute is secret/a password
                           (optional; defaults to ``False``)

    ``default`` also can be set to :const:`sopel.config.types.NO_DEFAULT`, if
    the value *must* be configured by the user (i.e. there is no suitable
    default value). Trying to read an empty ``NO_DEFAULT`` value will raise
    :class:`AttributeError`.

    .. important::

        Setting names SHOULD follow *snake_case* naming rules:

        * use only lowercase letters, digits, and underscore (``_``)
        * SHOULD NOT start with a digit

        Deviations from *snake_case* can break the following operations:

        * :ref:`accessing the setting <sopel.config>` from Python code using
          the :class:`~.Config` object's attributes
        * :ref:`overriding the setting's value <Overriding individual
          settings>` using environment variables

    """
    def __init__(self, name, default=None, is_secret=False):
        self.name = name
        """Name of the attribute."""
        self.default = default
        """Default value for this attribute.

        If not specified, the attribute's default value will be ``None``.
        """
        self.is_secret = bool(is_secret)
        """Tell if the attribute is secret/a password.

        The default value is ``False`` (not secret).

        Sopel's configuration can contain passwords, secret keys, and other
        private information that must be treated as sensitive data. Such
        options should be marked as "secret" with this attribute.
        """

    def configure(self, prompt, default, parent, section_name):
        """Parse and return a value from user's input.

        :param str prompt: text to show the user
        :param mixed default: default value used if no input given
        :param parent: usually the parent Config object
        :type parent: :class:`~sopel.config.Config`
        :param str section_name: the name of the containing section

        This method displays the ``prompt`` and waits for user's input on the
        terminal. If no input is provided (i.e. the user just presses "Enter"),
        the ``default`` value is returned instead.

        If :attr:`.is_secret` is ``True``, the input will be hidden, using the
        built-in :func:`~getpass.getpass` function.
        """
        if default is not NO_DEFAULT and default is not None:
            prompt = '{} [{}]'.format(prompt, default)

        if self.is_secret:
            value = getpass.getpass(prompt + ' (hidden input) ')
        else:
            value = input(prompt + ' ')

        if not value and default is NO_DEFAULT:
            raise ValueError("You must provide a value for this option.")

        value = value or default
        section = getattr(parent, section_name)

        return self._parse(value, parent, section)

    @abc.abstractmethod
    def serialize(self, value, *args, **kwargs):
        """Take some object, and return the string to be saved to the file."""

    @abc.abstractmethod
    def parse(self, value, *args, **kwargs):
        """Take a string from the file, and return the appropriate object."""

    def __get__(self, instance, owner=None):
        if instance is None:
            # If instance is None, we're getting from a section class, not an
            # instance of a section class. It makes the wizard code simpler
            # (and is really just more intuitive) to return the descriptor
            # instance here.
            return self

        value = None
        env_name = 'SOPEL_%s_%s' % (instance._section_name.upper(), self.name.upper())
        if env_name in os.environ:
            value = os.environ.get(env_name)
        elif instance._parser.has_option(instance._section_name, self.name):
            value = instance._parser.get(instance._section_name, self.name)

        settings = instance._parent
        section = getattr(settings, instance._section_name)
        return self._parse(value, settings, section)

    def _parse(self, value, settings, section):
        if value is not None:
            return self.parse(value)
        if self.default is not NO_DEFAULT:
            return self.default
        raise AttributeError(
            "Missing required value for {}.{}".format(
                section._section_name, self.name
            )
        )

    def __set__(self, instance, value):
        if value is None:
            if self.default == NO_DEFAULT:
                raise ValueError('Cannot unset an option with a required value.')
            instance._parser.remove_option(instance._section_name, self.name)
            return

        settings = instance._parent
        section = getattr(settings, instance._section_name)
        value = self._serialize(value, settings, section)
        instance._parser.set(instance._section_name, self.name, value)

    def _serialize(self, value, settings, section):
        return self.serialize(value)

    def __delete__(self, instance):
        instance._parser.remove_option(instance._section_name, self.name)


def _parse_boolean(value):
    if value is True or value == 1:
        return value
    if isinstance(value, str):
        return value.lower() in ['1', 'yes', 'y', 'true', 'on']
    return bool(value)


def _serialize_boolean(value):
    return 'true' if _parse_boolean(value) else 'false'


@deprecated(
    reason='Use BooleanAttribute instead of ValidatedAttribute with parse=bool',
    version='7.1',
    warning_in='8.0',
    removed_in='9.0',
    stack_frame=-2,
)
def _deprecated_special_bool_handling(serialize):
    if not serialize or serialize == bool:
        serialize = _serialize_boolean

    return _parse_boolean, serialize


class ValidatedAttribute(BaseValidated):
    """A descriptor for settings in a :class:`StaticSection`.

    :param str name: the attribute name to use in the config file
    :param parse: a function to be used to read the string and create the
                  appropriate object (optional; the string value will be
                  returned as-is if not set)
    :type parse: :term:`function`
    :param serialize: a function that, given an object, should return a string
                      that can be written to the config file safely (optional;
                      defaults to :class:`str`)
    :type serialize: :term:`function`
    :param bool is_secret: ``True`` when the attribute should be considered
                           a secret, like a password (default to ``False``)
    """
    def __init__(self,
                 name,
                 parse=None,
                 serialize=None,
                 default=None,
                 is_secret=False):
        super().__init__(name, default=default, is_secret=is_secret)

        if parse == bool:
            parse, serialize = _deprecated_special_bool_handling(serialize)

        # ignore typing errors on these monkeypatches for now
        # TODO: more dedicated subtypes; deprecate `parse`/`serialize` args
        self.parse = parse or self.parse  # type: ignore
        self.serialize = serialize or self.serialize  # type: ignore

    def serialize(self, value):
        """Return the ``value`` as a Unicode string.

        :param value: the option value
        :rtype: str
        """
        return str(value)

    def parse(self, value):
        """No-op: simply returns the given ``value``, unchanged.

        :param str value: the string read from the config file
        :rtype: str
        """
        return value

    def configure(self, prompt, default, parent, section_name):
        if self.parse == _parse_boolean:
            prompt += ' (y/n)'
            default = 'y' if default else 'n'
        return super().configure(prompt, default, parent, section_name)


class BooleanAttribute(BaseValidated):
    """A descriptor for Boolean settings in a :class:`StaticSection`.

    :param str name: the attribute name to use in the config file
    :param bool default: the default value to use if this setting is not
                         present in the config file

    If the ``default`` value is not specified, it will be ``False``.
    """
    def __init__(self, name, default=False):
        super().__init__(name, default=default, is_secret=False)

    def configure(self, prompt, default, parent, section_name):
        """Parse and return a value from user's input.

        :param str prompt: text to show the user
        :param bool default: default value used if no input given
        :param parent: usually the parent Config object
        :type parent: :class:`~sopel.config.Config`
        :param str section_name: the name of the containing section

        This method displays the ``prompt`` and waits for user's input on the
        terminal. If no input is provided (i.e. the user just presses "Enter"),
        the ``default`` value is returned instead.
        """
        prompt = '{} ({})'.format(prompt, 'Y/n' if default else 'y/N')
        value = input(prompt + ' ') or default
        section = getattr(parent, section_name)
        return self._parse(value, parent, section)

    def serialize(self, value):
        """Convert a Boolean value to a string for saving to the config file.

        :param bool value: the value to serialize
        """
        return 'true' if self.parse(value) else 'false'

    def parse(self, value):
        """Parse a limited set of values/objects into Boolean representations.

        :param mixed value: the value to parse

        The literal values ``True`` or ``1`` will be parsed as ``True``. The
        strings ``'1'``, ``'yes'``, ``'y'``, ``'true'``, ``'enable'``,
        ``'enabled'``, and ``'on'`` will also be parsed as ``True``,
        regardless of case. All other values will be parsed as ``False``.
        """
        if value is True or value == 1:
            return True
        if isinstance(value, str):
            return value.lower() in [
                '1',
                'enable',
                'enabled',
                'on',
                'true',
                'y',
                'yes',
            ]
        return bool(value)

    def __set__(self, instance, value):
        if value is None:
            instance._parser.remove_option(instance._section_name, self.name)
            return

        settings = instance._parent
        section = getattr(settings, instance._section_name)
        value = self._serialize(value, settings, section)
        instance._parser.set(instance._section_name, self.name, value)


class SecretAttribute(ValidatedAttribute):
    """A config attribute containing a value which must be kept secret.

    This attribute is always considered to be secret/sensitive data, but
    otherwise behaves like other any option.
    """
    def __init__(self, name, parse=None, serialize=None, default=None):
        super().__init__(
            name,
            parse=parse,
            serialize=serialize,
            default=default,
            is_secret=True,
        )


class ListAttribute(BaseValidated):
    """A config attribute containing a list of string values.

    :param str name: the attribute name to use in the config file
    :param strip: whether to strip whitespace from around each value
                  (optional, deprecated; applies only to legacy comma-separated
                  lists; multi-line lists are always stripped)
    :type strip: bool
    :param default: the default value if the config file does not define a
                    value for this option; to require explicit configuration,
                    use :const:`sopel.config.types.NO_DEFAULT` (optional)
    :type default: list

    From this :class:`StaticSection`::

        class SpamSection(StaticSection):
            cheeses = ListAttribute('cheeses')

    the option will be exposed as a Python :class:`list`::

        >>> config.spam.cheeses
        ['camembert', 'cheddar', 'reblochon', '#brie']

    which comes from this configuration file:

    .. code-block:: ini

        [spam]
        cheeses =
            camembert
            cheddar
            reblochon
            "#brie"

    Note that the ``#brie`` item starts with a ``#``, hence the double quote:
    without these quotation marks, the config parser would think it's a
    comment. The quote/unquote is managed automatically by this field, and
    if and only if it's necessary (see :meth:`parse` and :meth:`serialize`).

    .. versionchanged:: 7.0

        The option's value will be split on newlines by default. In this
        case, the ``strip`` parameter has no effect.

        See the :meth:`parse` method for more information.

    .. note::

        **About:** backward compatibility with comma-separated values.

        A :class:`ListAttribute` option used to allow to write, on a single
        line, the values separated by commas. It is still technically possible
        while raising a deprecation warning.

        In Sopel 7.x this behavior was discouraged; as of Sopel 8.x it is now
        deprecated with warnings, and it will be removed in Sopel 9.x.

        Bot owners should update their configurations to use newlines instead
        of commas.

        The comma delimiter fallback does not support commas within items in
        the list.
    """
    DELIMITER = ','  # Deprecated, will be removed in Sopel 9
    QUOTE_REGEX = re.compile(r'^"(?P<value>#.*)"$')
    """Regex pattern to match value that requires quotation marks.

    This pattern matches values that start with ``#`` inside quotation marks
    only: ``"#sopel"`` will match, but ``"sopel"`` won't, and neither will any
    variant that doesn't conform to this pattern.
    """

    def __init__(self, name, strip=True, default=None):
        default = default or []
        super().__init__(name, default=default)
        self.strip = strip  # Warn in Sopel 9.x and remove in Sopel 10.x

    def parse(self, value):
        """Parse ``value`` into a list.

        :param str value: a multi-line string of values to parse into a list
        :return: a list of items from ``value``
        :rtype: list

        .. versionchanged:: 7.0

            The value is now split on newlines, with fallback to comma
            when there is no newline in ``value``.

            When modified and saved to a file, items will be stored as a
            multi-line string (see :meth:`serialize`).

        .. versionchanged:: 8.0

            When the value contains a delimiter without newline, it warns the
            user to switch to a multi-line value, without a delimiter.

        """
        if "\n" in value:
            items = (
                # remove trailing comma
                # because `value,\nother` is valid in Sopel 7.x
                item.strip(self.DELIMITER).strip()
                for item in value.splitlines())
        else:
            # this behavior was discouraged in Sopel 7.x (in the documentation)
            # this behavior is now deprecated in Sopel 8.x
            # this behavior will be removed from Sopel 9.x
            items = value.split(self.DELIMITER)
            if self.DELIMITER in value:
                # trigger for "one, two" and "first line,"
                # a single line without the delimiter is fine
                LOGGER.warning(
                    'Using "%s" as item delimiter in option "%s" '
                    'is deprecated and will be removed in Sopel 9; '
                    'use multi-line instead',
                    self.DELIMITER, self.name)

        items = (self.parse_item(item) for item in items if item)
        if self.strip:
            return [item.strip() for item in items]

        return list(items)

    def parse_item(self, item):
        """Parse one ``item`` from the list.

        :param str item: one item from the list to parse
        :rtype: str

        If ``item`` matches the :attr:`QUOTE_REGEX` pattern, then it will be
        unquoted. Otherwise it's returned as-is.
        """
        result = self.QUOTE_REGEX.match(item)
        if result:
            return result.group('value')
        return item

    def serialize(self, value):
        """Serialize ``value`` into a multi-line string.

        :param list value: the input list
        :rtype: str
        :raise ValueError: if ``value`` is the wrong type (i.e. not a list)
        """
        if not isinstance(value, (list, set)):
            raise ValueError('ListAttribute value must be a list.')
        elif not value:
            # return an empty string when there is no value
            return ''

        # we ensure to read a newline, even with only one value in the list
        # this way, comma will be ignored when the configuration file
        # is read again later
        return '\n' + '\n'.join(self.serialize_item(item) for item in value)

    def serialize_item(self, item):
        """Serialize an ``item`` from the list value.

        :param str item: one item of the list to serialize
        :rtype: str

        If ``item`` starts with a ``#`` it will be quoted in order to prevent
        the config parser from thinking it's a comment.
        """
        if item.startswith('#'):
            # we need to protect item that would otherwise appear as comment
            return '"%s"' % item
        return item

    def configure(self, prompt, default, parent, section_name):
        each_prompt = '?'
        if isinstance(prompt, tuple):
            each_prompt = prompt[1]
            prompt = prompt[0]

        if default is not NO_DEFAULT:
            default_prompt = ','.join(['"{}"'.format(item) for item in default])
            prompt = '{} [{}]'.format(prompt, default_prompt)
        else:
            default = []
        print(prompt)
        values: list[str] = []
        value = input(each_prompt + ' ') or default
        if (value == default) and not default:
            value = ''
        while value:
            if value == default:
                values.extend(value)
            else:
                values.append(value)
            value = input(each_prompt + ' ')

        section = getattr(parent, section_name)
        values = self._serialize(values, parent, section)
        return self._parse(values, parent, section)


class SetAttribute(ListAttribute):
    """A config attribute containing a set of string values.

    :type default: set

    Constructor parameters are the same as for :class:`ListAttribute`, except
    that ``default`` should be a ``set`` instead of a ``list``.

    Configuration file semantics are also the same as :class:`ListAttribute`.
    """
    def parse(self, value):
        """Parse ``value`` into a set.

        :param str value: a multi-line string of values to parse into a set
        :return: a set of items from ``value``
        :rtype: set
        """
        items = super().parse(value)
        return set(items)

    def serialize(self, value):
        """Serialize ``value`` into a multi-line string.

        :param set value: the input set
        :rtype: str
        """
        if not isinstance(value, (set, list)):
            raise ValueError('SetAttribute value must be a set.')
        if isinstance(value, list):
            # convert to set to remove duplicates prior to serialization
            value = set(value)
        return super().serialize(value)


class ChoiceAttribute(BaseValidated):
    """A config attribute which must be one of a set group of options.

    :param str name: the attribute name to use in the config file
    :param choices: acceptable values; currently, only strings are supported
    :type choices: list or tuple
    :param default: which choice to use if none is set in the config file; to
                    require explicit configuration, use
                    :const:`sopel.config.types.NO_DEFAULT` (optional)
    :type default: str
    """
    def __init__(self, name, choices, default=None):
        super().__init__(name, default=default)
        self.choices = choices

    def parse(self, value):
        """Check the loaded ``value`` against the valid ``choices``.

        :param str value: the value loaded from the config file
        :return: the ``value``, if it is valid
        :rtype: str
        :raise ValueError: if ``value`` is not one of the valid ``choices``
        """
        if value in self.choices:
            return value
        else:
            raise ValueError(
                '{!r} is not one of the valid choices: {}'
                .format(value, ', '.join(self.choices))
            )

    def serialize(self, value):
        """Make sure ``value`` is valid and safe to write in the config file.

        :param str value: the value needing to be saved
        :return: the ``value``, if it is valid
        :rtype: str
        :raise ValueError: if ``value`` is not one of the valid ``choices``
        """
        if value in self.choices:
            return value
        else:
            raise ValueError(
                '{!r} is not one of the valid choices: {}'
                .format(value, ', '.join(self.choices))
            )


class FilenameAttribute(BaseValidated):
    """A config attribute which must be a file or directory.

    :param str name: the attribute name to use in the config file
    :param relative: whether the path should be relative to the location of
                     the config file (optional; note that absolute paths will
                     always be interpreted as absolute)
    :type relative: bool
    :param directory: whether the path should indicate a directory, rather
                      than a file (optional)
    :type directory: bool
    :param default: the value to use if none is defined in the config file; to
                    require explicit configuration, use
                    :const:`sopel.config.types.NO_DEFAULT` (optional)
    :type default: str
    """
    def __init__(self, name, relative=True, directory=False, default=None):
        super().__init__(name, default=default)
        self.relative = relative
        self.directory = directory

    def _parse(self, value, settings, section):
        if value is None:
            if self.default == NO_DEFAULT:
                raise AttributeError(
                    "Missing required value for {}.{}".format(
                        section._section_name, self.name
                    )
                )
            value = self.default

        if not value:
            return self.parse(value)

        if value.startswith('"') and value.endswith('"'):
            value = value.strip('"')
        elif value.startswith("'") and value.endswith("'"):
            value = value.strip("'")

        result = os.path.expanduser(value)
        if not os.path.isabs(result):
            if not self.relative:
                raise ValueError("Value must be an absolute path.")
            result = os.path.join(settings.homedir, result)

        return self.parse(result)

    def _serialize(self, value, settings, section):
        """Used to validate ``value`` when it is changed at runtime.

        :param settings: the config object which contains this attribute
        :type settings: :class:`~sopel.config.Config`
        :param section: the config section which contains this attribute
        :type section: :class:`~StaticSection`
        :return: the ``value``, if it is valid
        :rtype: str
        :raise ValueError: if the ``value`` is not valid
        """
        self._parse(value, settings, section)
        return self.serialize(value)

    def parse(self, value):
        """Parse ``value`` as a path on the filesystem to check.

        :param str value: the path to check
        :rtype: str
        :raise ValueError: if the directory or file doesn't exist and cannot
                           be created

        If there is no ``value``, then this returns ``None``. Otherwise, it'll
        check if the directory or file exists. If it doesn't, it'll try to
        create it.
        """
        if not value:
            return None

        if self.directory and not os.path.isdir(value):
            try:
                os.makedirs(value)
            except (IOError, OSError):
                raise ValueError(
                    "Value must be an existing or creatable directory.")
        if not self.directory and not os.path.isfile(value):
            try:
                with open(value, 'w') as f:
                    f.close()
            except (IOError, OSError):
                raise ValueError("Value must be an existing or creatable file.")
        return value

    def serialize(self, value):
        """Directly return the ``value`` without modification.

        :param str value: the value needing to be saved
        :return: the unaltered ``value``, if it is valid
        :rtype: str

        Managing the filename is done by other methods (:meth:`parse`), and
        this method is a no-op: this way it ensures that relative paths won't
        be replaced by absolute ones.
        """
        return value  # So that it's still relative
