# coding=utf-8
"""
py.py - Sopel Python Eval Module
Copyright 2008, Sean B. Palmer, inamidst.com
Licensed under the Eiffel Forum License 2.

https://sopel.chat
"""
from __future__ import unicode_literals, absolute_import, print_function, division

from requests import get

from sopel import module
from sopel.config.types import StaticSection, ValidatedAttribute
from sopel.tools.web import quote


class PySection(StaticSection):
    oblique_instance = ValidatedAttribute('oblique_instance',
                                          default='https://oblique.sopel.chat/')
    """The Oblique instance to use when evaluating Python expressions"""


def configure(config):
    """
    | name | example | purpose |
    | ---- | ------- | ------- |
    | oblique_instance | https://oblique.sopel.chat/ | The Oblique instance to use when evaluating Python expressions (see <https://github.com/sopel-irc/oblique>) |
    """
    config.define_section('py', PySection)
    config.py.configure_setting(
        'oblique_instance',
        'Enter the base URL of a custom Oblique instance (optional): '
    )


def setup(bot):
    bot.config.define_section('py', PySection)

    if not any(
        bot.config.py.oblique_instance.startswith(prot)
        for prot in ['http://', 'https://']
    ):
        raise ValueError('Oblique instance URL must start with a protocol.')

    if not bot.config.py.oblique_instance.endswith('/'):
        bot.config.py.oblique_instance += '/'


@module.commands('py')
@module.output_prefix('[py] ')
@module.example('.py len([1,2,3])', '3', online=True)
def py(bot, trigger):
    """Evaluate a Python expression."""
    if not trigger.group(2):
        return bot.reply('I need an expression to evaluate.')

    query = trigger.group(2)
    uri = bot.config.py.oblique_instance + 'py/'
    answer = get(uri + quote(query)).content.decode('utf-8')
    if answer:
        bot.say(answer)
    else:
        bot.reply('Sorry, no result.')


if __name__ == "__main__":
    from sopel.test_tools import run_example_tests
    run_example_tests(__file__)
