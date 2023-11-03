"""Tests Sopel's calculation tools"""
from __future__ import annotations

import ast
import operator

import pytest

from sopel.tools.calculation import EquationEvaluator, ExpressionEvaluator


def test_expression_eval():
    """Ensure ExpressionEvaluator respects limited operator set."""
    OPS = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
    }
    evaluator = ExpressionEvaluator(bin_ops=OPS)

    assert evaluator("1 + 1") == 2
    assert evaluator("43 - 1") == 42
    assert evaluator("1 + 1 - 2") == 0

    with pytest.raises(ExpressionEvaluator.Error) as exc:
        evaluator("2 * 2")
    assert "Unsupported binary operator" in exc.value.args[0]

    with pytest.raises(ExpressionEvaluator.Error) as exc:
        evaluator("~2")
    assert "Unsupported unary operator" in exc.value.args[0]


def test_equation_eval_invalid_constant():
    """Ensure unsupported constants are rejected."""
    evaluator = EquationEvaluator()

    with pytest.raises(ExpressionEvaluator.Error) as exc:
        evaluator("2 + 'string'")
    assert "values are not supported" in exc.value.args[0]


def test_equation_eval_timeout():
    """Ensure EquationEvaluator times out as expected."""
    # timeout is added to the current time;
    # negative means the timeout is "reached" before even starting
    timeout = -1.0
    evaluator = EquationEvaluator()

    with pytest.raises(ExpressionEvaluator.Error) as exc:
        evaluator("1000000**100", timeout)
    assert "Time for evaluating" in exc.value.args[0]

    with pytest.raises(ExpressionEvaluator.Error) as exc:
        evaluator("+42", timeout)
    assert "Time for evaluating" in exc.value.args[0]


def test_equation_eval():
    """Test that EquationEvaluator correctly parses input and calculates results."""
    evaluator = EquationEvaluator()

    assert evaluator("1 + 1") == 2
    assert evaluator("43 - 1") == 42
    assert evaluator("(((1 + 1 + 2) * 3 / 5) ** 8 - 13) // 21 % 35") == 16.0
    assert evaluator("-42") == -42
    assert evaluator("-(-42)") == 42
    assert evaluator("+42") == 42
    assert evaluator("3 ^ 2") == 9
