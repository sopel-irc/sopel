.. _plugin-test:

===============
Automated tests
===============

Testing a plugin manually can become tedious and it is an activity prone to
human mistakes. To help automate testing, Sopel provides a
:mod:`pytest plugin <sopel.tests.pytest_plugin>` with a set of testing tools
such as :mod:`factories <sopel.tests.factories>` and
:mod:`mock objects <sopel.tests.mocks>`.

.. contents::
   :local:
   :depth: 2

The pytest plugin
=================

Sopel's testing tools rely on pytest: when you install Sopel, it declares a
pytest plugin named ``pytest-sopel``. Then you can `install pytest`__ and start
writing your tests—no configuration required!

Assuming your test files are in the ``test`` folder in your project directory::

    project_dir/
        myplugin/
            __init__.py
            config.py
            commands.py
        test/
            test_command.py
            test_config.py
        README.md
        setup.py
        setup.cfg

You can run your test suite with::

    py.test -v test/

.. __: https://docs.pytest.org/en/stable/getting-started.html

.. note::

    This document assumes that your tests are in the ``test`` folder.

Example
=======

Testing a plugin is not easy, as commands and rules tend to need a lot of
context and setup, so first here is an example. Later sections of this document
will discuss the different parts required for this example.

.. code-block::

    import pytest
    from sopel.tests import rawlist


    TEST_NAME = 'test.cfg'
    TEST_CONFIG = """
    [core]
    owner = OwnerNick
    nick = TestBot
    """


    @pytest.fixture
    def bot(configfactory, botfactory):
        settings = configfactory(TEST_NAME, TEST_CONFIG)
        return botfactory.preloaded(settings, ['myplugin'])


    @pytest.fixture
    def irc(bot, ircfactory):
        return ircfactory(bot)


    @pytest.fixture
    def user(userfactory):
        return userfactory('MyNick')


    @pytest.fixture
    def owner(userfactory):
        return userfactory('OwnerNick')


    def test_my_command(bot, irc, user):
        irc.pm(user, '.mycommand arg')

        assert bot.backend.message_sent == rawlist(
            'PRIVMSG MyNick :Command answer to a regular user.'
        )


    def test_my_command_owner(bot, irc, owner):
        irc.pm(owner, '.mycommand arg')

        assert bot.backend.message_sent == rawlist(
            'PRIVMSG MyNick :Command answer to my owner.'
        )


Test setup
==========

Before you can actually test a rule or a command, you will need to set up:

* a test configuration
* a test bot
* a test server and test users
* or a test trigger

For that, Sopel provides factories through pytest fixtures. In the above
example, these factories are used to create custom pytest fixtures.

.. seealso::

    Sopel uses a lot of fixtures both from pytest and custom ones specificaly
    made for its test suite. Check the `pytest fixtures documentation`__ to
    learn more about them as well as how to create your own.

.. __: https://docs.pytest.org/en/stable/fixture.html

Test configuration
------------------

The configuration file is the first thing the test bot will require, and you
may need it too. You can use the
:func:`~sopel.tests.pytest_plugin.configfactory` fixture::

    TEST_NAME = 'test.cfg'
    TEST_CONFIG = """
    [core]
    owner = testnick
    nick = TestBot
    """

    def test_my_command(configfactory):
        tmpconfig = configfactory(TEST_NAME, TEST_CONFIG)

If you have a custom section for your plugin, you will need to declare it, as
you would do in your :func:`setup` function::

    from your_plugin.config import MyPluginSection

    def test_my_command(configfactory):
        tmpconfig = configfactory(TEST_NAME, TEST_CONFIG)
        tmpconfig.define_section('myplugin', MyPluginSection)

And since we are using pytest, you can create your own local fixture for that::

    @pytest.fixture
    def tmpconfig(configfactory):
        return configfactory(TEST_NAME, TMP_CONFIG)

    def test_my_command(tmpconfig):
        tmpconfig.define_section('myplugin', MyPluginSection)

If all you need is a test configuration, you could put the section definition
within your fixture. However, there are other options available to you when you
use a test bot.

Test bot
--------

Now that you have a test configuration available through your custom
``tmpconfig`` fixture, you may want a test bot. Use the
:func:`~sopel.tests.pytest_plugin.botfactory` fixture for that::

    def test_my_command(tmpconfig, botfactory):
        bot = botfactory(tmpconfig)

