#!/usr/bin/env python2.7
# coding=utf8
"""
Class-based wrapper around dmbot parser
"""
from __future__ import unicode_literals
from __future__ import print_function

from parser import *

class Dice(object):
    """
    OOP front for the methods in parser which handle the creation of the tree
    structure automatically.
    """

    def __init__(self, string="0"):
        """
        Default constructor. If the string parameter is specified it will
        initialise it with a constructed AST ready for evaluation, otherwise it
        will be evaluated with the string '0'.

        Optional:
        string  --  Dicebot expression to use to construct this dice expression
                    object.
        """
        self.tree = 0
        self.set_string(string)
        return

    def set_string(self, string):
        """
        Explicitly set the dice-spec that this Dice object represents.

        string  --  Dicebot expression to use to construct this expressions' AST
                    from.
        """
        self._string = string
        self.tree = make_tree(string)
        return self

    @property
    def string(self):
        """
        The dice-spec currently loaded into this object.
        """
        return self._string

    @property
    def roll(self):
        """
        Evaluates the dice-spec this object represents and returns a numerical
        value.
        """
        return evaluate_tree(self.tree)

