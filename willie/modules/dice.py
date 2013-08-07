"""
dice.py - Dice Module
Copyright 2010-2013, Dimitri "Tyrope" Molenaars, TyRope.nl
Copyright 2013, Ari Koivula, <ari@koivu.la>
Licensed under the Eiffel Forum License 2.

http://willie.dftba.net/
"""

import random
import willie.module
import re


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
        for __ in xrange(self.num):
            number = random.randint(1, self.type)
            count = self.dice.setdefault(number, 0)
            self.dice[number] = count + 1

    def drop_lowest(self, n):
        """Drop n lowest dice from the result.

        Args:
            n: the number of dice to drop.
        """
        for i in xrange(1, self.type + 1):
            count = self.dice[i]
            if n < count:
                self.dice[i] = count - n
                self.dropped[i] = n
                break
            else:
                del self.dice[i]
                self.dropped[i] = count
                n = n - count

    def get_simple_string(self):
        """Return the values of the dice like (2+2+2[+1+1])+1."""
        dice = self.dice.iteritems()
        faces = ("+".join([str(face)] * times) for face, times in dice)
        dice_str = "+".join(faces)

        dropped_str = ""
        if self.dropped:
            dropped = self.dropped.iteritems()
            dfaces = ("+".join([str(face)] * times) for face, times in dropped)
            dropped_str = "[+%s]" % ("+".join(dfaces),)

        plus_str = ""
        if self.addition:
            plus_str = "{:+d}".format(self.addition)

        return "(%s%s)%s" % (dice_str, dropped_str, plus_str)

    def get_compressed_string(self):
        """Return the values of the dice like (3x2[+2x1])+1."""
        dice = self.dice.iteritems()
        faces = ("%dx%d" % (times, face) for face, times in dice)
        dice_str = "+".join(faces)

        dropped_str = ""
        if self.dropped:
            dropped = self.dropped.iteritems()
            dfaces = ("%dx%d" % (times, face) for face, times in dropped)
            dropped_str = "[+%s]" % ("+".join(dfaces),)

        plus_str = ""
        if self.addition:
            plus_str = "{:+d}".format(self.addition)

        return "(%s%s)%s" % (dice_str, dropped_str, plus_str)

    def get_sum(self):
        """Get the sum of non-dropped dice and the addition."""
        result = self.addition
        for face, times in self.dice.iteritems():
            result += face * times
        return result

    def get_number_of_faces(self):
        """Returns sum of different faces for dropped and not dropped dice

        This can be used to estimate, whether the result can be shown in
        compressed form in a reasonable amount of space.
        """
        return len(self.dice) + len(self.dropped)


@willie.module.commands("roll")
@willie.module.commands("dice")
@willie.module.commands("d")
@willie.module.priority("medium")
@willie.module.example(".roll 3d1+1", 'You roll 3d1+1: (1+1+1)+1 = 4')
@willie.module.example(".roll 3d1v2+1", 'You roll 3d1v2+1: (1[+1+1])+1 = 2')
@willie.module.example(".roll 2d4", re='You roll 2d4: \(\d\+\d\) = \d')
@willie.module.example(".roll 100d1", re='[^:]*: \(100x1\) = 100')
def roll(bot, trigger):
    """.dice XdY[vZ][+N], rolls dice and reports the result.

    X is the number of dice. Y is the number of faces in the dice. Z is the
    number of lowest dice to be dropped from the result. N is the constant to
    be applied to the end result.
    """
    result = re.search(r"""
            (?P<dice_num>\d+)
            d
            (?P<dice_type>\d+)
            (v(?P<drop_lowest>\d+))?
            (?P<plus>(-|\+)\d+)?
            $""",
            trigger.group(2),
            re.IGNORECASE | re.VERBOSE)
    if not result:
        bot.reply("Syntax for rolling dice is XdY[vZ][+N].")
        return

    dice_num = int(result.group('dice_num'))
    dice_type = int(result.group('dice_type'))
    addition = int(result.group('plus') or 0)

    # Upper limit for dice should be at most a million. Creating a dict with
    # more than a million elements already takes a noticeable amount of time
    # on a fast computer and ~55kB of memory.
    if dice_num > 1000:
        bot.reply("I only have 1000 dice. =(")
        return

    dice = DicePouch(dice_num, dice_type, addition)

    if result.group('drop_lowest'):
        drop = int(result.group('drop_lowest'))
        dice.drop_lowest(drop)

    if dice_num <= 10:
        dice_str = dice.get_simple_string()
    elif dice.get_number_of_faces() <= 10:
        dice_str = dice.get_compressed_string()
    else:
        dice_str = "(...)"

    bot.reply("You roll %s: %s = %d" % (
            trigger.group(2), dice_str, dice.get_sum()))


@willie.module.commands("choice")
@willie.module.commands("ch")
@willie.module.commands("choose")
@willie.module.priority("medium")
def choose(bot, trigger):
    """
    .choice option1|option2|option3 - Makes a difficult choice easy.
    """
    if not trigger.group(2):
        return bot.reply('I\'d choose an option, but you didn\'t give me any.')
    choices = re.split('[\|\\\\\/]', trigger.group(2))
    pick = random.choice(choices)
    return bot.reply('Your options: %s. My choice: %s' % (', '.join(choices), pick))


if __name__ == "__main__":
    from willie.test_tools import run_example_tests
    run_example_tests(__file__)
