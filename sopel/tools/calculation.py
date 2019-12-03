# coding=utf-8
"""Tools to help safely do calculations from user input"""
from __future__ import unicode_literals, absolute_import, print_function, division

import time
import numbers
import operator
import ast

__all__ = ['eval_equation']


class ExpressionEvaluator:
    """A generic class for evaluating limited forms of Python expressions.

    :param dict bin_ops: optional; see notes
    :param dict unary_ops: optional; see notes

    Instances can pass ``binary_ops`` and ``unary_ops`` arguments with dicts of
    the form ``{ast.Node, function}``. When the :class:`ast.Node <ast.AST>` used
    as key is found, it will be evaluated using the given ``function``.
    """

    class Error(Exception):
        """Internal exception type for :class:`ExpressionEvaluator`\\s."""
        pass

    def __init__(self, bin_ops=None, unary_ops=None):
        self.binary_ops = bin_ops or {}
        self.unary_ops = unary_ops or {}

    def __call__(self, expression_str, timeout=5.0):
        """Evaluate a Python expression and return the result.

        :param str expression_str: the expression to evaluate
        :raise SyntaxError: if the given ``expression_str`` is not a valid
                            Python statement
        :raise ExpressionEvaluator.Error: if the instance of
            :class:`ExpressionEvaluator` does not have a handler for the
            :class:`ast.Node <ast.AST>`
        """
        ast_expression = ast.parse(expression_str, mode='eval')
        return self._eval_node(ast_expression.body, time.time() + timeout)

    def _eval_node(self, node, timeout):
        """Recursively evaluate the given :class:`ast.Node <ast.AST>`.

        :param node: the AST node to evaluate
        :type node: :class:`ast.AST`
        :param timeout: how long the expression is allowed to process before
                        timing out and failing
        :type timeout: int or float
        :raise ExpressionEvaluator.Error: if it can't handle the ``node``

        Uses :attr:`self.binary_ops` and :attr:`self.unary_ops` for the
        implementation.

        A subclass could overwrite this to handle more nodes, calling it only
        for nodes it does not implement itself.
        """
        if isinstance(node, ast.Num):
            return node.n

        elif (isinstance(node, ast.BinOp) and
                type(node.op) in self.binary_ops):
            left = self._eval_node(node.left, timeout)
            right = self._eval_node(node.right, timeout)
            if time.time() > timeout:
                raise ExpressionEvaluator.Error(
                    "Time for evaluating expression ran out.")
            return self.binary_ops[type(node.op)](left, right)

        elif (isinstance(node, ast.UnaryOp) and
                type(node.op) in self.unary_ops):
            operand = self._eval_node(node.operand, timeout)
            if time.time() > timeout:
                raise ExpressionEvaluator.Error(
                    "Time for evaluating expression ran out.")
            return self.unary_ops[type(node.op)](operand)

        raise ExpressionEvaluator.Error(
            "Ast.Node '%s' not implemented." % (type(node).__name__,))


def guarded_mul(left, right):
    """Multiply two values, guarding against overly large inputs.

    :param left: the left operand
    :type left: int or float
    :param right: the right operand
    :type right: int or float
    :raise ValueError: if the inputs are too large to handle safely
    """
    # Only handle ints because floats will overflow anyway.
    if not isinstance(left, numbers.Integral):
        pass
    elif not isinstance(right, numbers.Integral):
        pass
    elif left in (0, 1) or right in (0, 1):
        # Ignore trivial cases.
        pass
    elif left.bit_length() + right.bit_length() > 664386:
        # 664386 is the number of bits (10**100000)**2 has, which is instant on
        # my laptop, while (10**1000000)**2 has a noticeable delay. It could
        # certainly be improved.
        raise ValueError(
            "Value is too large to be handled in limited time and memory.")

    return operator.mul(left, right)


