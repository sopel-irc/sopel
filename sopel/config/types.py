# coding=utf-8
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

from __future__ import unicode_literals, absolute_import, print_function, division

import os.path
import sys
from sopel.tools import get_input

if sys.version_info.major >= 3:
    unicode = str
    basestring = (str, bytes)


class NO_DEFAULT(object):
    """A special value to indicate that there should be no default."""


class StaticSection(object):
    """A configuration section with parsed and validated settings.

    This class is intended to be subclassed with added ``ValidatedAttribute``\\s.
    """
    def __init__(self, config, section_name, validate=True):
        if not config.parser.has_section(section_name):
            config.parser.add_section(section_name)
        self._parent = config
        self._parser = config.parser
        self._section_name = section_name
        for value in dir(self):
            try:
                getattr(self, value)
            except ValueError as e:
                raise ValueError(
                    'Invalid value for {}.{}: {}'.format(section_name, value,
                                                         str(e))
                )
            except AttributeError:
                if validate:
                    raise ValueError(
                        'Missing required value for {}.{}'.format(section_name,
                                                                  value)
                    )

    def configure_setting(self, name, prompt, default=NO_DEFAULT):
        """Return a validated value for this attribute from the terminal.

        ``prompt`` will be the docstring of the attribute if not given.

        If ``default`` is passed, it will be used if no value is given by the
        user. If it is not passed, the current value of the setting, or the
        default value if it's unset, will be used. Note that if ``default`` is
        passed, the current value of the setting will be ignored, even if it is
        not the attribute's default.
        """
        clazz = getattr(self.__class__, name)
        if default is NO_DEFAULT:
            try:
                default = getattr(self, name)
            except AttributeError:
                pass
            except ValueError:
                print('The configured value for this option was invalid.')
                if clazz.default is not NO_DEFAULT:
                    default = clazz.default
        while True:
            try:
                value = clazz.configure(prompt, default, self._parent, self._section_name)
            except ValueError as exc:
                print(exc)
            else:
                break
        setattr(self, name, value)


class BaseValidated(object):
    """The base type for a descriptor in a ``StaticSection``."""
    def __init__(self, name, default=None):
        """
        ``name`` is the name of the setting in the section.
        ``default`` is the value to be returned if the setting is not set. If
        not given, AttributeError will be raised instead.
        """
        self.name = name
        self.default = default

    def configure(self, prompt, default, parent, section_name):
        """With the prompt and default, parse and return a value from terminal.
        """
        if default is not NO_DEFAULT and default is not None:
            prompt = '{} [{}]'.format(prompt, default)
        value = get_input(prompt + ' ')
        if not value and default is NO_DEFAULT:
            raise ValueError("You must provide a value for this option.")
        value = value or default
        return self.parse(value)

    def serialize(self, value):
        """Take some object, and return the string to be saved to the file.

        Must be implemented in subclasses.
        """
        raise NotImplementedError("Serialize method must be implemented in subclass")

    def parse(self, value):
        """Take a string from the file, and return the appropriate object.

        Must be implemented in subclasses."""
        raise NotImplementedError("Parse method must be implemented in subclass")

    def __get__(self, instance, owner=None):
        if instance is None:
            # If instance is None, we're getting from a section class, not an
            # instance of a session class. It makes the wizard code simpler
            # (and is really just more intuitive) to return the descriptor
            # instance here.
            return self

        env_name = 'SOPEL_%s_%s' % (instance._section_name.upper(), self.name.upper())
        if env_name in os.environ:
            value = os.environ.get(env_name)
        elif instance._parser.has_option(instance._section_name, self.name):
            value = instance._parser.get(instance._section_name, self.name)
        else:
            if self.default is not NO_DEFAULT:
                return self.default
            raise AttributeError(
                "Missing required value for {}.{}".format(
                    instance._section_name, self.name
                )
            )
        return self.parse(value)

    def __set__(self, instance, value):
        if value is None:
            instance._parser.remove_option(instance._section_name, self.name)
            return
        value = self.serialize(value)
        instance._parser.set(instance._section_name, self.name, value)

    def __delete__(self, instance):
        instance._parser.remove_option(instance._section_name, self.name)


def _parse_boolean(value):
    if value is True or value == 1:
        return value
    if isinstance(value, basestring):
        return value.lower() in ['1', 'yes', 'y', 'true', 'on']
    return bool(value)


def _serialize_boolean(value):
    return 'true' if _parse_boolean(value) else 'false'


class ValidatedAttribute(BaseValidated):
    def __init__(self, name, parse=None, serialize=None, default=None):
        """A descriptor for settings in a ``StaticSection``

        ``parse`` is the function to be used to read the string and create the
        appropriate object. If not given, return the string as-is.
        ``serialize`` takes an object, and returns the value to be written to
        the file. If not given, defaults to ``unicode``.
        """
        self.name = name
        if parse == bool:
            parse = _parse_boolean
            if not serialize or serialize == bool:
                serialize = _serialize_boolean
        self.parse = parse or self.parse
        self.serialize = serialize or self.serialize
        self.default = default

    def serialize(self, value):
        return unicode(value)

    def parse(self, value):
        return value

    def configure(self, prompt, default, parent, section_name):
        if self.parse == _parse_boolean:
            prompt += ' (y/n)'
            default = 'y' if default else 'n'
        return super(ValidatedAttribute, self).configure(prompt, default, parent, section_name)