However at this point, the bot doesn't know about your plugin, so it hasn't
run the setup phase. You can do that with the
:meth:`~sopel.tests.factories.BotFactory.preloaded` method::

    def test_my_command(tmpconfig, botfactory):
        bot = botfactory.preloaded(tmpconfig, ['myplugin'])
        assert bot.has_plugin('myplugin')  # should be True

.. important::

    When using the :meth:`~sopel.tests.factories.BotFactory.preloaded` method,
    you must not define your config sections manually, as this should be done
    by your ``setup`` plugin hook.

Of course, if you want to reuse the same test bot in all your tests, you can
create a fixture for that::

    @pytest.fixture
    def bot(configfactory, botfactory):
        settings = configfactory(TEST_NAME, TEST_CONFIG)
        return botfactory.preloaded(settings, ['myplugin'])

And then use it in your tests::

    def test_my_command(bot):
        assert bot.has_plugin('myplugin')  # should be True

The ``bot`` created by the factory is a regular instance of
:class:`sopel.bot.Sopel` with a
:class:`test IRC backend <sopel.tests.mocks.MockIRCBackend>` instead of a
regular one. This backend doesn't send anything over the network and instead
it registers everything into its ``message_sent`` list::

    from sopel.tests import rawlist


    def test_my_command(bot):
        bot.say('Hi!', '#channel')
        assert len(bot.backend.message_sent) == 1
        assert bot.backend.message_sent == rawlist(
            'PRIVMSG #channel :Hi!',
        )

.. seealso::

    For more information about the :func:`~sopel.tests.rawlist` function,
    see the `Checking the bot's output`_ section.

Test Server and test Users
--------------------------

Now that you have a test bot properly set up, it's time for the last parts
of your test setup: a test server with test users. As usual, there are fixtures
to help you. The :func:`~sopel.tests.pytest_plugin.ircfactory` can be used to
create a test server, and the :func:`~sopel.tests.pytest_plugin.userfactory`
can create test users::

    @pytest.fixture
    def irc(bot, ircfactory):
        return ircfactory(bot)

    def test_my_command(bot, irc, userfactory):
        user = userfactory('MyNick')
        irc.pm(user, '.mycommand arg')

        assert bot.backend.message_sent == rawlist(
            'PRIVMSG MyNick :Command answer to a regular user.'
        )

    def test_my_command_owner(bot, irc, userfactory):
        owner = userfactory('OwnerNick')
        irc.pm(owner, '.mycommand arg')

        assert bot.backend.message_sent == rawlist(
            'PRIVMSG MyNick :Command answer to my owner.'
        )

As usual, you can create custom fixtures for the test server (as above) and for
your test users, for example, one for a regular user, and one for the owner::

    @pytest.fixture
    def user(userfactory):
        return userfactory('MyNick')


    @pytest.fixture
    def owner(userfactory):
        return userfactory('OwnerNick')

Channel messages
................

A bot can join channels, and so does your test bot: by using the test server,
you can make the bot join a channel, or add new users to a channel while the
bot is already in it::

    def test_my_command(bot, irc, user, owner):
        # bot joins #channel with the owner in it
        irc.channel_join('#channel', users=[owner])

        # user joins #channel after
        irc.join(user, '#channel')

        # clear messages on join
        bot.backend.clear_message_sent()

        # user talks into a channel
        irc.say(user, '.mycommand arg')

        assert bot.backend.message_sent == rawlist(
            'PRIVMSG #channel :MyNick: my reply into a channel.'
        )

You can automate this setup within your fixture::

    @pytest.fixture
    def irc(bot, user, owner, ircfactory):
        test_server = ircfactory(bot)
        # auto-join channels
        test_server.channel_join('#channel', users=[owner, user])
        # clear messages on join
        bot.backend.clear_message_sent()
        return test_server

And now you are all set up to test your plugin's commands and rules!

Checking the bot's output
=========================

Once you have a test bot (or a wrapped version for your command), you can check
what the bot said after running your command thanks to the
:func:`~sopel.tests.rawlist` function::

    from sopel.tests import rawlist

    def test_my_command(bot):
        bot.say('hi!', '#channel')
        bot.say('how are you?', 'TestUser')
        assert bot.backend.message_sent == rawlist(
            'PRIVMSG #channel :Hi!',
            'PRIVMSG TestUser :how are you?',
        )

The test bot has a :class:`test backend <sopel.tests.mocks.MockIRCBackend>`
that registers everything the bot tried to send to the IRC server without
actually sending anything to any server.

The ``rawlist`` function is a convenient helper that helps you compare what was
registered by properly encoding and formatting your lines.
