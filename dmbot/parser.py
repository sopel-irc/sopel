#!/usr/bin/env python2.7
# coding=utf8
"""
Implementation of DMBot style dice specification language and math parser.
"""
from __future__ import unicode_literals
from __future__ import print_function

from parsley import *
import random


grammar = makeGrammar("""

Digit = :x ?(x in '0123456789') -> x
Integer = <Digit+>:x -> int(x)
Decimal = (Integer:i '.' Integer:f -> float("%d.%d" % (i,f))) | (Integer:i -> int(i))
SIForm = Decimal:a 'e' Decimal:b -> a * 10**b
Number = SIForm | Decimal | ('-' SIForm:x -> -1*x) | ('-' Decimal:x -> -1*x)
Letter = :x ?(x in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXY') -> x


Dice = (Integer:a 'd' Integer:b <Letter*>:mod ws -> ('d'+mod, a, b)) | ('d' Integer:a <Letter*>:mod ws -> ('d'+mod, 1, a))
Terminal = Dice | Number

Paren = ('(' ws Expression:a ws ')' ws -> a) | Terminal

Division = (Paren:a ws '/' ws Division:b ws -> ('/', a, b)) | Paren
Multiplication = (Division:a ws '*' ws Multiplication:b ws -> ('*', a, b)) | Division

Addition = (Multiplication:a ws '+' ws Addition:b ws -> ('+', a, b))  | Multiplication
Subtraction = (Addition:a ws '-' ws Subtraction:b ws -> ('-', a, b)) | Addition
Subexpression = Subtraction
Series = Subexpression:a ws ',' ws Subexpression:b ws -> (',', a, b)
Expression = Series | Subexpression

""", {})

def roll_dice(num, size):
    """
    Roll a number of dice using Python's singleton random module.

    num     --  The number of dice to roll
    size    --  The number of sides on the dice, which will be assumed to be 
                marked 1 through size.
    """
    return [ random.randint(1,size) for _ in range(num) ]


def node_type(tree):
    """
    Queries what type of AST node is at the head of the tree i.e. addition,
    subtraction or multiplication. Each such type is represented by the first
    character of a string: with any additional characters reserved for arguments
    and flags to be used when resolving that node into a numerical type.

    tree    --  A 3-tuple representing a binary tree node.
    """
    (a,_,_) = tree
    return a[0]

def floating_reroll(mutable, die_size):
    """
    Recursively implements floating re-rolls or 'exploding' dice.

    mutable     --  A list containing a single numerical value, used as a hack
                    to allow mutability.
    die_size    --  The size of the dice to rolled.
    """
    if (mutable[0] % die_size) == 0:
        mutable[0] += roll_dice(1,die_size)[0]
        floating_reroll(mutable, die_size)
    return mutable
        
def evaluate_dice(tree):
    """
    Resolve a 3-tuple binary tree representing a dice-throw into a single
    'throw' of the dice as a numerical value.

    tree    --  3-tuple binary tree representing the dice-specification. Left
                branch is the number of dice, right branch is the size of those
                dice.
    """
    (mods, left, right) = tree
    mods = mods.lower()
    left = evaluate_tree(left)
    right = evaluate_tree(right)
    dice = roll_dice(left, right)
    drop_lowest = mods.count('l')
    floating_rerolls = mods.count('f')
    if floating_rerolls > 0:
        for i in range(len(dice) ):
            mutable = [ dice[i] ]
            floating_reroll(mutable, right)
            dice[i] = mutable[0]
    if drop_lowest > 0:
        dice = sorted(dice)
        for _ in range(drop_lowest):
            dice.pop(0)
    return sum(dice)

def evaluate_add(tree):
    """
    Resolve a 3-tuple binary tree representation of an addition operation into
    a numerical value representing the value.

    tree    --  3-tuple binary tree representing the addition.
    """
    (_, left, right) = tree
    left = evaluate_tree(left)
    right = evaluate_tree(right)
    return left + right

def evaluate_sub(tree):
    """
    Resolve a 3-tuple binary tree represention of a subtraction operation into
    a numerical value representing the value.

    tree    -- 3-tuple binary tree representing the subtraction.
    """
    (_, left, right) = tree
    left = evaluate_tree(left)
    right = evaluate_tree(right)
    return left - right

def evaluate_mult(tree):
    """
    Resolve a 3-tuple binary tree representation of a multiplication operation
    into a numerical value representing the value.

    tree    --  3-tuple binary tree representing the multiplication.
    """
    (_, left, right) = tree
    left = evaluate_tree(left)
    right = evaluate_tree(right)
    return left * right

def evaluate_div(tree):
    """
    Resolve a 3-tuple binary tree representation of a division operation into a
    numerical value representing the value.

    tree    --  3-tuple binary tree representing the multiplication.
    """
    (_, left, right) = tree
    left = evaluate_tree(left)
    right = evaluate_tree(right)
    return left / right

def evaluate_series(tree):
    """
    Resolve a 3-tuple binary tree representation of a series, or repetition of
    operations, into a python list representing the numerical values of each
    evaluation of the left-head operation.

    tree    --  3-tuple binary tree representing the series, left branch is the
                statement to repeat, right branch is the number of repetitions.
    """
    (_, left, right) = tree
    right = evaluate_tree(right)
    return [ evaluate_tree(left) for _ in range(right) ]

"""
Dict for binding the node-type to the function used to resolve it numerically.
"""
eval_bindings = {
        'd': evaluate_dice,
        '+': evaluate_add,
        '-': evaluate_sub,
        '*': evaluate_mult,
        '/': evaluate_div,
        ',': evaluate_series
}
        

def make_tree(string):
    """
    Construct a 3-tuple binary tree representing an AST from a string. Uses the
    parsley grammar defined in global variable grammar.

    string  --  The string to translate.
    """
    return grammar(string).Expression()

def evaluate_tree(tree):
    """
    Evaluate a 3-tuple binary tree represnting an AST into a numerical value.
    """
    if isinstance(tree, int) or isinstance(tree, float):
        return tree
    if isinstance(tree, tuple):
        return eval_bindings[node_type(tree)](tree)

