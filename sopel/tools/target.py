# coding=utf-8
from __future__ import unicode_literals, absolute_import, print_function, division

import functools
from sopel.tools import Identifier


@functools.total_ordering
class User(object):
    def __init__(self, nick, user, host):
        assert isinstance(nick, Identifier)
        self.nick = nick
        self.user = user
        self.host = host
        self.channels = {}

    hostmask = property(lambda self: '{}!{}@{}'.format(self.nick, self.user,
                                                       self.host))

    def __eq__(self, other):
        if not isinstance(other, User):
            return NotImplemented
        return self.name == other.name

    def __lt__(self, other):
        if not isinstance(other, User):
            return NotImplemented
        return self.name < other.name


@functools.total_ordering
class Channel(object):
    def __init__(self, name):
        assert isinstance(name, Identifier)
        self.name = name
        self.users = {}
        self.privileges = {}

    def clear_user(self, nick):
        user = self.users[nick]
        user.channels.pop(self.name, None)
        del self.users[nick]
        del self.privileges[nick]

    def add_user(self, user):
        assert isinstance(user, User)
        self.users[user.nick] = user
        self.privileges[user.nick] = 0

    def rename_user(self, old, new):
        if old in self.users:
            self.users[new] = self.users.pop(old)
        if old in self.privileges:
            self.privileges[new] = self.privileges.pop(old)

    def __eq__(self, other):
        if not isinstance(other, Channel):
            return NotImplemented
        return self.name == other.name

    def __lt__(self, other):
        if not isinstance(other, Channel):
            return NotImplemented
        return self.name < other.name
