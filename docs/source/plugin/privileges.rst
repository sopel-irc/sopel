===============
User privileges
===============

IRC users can have privileges in a **channel**, given by MODE messages such as:

.. code-block:: irc

    MODE #example +ov Nickname Nickname

This will give both OP and Voice privileges to the user named "Nickname" in the
"#example" channel (and only in this channel). When Sopel receives a MODE
message it registers and updates its knowledge of a user's privileges in a
channel, which can be used by plugins in various way.

Access rights
=============

Privileged users
----------------

A plugin can limit who can trigger its callables using the
:func:`~sopel.plugin.require_privilege` decorator::

    from sopel import plugin, privileges

    @plugin.require_privilege(privileges.OP)
    @plugin.require_chanmsg
    @plugin.command('chanopcommand')
    def chanop_command(bot, trigger):
        # only a channel operator can use this command

This way, only users with OP privileges or above in a channel can use the
command ``chanopcommand`` in that channel: other users will be ignored by the
bot. It is possible to tell these users why with the ``message`` parameter::

    @plugin.require_privilege(privileges.OP, 'You need +o privileges.')

.. important::

    A command that requires channel privileges will always execute if
    called from a private message to the bot. You can use the
    :func:`sopel.plugin.require_chanmsg` decorator to ignore the command
    if it's called in PMs.

The bot is a user too
---------------------

Sometimes, you may want the bot to be a privileged user in a channel to allow a
command. For that, there is the :func:`~sopel.plugin.require_bot_privilege`
decorator::

    @plugin.require_bot_privilege(privileges.OP)
    @plugin.require_chanmsg
    @plugin.command('opbotcommand')
    def change_topic(bot, trigger):
        # only if the bot has OP privileges

This way, this command cannot be used if the bot doesn't have the right
privileges in the channel where it is used, independent from the privileges of
the user who invokes the command.

As with ``require_privilege``, you can provide an error message::

    @plugin.require_bot_privilege(
        privileges.OP, 'The bot needs +o privileges.')

And you **can** use both ``require_privilege`` and ``require_bot_privilege`` on
the same plugin callable::

    @plugin.require_privilege(privileges.VOICE)
    @plugin.require_bot_privilege(privileges.OP)
    @plugin.require_chanmsg
    @plugin.command('special')
    def special_command(bot, trigger):
        # only if the user has +v and the bot has +o (or above)

This way, you can allow a less privileged user to access a command for a more
privileged bot (this works for any combination of privileges).

.. important::

    A command that requires channel privileges will always execute if
    called from a private message to the bot. You can use the
    :func:`sopel.plugin.require_chanmsg` decorator to ignore the command
    if it's called in PMs.

Restrict to user account
------------------------

Sometimes, a command should be used only by users who are authenticated via
IRC services. On IRC networks that provide such information to IRC clients,
this is possible with the :func:`~sopel.plugin.require_account` decorator::

    @plugin.require_privilege(privileges.VOICE)
    @plugin.require_account
    @plugin.require_chanmsg
    @plugin.command('danger')
    def dangerous_command(bot, trigger):
        # only if the user has +v and has a registered account

This has two consequences:

1. this command cannot be used by users who are not authenticated
2. this command cannot be used on an IRC network that doesn't allow
   authentication or doesn't expose that information

It makes your plugin safer to use and prevents the possibility to use it on
insecure IRC networks.

.. seealso::

   `IRCv3 account-tracking specifications`__.

.. __: https://ircv3.net/irc/#account-tracking


Getting user privileges in a channel
====================================

Within a :term:`plugin callable`, you can get access to a user's privileges in
a channel to check privileges manually. For example, you could adapt the level
of information your callable provides based on said privileges.

First you need a user's nick and a channel (e.g. from the trigger parameter),
then you can get that user's privileges through the **channel**'s
:attr:`~sopel.tools.target.Channel.privileges` attribute::

    user_privileges = channel.privileges['Nickname']
    user_privileges = channel.privileges[trigger.nick]

You can check the user's privileges manually using bitwise operators. Here
for example, we check if the user is voiced (+v) or above::

    from sopel import privileges

    if user_privileges & privileges.VOICE:
        # user is voiced
    elif user_privileges > privileges.VOICE:
        # not voiced, but higher privileges
        # like privileges.HALFOP or privileges.OP
    else:
        # no privilege

Another option is to use dedicated methods from the ``channel`` object::

    if channel.is_voiced('Nickname'):
        # user is voiced
    elif channel.has_privilege('Nickname', privileges.VOICE):
        # not voiced, but higher privileges
        # like privileges.HALFOP or privileges.OP
    else:
        # no privilege

You can also iterate over the list of users and filter them by privileges::

    # get users with the OP privilege
    op_users = [
        user
        for nick, user in channel.users
        if channel.is_op(nick, privileges.OP)
    ]

    # get users with OP privilege or above
    op_or_higher_users = [
        user
        for nick, user in channel.users
        if channel.has_privileges(nick, privileges.OP)
    ]

.. seealso::

    Read about the :class:`~sopel.tools.target.Channel` and
    :class:`~sopel.tools.target.User` classes for more details.


sopel.privileges
================

.. automodule:: sopel.privileges
   :members:
   :member-order: bysource
