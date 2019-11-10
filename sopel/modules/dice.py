# coding=utf-8
"""
dice.py - Sopel Dice Module
Copyright 2010-2013, Dimitri "Tyrope" Molenaars, TyRope.nl
Copyright 2013, Ari Koivula, <ari@koivu.la>
Licensed under the Eiffel Forum License 2.

https://sopel.chat
"""
from __future__ import unicode_literals, absolute_import, print_function, division

import operator
import random
import re

import sopel.module
from sopel.tools.calculation import eval_equation


class DicePouch:
    def __init__(self, num_of_die, type_of_die, addition):
        """Initialize dice pouch and roll the dice.

        Args:
            num_of_die: number of dice in the pouch.
            type_of_die: how many faces the dice have.
            addition: how much is added to the result of the dice.
        """
        self.num = num_of_die
        self.type = type_of_die
        self.addition = addition

        self.dice = {}
        self.dropped = {}

        self.roll_dice()

    def roll_dice(self):
        """Roll all the dice in the pouch."""
        self.dice = {}
        self.dropped = {}
        for __ in range(self.num):
            number = random.randint(1, self.type)
            count = self.dice.setdefault(number, 0)
            self.dice[number] = count + 1

    def drop_lowest(self, n):
        """Drop n lowest dice from the result.

        Args:
            n: the number of dice to drop.
        """

        sorted_x = sorted(self.dice.items(), key=operator.itemgetter(0))

        for i, count in sorted_x:
            count = self.dice[i]
            if n == 0:
                break
            elif n < count:
                self.dice[i] = count - n
                self.dropped[i] = n
                break
            else:
                self.dice[i] = 0
                self.dropped[i] = count
                n = n - count

        for i, count in self.dropped.items():
            if self.dice[i] == 0:
                del self.dice[i]

    def get_simple_string(self):
        """Return the values of the dice like (2+2+2[+1+1])+1."""
        dice = self.dice.items()
        faces = ("+".join([str(face)] * times) for face, times in dice)
        dice_str = "+".join(faces)

        dropped_str = ""
        if self.dropped:
            dropped = self.dropped.items()
            dfaces = ("+".join([str(face)] * times) for face, times in dropped)
            dropped_str = "[+%s]" % ("+".join(dfaces),)

        plus_str = ""
        if self.addition:
            plus_str = "{:+d}".format(self.addition)

        return "(%s%s)%s" % (dice_str, dropped_str, plus_str)

    def get_compressed_string(self):
        """Return the values of the dice like (3x2[+2x1])+1."""
        dice = self.dice.items()
        faces = ("%dx%d" % (times, face) for face, times in dice)
        dice_str = "+".join(faces)

        dropped_str = ""
        if self.dropped:
            dropped = self.dropped.items()
            dfaces = ("%dx%d" % (times, face) for face, times in dropped)
            dropped_str = "[+%s]" % ("+".join(dfaces),)

        plus_str = ""
        if self.addition:
            plus_str = "{:+d}".format(self.addition)

        return "(%s%s)%s" % (dice_str, dropped_str, plus_str)

    def get_sum(self):
        """Get the sum of non-dropped dice and the addition."""
        result = self.addition
        for face, times in self.dice.items():
            result += face * times
        return result

    def get_number_of_faces(self):
        """Returns sum of different faces for dropped and not dropped dice

        This can be used to estimate, whether the result can be shown in
        compressed form in a reasonable amount of space.
        """
        return len(self.dice) + len(self.dropped)


def _roll_dice(bot, dice_expression):
    result = re.search(
        r"""
        (?P<dice_num>-?\d*)
        d
        (?P<dice_type>-?\d+)
        (v(?P<drop_lowest>-?\d+))?
        $""",
        dice_expression,
        re.IGNORECASE | re.VERBOSE)

    dice_num = int(result.group('dice_num') or 1)
    dice_type = int(result.group('dice_type'))

    # Dice can't have zero or a negative number of sides.
    if dice_type <= 0:
        bot.reply("I don't have any dice with %d sides. =(" % dice_type)
        return None  # Signal there was a problem

    # Can't roll a negative number of dice.
    if dice_num < 0:
        bot.reply("I'd rather not roll a negative amount of dice. =(")
        return None  # Signal there was a problem

    # Upper limit for dice should be at most a million. Creating a dict with
    # more than a million elements already takes a noticeable amount of time
    # on a fast computer and ~55kB of memory.
    if dice_num > 1000:
        bot.reply('I only have 1000 dice. =(')
        return None  # Signal there was a problem

    dice = DicePouch(dice_num, dice_type, 0)

    if result.group('drop_lowest'):
        drop = int(result.group('drop_lowest'))
        if drop >= 0:
            dice.drop_lowest(drop)
        else:
            bot.reply("I can't drop the lowest %d dice. =(" % drop)

    return dice


