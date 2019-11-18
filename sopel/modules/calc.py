# coding=utf-8
"""
calc.py - Sopel Calculator Module
Copyright 2008, Sean B. Palmer, inamidst.com
Licensed under the Eiffel Forum License 2.

https://sopel.chat
"""
from __future__ import unicode_literals, absolute_import, print_function, division

from sopel.module import commands, example
from sopel.tools.calculation import eval_equation


@commands('c', 'calc')
@example('.c 5 + 3', '8')
@example('.c 0.9*10', '9')
@example('.c 10*0.9', '9')
@example('.c 2*(1+2)*3', '18')
@example('.c 2**10', '1024')
@example('.c 5 // 2', '2')
@example('.c 5 / 2', '2.5')
def c(bot, trigger):
    """Evaluate some calculation."""
    if not trigger.group(2):
        return bot.reply("Nothing to calculate.")
    # Account for the silly non-Anglophones and their silly radix point.
    eqn = trigger.group(2).replace(',', '.')
    try:
        result = eval_equation(eqn)
        result = "{:.10g}".format(result)
    except ZeroDivisionError:
        result = "Division by zero is not supported in this universe."
    except Exception as e:
        result = "{error}: {msg}".format(error=type(e), msg=e)
    bot.reply(result)


if __name__ == "__main__":
    from sopel.test_tools import run_example_tests
    run_example_tests(__file__)