class ListAttribute(BaseValidated):
    """A config attribute containing a list of string values.

    From this :class:`StaticSection`::

        class SpamSection(StaticSection):
            cheeses = ListAttribute('cheeses')

    the option will be exposed as a Python :class:`list`::

        >>> config.spam.cheeses
        ['camembert', 'cheddar', 'reblochon']

    which come from this configuration file::

        [spam]
        cheeses = camembert
                  cheddar
                  reblochon

    .. versionchanged:: 7.0

        The option's value will be split on newlines by default. In this
        case, the ``strip`` parameter has no effect.

        See the :meth:`parse` method for more information.

    .. note::

        **About:** backward compatibility with comma-separated values.

        A :class:`ListAttribute` option allows to write, on a single line,
        the values separated by commas. As of Sopel 7.x this behavior is
        discouraged. It will be deprecated in Sopel 8.x, then removed in
        Sopel 9.x.

        Bot owners are encouraged to update their configurations to use
        newlines instead of commas.

        The comma delimiter fallback does not support commas within items in
        the list.
    """
    DELIMITER = ','

    def __init__(self, name, strip=True, default=None):
        default = default or []
        super(ListAttribute, self).__init__(name, default=default)
        self.strip = strip

    def parse(self, value):
        """Parse ``value`` into a list.

        :param str value: a multi-line string of values to parse into a list
        :return: a list of items from ``value``
        :rtype: :class:`list`

        .. versionchanged:: 7.0

            The value is now split on newlines, with fallback to comma
            when there is no newline in ``value``.

            When modified and saved to a file, items will be stored as a
            multi-line string.
        """
        if "\n" in value:
            items = [
                # remove trailing comma
                # because `value,\nother` is valid in Sopel 7.x
                item.strip(self.DELIMITER).strip()
                for item in value.splitlines()]
        else:
            # this behavior will be:
            # - Discouraged in Sopel 7.x (in the documentation)
            # - Deprecated in Sopel 8.x
            # - Removed from Sopel 9.x
            items = value.split(self.DELIMITER)

        value = list(filter(None, items))
        if self.strip:  # deprecate strip option in Sopel 8.x
            return [v.strip() for v in value]
        else:
            return value

    def serialize(self, value):
        """Serialize ``value`` into a multi-line string."""
        if not isinstance(value, (list, set)):
            raise ValueError('ListAttribute value must be a list.')

        # we ensure to read a newline, even with only one value in the list
        # this way, comma will be ignored when the configuration file
        # is read again later
        return '\n' + '\n'.join(value)

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
        values = []
        value = get_input(each_prompt + ' ') or default
        if (value == default) and not default:
            value = ''
        while value:
            if value == default:
                values.extend(value)
            else:
                values.append(value)
            value = get_input(each_prompt + ' ')
        return self.parse(self.serialize(values))


class ChoiceAttribute(BaseValidated):
    """A config attribute which must be one of a set group of options.

    Currently, the choices can only be strings."""
    def __init__(self, name, choices, default=None):
        super(ChoiceAttribute, self).__init__(name, default=default)
        self.choices = choices

    def parse(self, value):
        if value in self.choices:
            return value
        else:
            raise ValueError('Value must be in {}'.format(self.choices))

    def serialize(self, value):
        if value in self.choices:
            return value
        else:
            raise ValueError('Value must be in {}'.format(self.choices))


class FilenameAttribute(BaseValidated):
    """A config attribute which must be a file or directory."""
    def __init__(self, name, relative=True, directory=False, default=None):
        """
        ``relative`` is whether the path should be relative to the location
        of the config file (absolute paths will still be absolute). If
        ``directory`` is True, the path must indicate a directory, rather than
        a file.
        """
        super(FilenameAttribute, self).__init__(name, default=default)
        self.relative = relative
        self.directory = directory

    def __get__(self, instance, owner=None):
        if instance is None:
            return self
        env_name = 'SOPEL_%s_%s' % (instance._section_name.upper(), self.name.upper())
        if env_name in os.environ:
            value = os.environ.get(env_name)
        elif instance._parser.has_option(instance._section_name, self.name):
            value = instance._parser.get(instance._section_name, self.name)
        else:
            if self.default is not NO_DEFAULT:
                value = self.default
            else:
                raise AttributeError(
                    "Missing required value for {}.{}".format(
                        instance._section_name, self.name
                    )
                )
        main_config = instance._parent
        this_section = getattr(main_config, instance._section_name)
        return self.parse(main_config, this_section, value)

    def __set__(self, instance, value):
        main_config = instance._parent
        this_section = getattr(main_config, instance._section_name)
        value = self.serialize(main_config, this_section, value)
        instance._parser.set(instance._section_name, self.name, value)

    def configure(self, prompt, default, parent, section_name):
        """With the prompt and default, parse and return a value from terminal.
        """
        if default is not NO_DEFAULT and default is not None:
            prompt = '{} [{}]'.format(prompt, default)
        value = get_input(prompt + ' ')
        if not value and default is NO_DEFAULT:
            raise ValueError("You must provide a value for this option.")
        value = value or default
        return self.parse(parent, section_name, value)

    def parse(self, main_config, this_section, value):
        if value is None:
            return

        value = os.path.expanduser(value)

        if not os.path.isabs(value):
            if not self.relative:
                raise ValueError("Value must be an absolute path.")
            value = os.path.join(main_config.homedir, value)

        if self.directory and not os.path.isdir(value):
            try:
                os.makedirs(value)
            except (IOError, OSError):
                raise ValueError(
                    "Value must be an existing or creatable directory.")
        if not self.directory and not os.path.isfile(value):
            try:
                open(value, 'w').close()
            except (IOError, OSError):
                raise ValueError("Value must be an existing or creatable file.")
        return value

    def serialize(self, main_config, this_section, value):
        self.parse(main_config, this_section, value)
        return value  # So that it's still relative
