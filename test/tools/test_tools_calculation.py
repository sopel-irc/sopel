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

    with pytest.raises(ExpressionEvaluator.Error):
        evaluator("2 * 2")


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
