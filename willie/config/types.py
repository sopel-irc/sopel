# coding=utf8

from __future__ import unicode_literals
import os.path
import sys

try:
    import configparser
except ImportError:
    import ConfigParser as configparser

if sys.version_info.major >= 3:
    unicode = str
    basestring = (str, bytes)


class StaticSection(object):
    """A configuration section with parsed and validated settings.

    This class is intended to be subclassed with added ``ValidatedAttribute``s.
    """
    def __init__(self, config, section_name):
        if not config.parser.has_section(section_name):
            raise ValueError("Section {} doesn't exist".format(section_name))
        self._parent = config
        self._parser = config.parser
        self._section_name = section_name
        for value in self.__dict__.keys():
            try:
                getattr(self, value)
            except ValueError as e:
                raise ValueError(
                    'Invalid value for {}.{}: {}'.format(section_name, value,
                                                         e.messgae)
                )
            except AttributeError:
                raise ValueError(
                    'Missing required value for {}.{}'.format(section_name,
                                                              value)
                )


class NO_DEFAULT(object):
    """Nonce value to allow a default of None"""


class BaseValidated(object):
    def __init__(self, name, default=None):
        self.name = name
        self.default = default

    def serialize(self, value):
        raise NotImplemented("Serialize method must be implemented in subclass")

    def parse(self, value):
        raise NotImplemented("Parse method must be implemented in subclass")

    def __get__(self, instance, owner=None):
        try:
            value = instance._parser.get(instance._section_name, self.name)
        except configparser.NoOptionError:
            if self.default is not NO_DEFAULT:
                return self.default
            raise AttributeError(
                "Missing required value for {}.{}".format(
                    instance._section_name, self.name
                )
            )
        return self.parse(value)

    def __set__(self, instance, value):
        value = self.serialize(value)
        instance._parser.set(instance._section_name, self.name, value)

    def __delete__(self, instance):
        instance._parser.remove_option(instance._section_name, self.name)


def _parse_boolean(value):
    if value is True or value == 1:
        return value
    if isinstance(value, basestring):
        return value.lower() in ['1', 'yes', 'true', 'on']
    return bool(value)


def _serialize_boolean(value):
    return 'true' if _parse_boolean(value) else 'false'


class ValidatedAttribute(BaseValidated):
    def __init__(self, name, parse=None, serialize=None, default=None):
        """A descriptor for settings in a ``StaticSection``

        ``name`` is the name of the setting in the section.
        ``parse`` is the function to be used to read the string and create the
        appropriate object. If not given, return the string as-is.
        ``serialize`` takes an object, and returns the value to be written to
        the file. If not given, defaults to ``unicode``.
        ``default`` is the value to be returned if the setting is not set. If
        not given, AttributeError will be raised instead."""
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


class ListAttribute(BaseValidated):
    def __init__(self, name, default=None):
        default = default or []
        super(ListAttribute, self).__init__(name, default)

    def parse(self, value):
        return value.split(',')

    def serialize(self, value):
        return ','.join(value)


class ChoiceAttribute(BaseValidated):
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


class _HomedirAttribute(BaseValidated):
    def __init__(self):
        pass

    def __get__(self, instance, owner=None):
        return os.path.dirname(instance._parent.filename)

    def __put__(self, instance, value):
        raise AttributeError("Can't set attribute.")

    def __delete__(self, instance):
        raise AttributeError("Can't delete attribute.")


class FilenameAttribute(BaseValidated):
    def __init__(self, name, relative=True, directory=False, default=None):
        super(FilenameAttribute, self).__init__(name, default=default)
        self.relative = relative
        self.directory = directory

    def __get__(self, instance, owner=None):
        try:
            value = instance._parser.get(instance._section_name, self.name)
        except configparser.NoOptionError:
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

    def parse(self, main_config, this_section, value):
        if not os.path.isabs(value):
            if not self.relative:
                raise ValueError("Value must be an absolute path.")
            value = os.path.join(main_config.core.homedir, value)

        value = os.path.expanduser(value)

        if self.directory and not os.path.isdir(value):
            try:
                os.mkdirs(value)
            except OSError:
                raise ValueError(
                    "Value must be an existing or creatable directory.")
        if not self.directory and not os.path.isfile(value):
            try:
                open(value, 'w').close()
            except OSError:
                raise ValueError("Value must be an exisint or creatable file.")
        return value

    def serialize(self, main_config, this_section, value):
        self.parse(main_config, this_section, value)
        return value  # So that it's still relative
