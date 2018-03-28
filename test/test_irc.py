# coding=utf-8
"""Tests for message formatting"""
from __future__ import unicode_literals, absolute_import, print_function, division

import pytest

import asynchat
import os
import shutil
import socket
import tempfile
import asyncore

from sopel import irc
from sopel.tools import Identifier
import sopel.config as conf


HOST = '127.0.0.1'
SERVER_QUIT = 'QUIT'


class BasicServer(asyncore.dispatcher):
    def __init__(self, address, handler):
        asyncore.dispatcher.__init__(self)
        self.response_handler = handler
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.bind(address)
        self.address = self.socket.getsockname()
        self.listen(1)
        return

    def handle_accept(self):
        # Called when a client connects to our socket
        client_info = self.accept()
        BasicHandler(sock=client_info[0], handler=self.response_handler)
        self.handle_close()
        return

    def handle_close(self):
        self.close()


class BasicHandler(asynchat.async_chat):
    ac_in_buffer_size = 512
    ac_out_buffer_size = 512

    def __init__(self, sock, handler):
        self.received_data = []
        asynchat.async_chat.__init__(self, sock)
        self.handler_function = handler
        self.set_terminator(b'\n')
        return

    def collect_incoming_data(self, data):
        self.received_data.append(data.decode('utf-8'))

    def found_terminator(self):
        self._process_command()

    def _process_command(self):
        command = ''.join(self.received_data)
        response = self.handler_function(self, command)
        self.push(':fake.server {}\n'.format(response).encode())
        self.received_data = []


def start_server(rpl_function=None):
    def rpl_func(msg):
        print(msg)
        return msg

    if rpl_function is None:
        rpl_function = rpl_func

    address = ('localhost', 0)  # let the kernel give us a port
    server = BasicServer(address, rpl_function)
    return server


@pytest.fixture
def bot(request):
    cfg_dir = tempfile.mkdtemp()
    print(cfg_dir)
    filename = tempfile.mkstemp(dir=cfg_dir)[1]
    os.mkdir(os.path.join(cfg_dir, 'modules'))

    def fin():
        print('teardown config file')
        shutil.rmtree(cfg_dir)
    request.addfinalizer(fin)

    def gen(data):
        with open(filename, 'w') as fileo:
            fileo.write(data)
        cfg = conf.Config(filename)
        irc_bot = irc.Bot(cfg)
        irc_bot.config = cfg
        return irc_bot

    return gen


def test_bot_init(bot):
    test_bot = bot(
        '[core]\n'
        'owner=Baz\n'
        'nick=Foo\n'
        'user=Bar\n'
        'name=Sopel\n'
    )
    assert test_bot.nick == Identifier('Foo')
    assert test_bot.user == 'Bar'
    assert test_bot.name == 'Sopel'


def basic_irc_replies(server, msg):
    if msg.startswith('NICK'):
        return '001 Foo :Hello'
    elif msg.startswith('USER'):
        # Quit here because good enough
        server.close()
    elif msg.startswith('PING'):
        return 'PONG{}'.format(msg.replace('PING', '', 1))
    elif msg.startswith('CAP'):
        return 'CAP * :'
    elif msg.startswith('QUIT'):
        server.close()
    else:
        return '421 {} :Unknown command'.format(msg)


def test_bot_connect(bot):
    test_bot = bot(
        '[core]\n'
        'owner=Baz\n'
        'nick=Foo\n'
        'user=Bar\n'
        'name=Sopel\n'
        'host=127.0.0.1\n'
        'timeout=10\n'
    )
    s = start_server(basic_irc_replies)

    # Do main run
    test_bot.run(HOST, s.address[1])
