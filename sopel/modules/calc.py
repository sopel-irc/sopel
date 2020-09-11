# coding=utf-8
"""
calc.py - Sopel Calculator Plugin
Copyright 2008, Sean B. Palmer, inamidst.com
Licensed under the Eiffel Forum License 2.

https://sopel.chat
"""
from __future__ import absolute_import, division, print_function, unicode_literals

from sopel import plugin
from sopel.tools.calculation import eval_equation


@plugin.command('c', 'calc')
@plugin.example('.c 5 + 3', '8')
@plugin.example('.c 0.9*10', '9')
@plugin.example('.c 10*0.9', '9')
@plugin.example('.c 2*(1+2)*3', '18')
@plugin.example('.c 2**10', '1024')
@plugin.example('.c 5 // 2', '2')
@plugin.example('.c 5 / 2', '2.5')
@plugin.output_prefix('[calc] ')
def c(bot, trigger):
    """Evaluate some calculation."""
    if not trigger.group(2):
        bot.reply('Nothing to calculate.')
        return
    # Account for the silly non-Anglophones and their silly radix point.
    eqn = trigger.group(2).replace(',', '.')
    try:
        result = eval_equation(eqn)
        result = "{:.10g}".format(result)
    except ZeroDivisionError:
        bot.reply('Division by zero is not supported in this universe.')
        return
    except SyntaxError:
        bot.reply('Invalid syntax')
        return

    bot.say(result)