@sopel.module.commands("roll")
@sopel.module.commands("dice")
@sopel.module.commands("d")
@sopel.module.priority("medium")
@sopel.module.example(".roll 3d1+1", 'You roll 3d1+1: (1+1+1)+1 = 4')
@sopel.module.example(".roll 3d1v2+1", 'You roll 3d1v2+1: (1[+1+1])+1 = 2')
@sopel.module.example(".roll 2d4", r'You roll 2d4: \(\d\+\d\) = \d', re=True, user_help=True)
@sopel.module.example(".roll 100d1", r'[^:]*: \(100x1\) = 100', re=True)
@sopel.module.example(".roll 1001d1", 'I only have 1000 dice. =(')
@sopel.module.example(".roll 1d1 + 1d1", 'You roll 1d1 + 1d1: (1) + (1) = 2')
@sopel.module.example(".roll 1d1+1d1", 'You roll 1d1+1d1: (1)+(1) = 2')
@sopel.module.example(".roll 1d6 # initiative", r'You roll 1d6: \(\d\) = \d', re=True)
def roll(bot, trigger):
    """.dice XdY[vZ][+N][#COMMENT], rolls dice and reports the result.

    X is the number of dice. Y is the number of faces in the dice. Z is the
    number of lowest dice to be dropped from the result. N is the constant to
    be applied to the end result. Comment is for easily noting the purpose.
    """
    # This regexp is only allowed to have one capture group, because having
    # more would alter the output of re.findall.
    dice_regexp = r"-?\d*[dD]-?\d+(?:[vV]-?\d+)?"

    # Get a list of all dice expressions, evaluate them and then replace the
    # expressions in the original string with the results. Replacing is done
    # using string formatting, so %-characters must be escaped.
    if not trigger.group(2):
        return bot.reply("No dice to roll.")
    arg_str_raw = trigger.group(2).split("#", 1)[0].strip()
    dice_expressions = re.findall(dice_regexp, arg_str_raw)
    arg_str = arg_str_raw.replace("%", "%%")
    arg_str = re.sub(dice_regexp, "%s", arg_str)

    def f(dice_expr):
        return _roll_dice(bot, dice_expr)

    dice = list(map(f, dice_expressions))

    if None in dice:
        # Stop computing roll if there was a problem rolling dice.
        return

    def _get_eval_str(dice):
        return "(%d)" % (dice.get_sum(),)

    def _get_pretty_str(dice):
        if dice.num <= 10:
            return dice.get_simple_string()
        elif dice.get_number_of_faces() <= 10:
            return dice.get_compressed_string()
        else:
            return "(...)"

    eval_str = arg_str % (tuple(map(_get_eval_str, dice)))
    pretty_str = arg_str % (tuple(map(_get_pretty_str, dice)))

    try:
        result = eval_equation(eval_str)
    except TypeError:
        bot.reply(
            "The type of this equation is, apparently, not a string. "
            "How did you do that, anyway?"
        )
    except ValueError:
        # As it seems that ValueError is raised if the resulting equation would
        # be too big, give a semi-serious answer to reflect on this.
        bot.reply("You roll %s: %s = very big" % (
            arg_str_raw, pretty_str))
        return
    except (SyntaxError, eval_equation.Error):
        bot.reply(
            "I don't know how to process that. "
            "Are the dice as well as the algorithms correct?"
        )
        return

    bot.reply("You roll %s: %s = %d" % (
        arg_str_raw, pretty_str, result))


if __name__ == "__main__":
    from sopel.test_tools import run_example_tests
    run_example_tests(__file__)