def pow_complexity(num, exp):
    """Estimate the worst case time :func:`pow` takes to calculate.

    :param num: base
    :type num: int or float
    :param exp: exponent
    :type exp: int or float

    This function is based on experimental data from the time it takes to
    calculate ``num**exp`` in 32-bit CPython 2.7.6 on an Intel Core i7-2670QM
    laptop running Windows.

    It tries to implement this surface: x=exp, y=num

    +----+------+------+------+------+-------+-------+-------+-------+-------+
    |    |  1e5 |  2e5 |  3e5 |  4e5 |  5e5  |  6e5  |  7e5  |  8e5  |  9e5  |
    +====+======+======+======+======+=======+=======+=======+=======+=======+
    | e1 | 0.03 | 0.09 | 0.16 | 0.25 |  0.35 |  0.46 |  0.60 |  0.73 |  0.88 |
    +----+------+------+------+------+-------+-------+-------+-------+-------+
    | e2 | 0.08 | 0.24 | 0.46 | 0.73 |  1.03 |  1.40 |  1.80 |  2.21 |  2.63 |
    +----+------+------+------+------+-------+-------+-------+-------+-------+
    | e3 | 0.15 | 0.46 | 0.87 | 1.39 |  1.99 |  2.63 |  3.35 |  4.18 |  5.15 |
    +----+------+------+------+------+-------+-------+-------+-------+-------+
    | e4 | 0.24 | 0.73 | 1.39 | 2.20 |  3.11 |  4.18 |  5.39 |  6.59 |  7.88 |
    +----+------+------+------+------+-------+-------+-------+-------+-------+
    | e5 | 0.34 | 1.03 | 2.00 | 3.12 |  4.48 |  5.97 |  7.56 |  9.37 | 11.34 |
    +----+------+------+------+------+-------+-------+-------+-------+-------+
    | e6 | 0.46 | 1.39 | 2.62 | 4.16 |  5.97 |  7.86 | 10.09 | 12.56 | 15.39 |
    +----+------+------+------+------+-------+-------+-------+-------+-------+
    | e7 | 0.60 | 1.79 | 3.34 | 5.39 |  7.60 | 10.16 | 13.00 | 16.23 | 19.44 |
    +----+------+------+------+------+-------+-------+-------+-------+-------+
    | e8 | 0.73 | 2.20 | 4.18 | 6.60 |  9.37 | 12.60 | 16.26 | 19.83 | 23.70 |
    +----+------+------+------+------+-------+-------+-------+-------+-------+
    | e9 | 0.87 | 2.62 | 5.15 | 7.93 | 11.34 | 15.44 | 19.40 | 23.66 | 28.58 |
    +----+------+------+------+------+-------+-------+-------+-------+-------+

    For powers of 2 it tries to implement this surface:

    +---+------+------+------+------+------+------+------+------+------+
    |   |  1e7 |  2e7 |  3e7 |  4e7 |  5e7 |  6e7 |  7e7 |  8e7 |  9e7 |
    +===+======+======+======+======+======+======+======+======+======+
    | 1 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
    +---+------+------+------+------+------+------+------+------+------+
    | 2 | 0.21 | 0.44 | 0.71 | 0.92 | 1.20 | 1.49 | 1.66 | 1.95 | 2.23 |
    +---+------+------+------+------+------+------+------+------+------+
    | 4 | 0.43 | 0.91 | 1.49 | 1.96 | 2.50 | 3.13 | 3.54 | 4.10 | 4.77 |
    +---+------+------+------+------+------+------+------+------+------+
    | 8 | 0.70 | 1.50 | 2.24 | 3.16 | 3.83 | 4.66 | 5.58 | 6.56 | 7.67 |
    +---+------+------+------+------+------+------+------+------+------+

    The function numbers were selected by starting with the theoretical
    complexity of ``exp * log2(num)**2`` and fiddling with the exponents
    until it more or less matched with the table.

    Because this function is based on a limited set of data it might not give
    accurate results outside these boundaries. The results derived from large
    ``num`` and ``exp`` were quite accurate for small ``num`` and very large
    ``exp`` though, except when ``num`` was a power of 2.
    """
    if num in (0, 1) or exp in (0, 1):
        return 0
    elif (num & (num - 1)) == 0:
        # For powers of 2 the scaling is a bit different.
        return exp ** 1.092 * num.bit_length() ** 1.65 / 623212911.121
    else:
        return exp ** 1.590 * num.bit_length() ** 1.73 / 36864057619.3


def guarded_pow(num, exp):
    """Raise a number to a power, guarding against overly large inputs.

    :param num: base
    :type num: int or float
    :param exp: exponent
    :type exp: int or float
    :raise ValueError: if the inputs are too large to handle safely
    """
    # Only handle ints because floats will overflow anyway.
    if not isinstance(num, numbers.Integral):
        pass
    elif not isinstance(exp, numbers.Integral):
        pass
    elif pow_complexity(num, exp) < 0.5:
        # Value 0.5 is arbitrary and based on an estimated runtime of 0.5s
        # on a fairly decent laptop processor.
        pass
    else:
        raise ValueError("Pow expression too complex to calculate.")

    return operator.pow(num, exp)


class EquationEvaluator(ExpressionEvaluator):
    __bin_ops = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: guarded_mul,
        ast.Div: operator.truediv,
        ast.Pow: guarded_pow,
        ast.Mod: operator.mod,
        ast.FloorDiv: operator.floordiv,
        ast.BitXor: guarded_pow
    }
    __unary_ops = {
        ast.USub: operator.neg,
        ast.UAdd: operator.pos,
    }

    def __init__(self):
        ExpressionEvaluator.__init__(
            self,
            bin_ops=self.__bin_ops,
            unary_ops=self.__unary_ops
        )

    def __call__(self, expression_str):
        result = ExpressionEvaluator.__call__(self, expression_str)

        # This wrapper is here so additional sanity checks could be done
        # on the result of the eval, but currently none are done.

        return result


eval_equation = EquationEvaluator()
"""Evaluates a Python equation expression and returns the result.

:param str equation: the equation to evaluate
:param timeout: optional timeout value
:type timeout: int or float

Supports addition (+), subtraction (-), multiplication (*), division (/),
power (**) and modulo (%).
"""
