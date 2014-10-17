#!/usr/bin/env python2.7
# coding=utf8
from __future__ import unicode_literals
from __future__ import print_function

from unittest import TestCase

from dice import Dice

class TestDice(TestCase):

    def test_dice(self):
        dice = Dice("d20")
        roll = dice.roll
        assert roll >= 1, dice
        assert roll <= 20, dice
        return
