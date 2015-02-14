# coding=utf8
from __future__ import unicode_literals

if sys.version_info.major >= 3:
    unicode = str
    basestring = str


class StrictConfigSection(object):
    # TODO make take a parser
    def __init__(self, section):
        self._section = section


def _bool(value):
    if value.lower() in ['1', 'yes', 'true', 'on']:
        return True
    elif value.lower() in ['0', 'no', 'false', 'off']:
        return False
    else:
        raise ValueError('Value must be a bool-like string.')


class ConfigProperty(object):
    def __init__(self, name, example=None, default_to_example=False,
                 cls=unicode):
        self.name = name
        self.example = example
        self._do_default = defaults
        if cls is bool:
            cls = _bool
        elif cls is list:
            cls = _list
        self._cls = cls
        self._have_parsed = False
        self._deserialized = None

    def __get__(self, obj, objtype=None):
        if not self._have_parsed:
            value = getattr(obj._section, self.name)
            self._deserialized = self.deserialize(value)
            self._have_parsed = True
        return self._deserialized

    def __set__(self, obj, value):
        serial = self.serialize(serial)
        self._deserialized = value
        self._have_parsed = True
        setattr(obj._section, self.name, serial)

    def deserialize(self, value):
        """Return the value as the appropriate type."""
        return self._cls(value)

    def serialize(self, value):
        """Return the value as a string to be put in the config file"""
        return unicode(value)
        #TODO validate doable config values?


class CoreConfig(StrictConfigSection):
    # name, example, default, cls
    _strict = True
    nick = ConfigProperty('nick', Identifier('Willie'), True, Identifier)
    """The nickname for the bot"""
    user = ConfigProperty('user', 'willie', True)
    """The "user" for your bot (the part that comes before the @ in the hostname)"""
    name = ConfigProperty('name', 'Willie - http://willie.dftba.net',
                          True)
    """The "real name" of you bot for WHOIS responses"""
    host = ConfigProperty('host', 'irc.dftba.net', True)
    """The host to connect to"""
    port = ConfigProperty('port', 6667, True, int)
    """The port to connect to"""
    use_ssl = ConfigProperty('use_ssl', False, True, bool)
