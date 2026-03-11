"""
dice.py - Sopel Dice Plugin
Copyright 2010-2013, Dimitri "Tyrope" Molenaars, TyRope.nl
Copyright 2013, Ari Koivula, <ari@koivu.la>
Licensed under the Eiffel Forum License 2.

https://sopel.chat
"""
from __future__ import annotations

import operator
import random
import re
from typing import TYPE_CHECKING

from sopel import plugin
from sopel.tools.calculation import eval_equation


if TYPE_CHECKING:
    from sopel.bot import SopelWrapper
    from sopel.trigger import Trigger


MAX_DICE = 1000


class DicePouch:
    def __init__(self, dice_count: int, dice_type: int) -> None:
        """Initialize dice pouch and roll the dice.

        :param dice_count: the number of dice in the pouch
        :param dice_type: how many faces each die has
        """
        self.num: int = dice_count
        self.type: int = dice_type

        self.dice: dict[int, int] = {}
        self.dropped: dict[int, int] = {}

        self.roll_dice()

    def roll_dice(self) -> None:
        """Roll all the dice in the pouch."""
        self.dice = {}
        self.dropped = {}
        for __ in range(self.num):
            number = random.randint(1, self.type)
            count = self.dice.setdefault(number, 0)
            self.dice[number] = count + 1

    def drop_lowest(self, n: int) -> None:
        """Drop ``n`` lowest dice from the result.

        :param n: the number of dice to drop
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

    def get_simple_string(self) -> str:
        """Return the values of the dice like (2+2+2[+1+1])."""
        dice = self.dice.items()
        faces = ("+".join([str(face)] * times) for face, times in dice)
        dice_str = "+".join(faces)

        dropped_str = ""
        if self.dropped:
            dropped = self.dropped.items()
            dfaces = ("+".join([str(face)] * times) for face, times in dropped)
            dropped_str = "[+%s]" % ("+".join(dfaces),)

        return "(%s%s)" % (dice_str, dropped_str)

    def get_compressed_string(self) -> str:
        """Return the values of the dice like (3x2[+2x1])."""
        dice = self.dice.items()
        faces = ("%dx%d" % (times, face) for face, times in dice)
        dice_str = "+".join(faces)

        dropped_str = ""
        if self.dropped:
            dropped = self.dropped.items()
            dfaces = ("%dx%d" % (times, face) for face, times in dropped)
            dropped_str = "[+%s]" % ("+".join(dfaces),)

        return "(%s%s)" % (dice_str, dropped_str)

    def get_sum(self) -> int:
        """Get the sum of non-dropped dice."""
        result = 0
        for face, times in self.dice.items():
            result += face * times
        return result

    def get_number_of_faces(self) -> int:
        """Returns sum of different faces for dropped and not dropped dice.

        This can be used to estimate whether the result can be shown (in
        compressed form) in a reasonable amount of space.
        """
        return len(self.dice) + len(self.dropped)


class DiceError(Exception):
    """Custom base exception type."""


class InvalidDiceFacesError(DiceError):
    """Custom exception type for invalid number of die faces."""
    def __init__(self, faces: int):
        super().__init__(faces)

    @property
    def faces(self) -> int:
        return self.args[0]


class NegativeDiceCountError(DiceError):
    """Custom exception type for invalid numbers of dice."""
    def __init__(self, count: int):
        super().__init__(count)

    @property
    def count(self) -> int:
        return self.args[0]


class TooManyDiceError(DiceError):
    """Custom exception type for excessive numbers of dice."""
    def __init__(self, requested: int, available: int):
        super().__init__(requested, available)

    @property
    def available(self) -> int:
        return self.args[1]

    @property
    def requested(self) -> int:
        return self.args[0]


class UnableToDropDiceError(DiceError):
    """Custom exception type for failing to drop lowest N dice."""
    def __init__(self, dropped: int, total: int):
        super().__init__(dropped, total)

    @property
    def dropped(self) -> int:
        return self.args[0]

    @property
    def total(self) -> int:
        return self.args[1]


def _get_error_message(exc: DiceError) -> str:
    if isinstance(exc, InvalidDiceFacesError):
        return "I don't have any dice with {} sides.".format(exc.faces)
    if isinstance(exc, NegativeDiceCountError):
        return "I can't roll {} dice.".format(exc.count)
    if isinstance(exc, TooManyDiceError):
        return "I only have {}/{} dice.".format(exc.available, exc.requested)
    if isinstance(exc, UnableToDropDiceError):
        return "I can't drop the lowest {} of {} dice.".format(
            exc.dropped, exc.total)

    return "Unknown error rolling dice: %r" % exc


def _roll_dice(dice_match: re.Match[str]) -> DicePouch:
    dice_num = int(dice_match.group('dice_num') or 1)
    dice_type = int(dice_match.group('dice_type'))

    # Dice can't have zero or a negative number of sides.
    if dice_type <= 0:
        raise InvalidDiceFacesError(dice_type)

    # Can't roll a negative number of dice.
    if dice_num < 0:
        raise NegativeDiceCountError(dice_num)

    # Upper limit for dice should be at most a million. Creating a dict with
    # more than a million elements already takes a noticeable amount of time
    # on a fast computer and ~55kB of memory.
    if dice_num > MAX_DICE:
        raise TooManyDiceError(dice_num, MAX_DICE)

    dice = DicePouch(dice_num, dice_type)

    if dice_match.group('drop_lowest'):
        drop = int(dice_match.group('drop_lowest'))
        if drop >= 0:
            dice.drop_lowest(drop)
        else:
            raise UnableToDropDiceError(drop, dice_num)

    return dice


@plugin.command('roll', 'dice', 'd')
@plugin.priority(plugin.Priority.MEDIUM)
@plugin.example(".roll", "No dice to roll.")
@plugin.example(".roll 2d6+4^2&",
                "I don't know how to process that. "
                "Are the dice as well as the algorithms correct?")
@plugin.example(".roll 65(2)", "I couldn't find any valid dice expressions.")
@plugin.example(".roll 2d-2", "I don't have any dice with -2 sides.")
@plugin.example(".roll 1d0", "I don't have any dice with 0 sides.")
@plugin.example(".roll -1d6", "I can't roll -1 dice.")
@plugin.example(".roll 3d6v-1", "I can't drop the lowest -1 of 3 dice.")
@plugin.example(".roll 2d6v0", r'2d6v0: \(\d\+\d\) = \d+', re=True)
@plugin.example(".roll 2d6v4", r'2d6v4: \(\[\+\d\+\d\]\) = 0', re=True)
@plugin.example(".roll 2d6v1+8", r'2d6v1\+8: \(\d\[\+\d\]\)\+8 = \d+', re=True)
@plugin.example(".roll 11d1v1", "11d1v1: (10x1[+1x1]) = 10")
@plugin.example(".roll 3d1+1", '3d1+1: (1+1+1)+1 = 4')
@plugin.example(".roll 3d1v2+1", '3d1v2+1: (1[+1+1])+1 = 2')
@plugin.example(".roll 2d4", r'2d4: \(\d\+\d\) = \d', re=True)
@plugin.example(".roll 100d1", r'[^:]*: \(100x1\) = 100', re=True)
@plugin.example(".roll 100d100", r'100d100: \(\.{3}\) = \d+', re=True)
@plugin.example(".roll 1000d999^1000d999", 'You roll 1000d999^1000d999: (...)^(...) = very big')
@plugin.example(".roll 1000d999^1000d99", "I can't display a number that big. =(")
@plugin.example(
    ".roll {}d1".format(MAX_DICE + 1), 'I only have {}/{} dice.'.format(MAX_DICE, MAX_DICE + 1))
@plugin.example(".roll 1d1 + 1d1", '1d1 + 1d1: (1) + (1) = 2')
@plugin.example(".roll 1d1+1d1", '1d1+1d1: (1)+(1) = 2')
@plugin.example(".roll d6 # initiative", r'd6: \(\d\) = \d', re=True)
@plugin.example(".roll 2d20v1+2 # roll with advantage", user_help=True)
@plugin.example(".roll 2d10+3", user_help=True)
@plugin.example(".roll 1d6", user_help=True)
@plugin.output_prefix('[dice] ')
def roll(bot: SopelWrapper, trigger: Trigger) -> None:
    """Rolls dice and reports the result.

    The dice roll follows this format: XdY[vZ][+N][#COMMENT]

    X is the number of dice. Y is the number of faces in the dice. Z is the
    number of lowest dice to be dropped from the result. N is the constant to
    be applied to the end result. Comment is for easily noting the purpose.
    """
    dice_regexp = r"""
        (?P<dice_num>-?\d*)
        d
        (?P<dice_type>-?\d+)
        (v(?P<drop_lowest>-?\d+))?
    """

    # Get a list of all dice expressions, evaluate them and then replace the
    # expressions in the original string with the results. Replacing is done
    # using string formatting, so %-characters must be escaped.
    if not trigger.group(2):
        bot.reply("No dice to roll.")
        return

    arg_str_raw = trigger.group(2).split("#", 1)[0].strip()
    arg_str = arg_str_raw.replace("%", "%%")
    arg_str = re.sub(
        dice_regexp, "%s", arg_str,
        flags=re.IGNORECASE | re.VERBOSE)

    dice_expressions = [
        match for match in
        re.finditer(dice_regexp, arg_str_raw, re.IGNORECASE | re.VERBOSE)
    ]

    if not dice_expressions:
        bot.reply("I couldn't find any valid dice expressions.")
        return

    try:
        dice = [_roll_dice(dice_expr) for dice_expr in dice_expressions]
    except DiceError as err:
        # Stop computing roll if there was a problem rolling dice.
        bot.reply(_get_error_message(err))
        return

    def _get_eval_str(dice: DicePouch) -> str:
        return "(%d)" % (dice.get_sum(),)

    def _get_pretty_str(dice: DicePouch) -> str:
        if dice.num <= 10:
            return dice.get_simple_string()
        elif dice.get_number_of_faces() <= 10:
            return dice.get_compressed_string()
        else:
            return "(...)"

    eval_str: str = arg_str % (tuple(map(_get_eval_str, dice)))
    pretty_str: str = arg_str % (tuple(map(_get_pretty_str, dice)))

    try:
        result = eval_equation(eval_str)
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

    try:
        bot.say("%s: %s = %d" % (arg_str_raw, pretty_str, result))
    except ValueError:
        # Converting the result to a string can also raise ValueError if it has
        # more than int_max_str_digits digits (4300 by default on CPython)
        # See https://docs.python.org/3.12/library/stdtypes.html#int-max-str-digits
        bot.reply("I can't display a number that big. =(")
