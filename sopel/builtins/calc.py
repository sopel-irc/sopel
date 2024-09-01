"""
calc.py - Sopel Calculator Plugin
Copyright 2008, Sean B. Palmer, inamidst.com
Licensed under the Eiffel Forum License 2.

https://sopel.chat
"""
from __future__ import annotations

from sopel import plugin
from sopel.tools.calculation import eval_equation


@plugin.command('c', 'calc')
@plugin.example('.c', 'Nothing to calculate.')
@plugin.example('.c foo * bar', "Can't process expression: Node type 'Name' is not supported.")
@plugin.example('.c 10 / 0', 'Division by zero is not supported in this universe.')
@plugin.example('.c 10\\2', 'Invalid syntax')
@plugin.example('.c (10**1000000)**2',
                "Error running calculation: "
                "ValueError('Pow expression too complex to calculate.')")
@plugin.example('.c (10**100000)**2 * (10**100000)**2',
                "Error running calculation: "
                "ValueError('Value is too large to be handled in limited time and memory.')")
@plugin.example('.c 5 + 3', '8')
@plugin.example('.c 0.9*10', '9')
@plugin.example('.c 10*0.9', '9')
@plugin.example('.c 0.5**2', '0.25')
@plugin.example('.c 3**0', '1')
@plugin.example('.c 0 * 5', '0')
@plugin.example('.c 5**5', '3125')
@plugin.example('.c 2*(1+2)*3', '18', user_help=True)
@plugin.example('.c 2**10', '1024', user_help=True)
@plugin.example('.c 5 // 2', '2', user_help=True)
@plugin.example('.c 5 / 2', '2.5', user_help=True)
@plugin.output_prefix('[calc] ')
def c(bot, trigger):
    """Evaluate some calculation."""
    if not trigger.group(2):
        bot.reply('Nothing to calculate.')
        return
    # Account for the silly non-Anglophones and their silly radix point.
    eqn = trigger.group(2).replace(',', '.')
    try:
        result = "{:.10g}".format(eval_equation(eqn))
    except eval_equation.Error as err:
        bot.reply("Can't process expression: {}".format(str(err)))
        return
    except ZeroDivisionError:
        bot.reply('Division by zero is not supported in this universe.')
        return
    except SyntaxError:
        bot.reply('Invalid syntax')
        return
    except ValueError as err:
        bot.reply("Error running calculation: %r" % err)
        return

    bot.say(result)
