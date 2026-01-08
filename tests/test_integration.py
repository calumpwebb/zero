"""
End-to-end integration tests for the Zero language.
These tests run the full pipeline: source → lexer → parser → semantic → compiler → vm
"""

import pytest
from zero.lexer import tokenize
from zero.parser import parse
from zero.semantic import analyze
from zero.compiler import compile_program
from zero.vm import run


def execute(source: str):
    """Run source code through the full pipeline and return the result."""
    tokens = tokenize(source)
    ast = parse(tokens)
    analyze(ast)
    bytecode = compile_program(ast)
    return run(bytecode)


# =============================================================================
# Compound Assignment Integration Tests
# =============================================================================


class TestCompoundAssignmentIntegration:
    def test_plus_equal_int(self, capsys):
        source = """
fn main() {
    x: int = 5
    x += 3
    print(x)
}
"""
        execute(source)
        assert capsys.readouterr().out == "8\n"

    def test_minus_equal_int(self, capsys):
        source = """
fn main() {
    x: int = 10
    x -= 4
    print(x)
}
"""
        execute(source)
        assert capsys.readouterr().out == "6\n"

    def test_plus_equal_multiple(self, capsys):
        source = """
fn main() {
    x: int = 0
    x += 5
    x += 3
    x += 2
    print(x)
}
"""
        execute(source)
        assert capsys.readouterr().out == "10\n"

    def test_minus_equal_multiple(self, capsys):
        source = """
fn main() {
    x: int = 20
    x -= 5
    x -= 3
    print(x)
}
"""
        execute(source)
        assert capsys.readouterr().out == "12\n"

    def test_mixed_compound_assignment(self, capsys):
        source = """
fn main() {
    x: int = 10
    x += 5
    x -= 3
    x += 1
    print(x)
}
"""
        execute(source)
        assert capsys.readouterr().out == "13\n"

    def test_plus_equal_with_expression(self, capsys):
        source = """
fn main() {
    x: int = 5
    x += 1 + 2
    print(x)
}
"""
        execute(source)
        assert capsys.readouterr().out == "8\n"

    def test_compound_assignment_with_function_param(self, capsys):
        source = """
fn add_to(a: int, b: int): int {
    a += b
    return a
}

fn main() {
    print(add_to(5, 3))
}
"""
        execute(source)
        assert capsys.readouterr().out == "8\n"

    def test_compound_in_conditional(self, capsys):
        source = """
fn main() {
    x: int = 5
    if (x > 3) {
        x += 10
    }
    print(x)
}
"""
        execute(source)
        assert capsys.readouterr().out == "15\n"

    def test_compound_print(self, capsys):
        source = """
fn main() {
    x: int = 5
    x += 3
    print(x)
}
"""
        execute(source)
        assert capsys.readouterr().out == "8\n"


# =============================================================================
# Multiplicative Operations Integration Tests
# =============================================================================


class TestMultiplicativeIntegration:
    def test_simple_multiplication(self, capsys):
        source = """
fn main() {
    print(3 * 4)
}
"""
        execute(source)
        assert capsys.readouterr().out == "12\n"

    def test_simple_modulo(self, capsys):
        source = """
fn main() {
    print(10 % 3)
}
"""
        execute(source)
        assert capsys.readouterr().out == "1\n"

    def test_precedence_mul_before_add(self, capsys):
        # 5 + 3 * 2 should be 11, not 16
        source = """
fn main() {
    print(5 + 3 * 2)
}
"""
        execute(source)
        assert capsys.readouterr().out == "11\n"

    def test_precedence_add_before_mul_with_parens(self, capsys):
        # (5 + 3) * 2 should be 16
        source = """
fn main() {
    print((5 + 3) * 2)
}
"""
        execute(source)
        assert capsys.readouterr().out == "16\n"

    def test_precedence_mul_on_left(self, capsys):
        # 3 * 2 + 5 should be 11, not 21
        source = """
fn main() {
    print(3 * 2 + 5)
}
"""
        execute(source)
        assert capsys.readouterr().out == "11\n"

    def test_chained_multiplication(self, capsys):
        source = """
fn main() {
    print(2 * 3 * 4)
}
"""
        execute(source)
        assert capsys.readouterr().out == "24\n"

    def test_mixed_operators(self, capsys):
        # 10 + 2 * 3 - 4 should be 10 + 6 - 4 = 12
        source = """
fn main() {
    print(10 + 2 * 3 - 4)
}
"""
        execute(source)
        assert capsys.readouterr().out == "12\n"

    def test_modulo_in_expression(self, capsys):
        # 10 % 3 + 5 should be 1 + 5 = 6
        source = """
fn main() {
    print(10 % 3 + 5)
}
"""
        execute(source)
        assert capsys.readouterr().out == "6\n"

    def test_complex_precedence(self, capsys):
        # (2 + 3) * (4 + 1) should be 5 * 5 = 25
        source = """
fn main() {
    print((2 + 3) * (4 + 1))
}
"""
        execute(source)
        assert capsys.readouterr().out == "25\n"


# =============================================================================
# Comparison Operations Integration Tests
# =============================================================================


class TestComparisonIntegration:
    # Integer comparisons
    def test_int_equality_true(self, capsys):
        source = """
fn main() {
    if (5 == 5) { print(1) } else { print(0) }
}
"""
        execute(source)
        assert capsys.readouterr().out == "1\n"

    def test_int_equality_false(self, capsys):
        source = """
fn main() {
    if (5 == 3) { print(1) } else { print(0) }
}
"""
        execute(source)
        assert capsys.readouterr().out == "0\n"

    def test_int_inequality(self, capsys):
        source = """
fn main() {
    if (5 != 3) { print(1) } else { print(0) }
}
"""
        execute(source)
        assert capsys.readouterr().out == "1\n"

    def test_int_less_than(self, capsys):
        source = """
fn main() {
    if (3 < 5) { print(1) } else { print(0) }
}
"""
        execute(source)
        assert capsys.readouterr().out == "1\n"

    def test_int_greater_than(self, capsys):
        source = """
fn main() {
    if (5 > 3) { print(1) } else { print(0) }
}
"""
        execute(source)
        assert capsys.readouterr().out == "1\n"

    def test_int_less_equal(self, capsys):
        source = """
fn main() {
    if (5 <= 5) { print(1) } else { print(0) }
}
"""
        execute(source)
        assert capsys.readouterr().out == "1\n"

    def test_int_greater_equal(self, capsys):
        source = """
fn main() {
    if (5 >= 3) { print(1) } else { print(0) }
}
"""
        execute(source)
        assert capsys.readouterr().out == "1\n"

    # Bool comparisons
    def test_bool_equality_true(self, capsys):
        source = """
fn main() {
    if (true == true) { print(1) } else { print(0) }
}
"""
        execute(source)
        assert capsys.readouterr().out == "1\n"

    def test_bool_equality_false(self, capsys):
        source = """
fn main() {
    if (true == false) { print(1) } else { print(0) }
}
"""
        execute(source)
        assert capsys.readouterr().out == "0\n"

    def test_bool_inequality(self, capsys):
        source = """
fn main() {
    if (true != false) { print(1) } else { print(0) }
}
"""
        execute(source)
        assert capsys.readouterr().out == "1\n"

    # String comparisons
    def test_string_equality_true(self, capsys):
        source = """
fn main() {
    if ("hello" == "hello") { print(1) } else { print(0) }
}
"""
        execute(source)
        assert capsys.readouterr().out == "1\n"

    def test_string_equality_false(self, capsys):
        source = """
fn main() {
    if ("hello" == "world") { print(1) } else { print(0) }
}
"""
        execute(source)
        assert capsys.readouterr().out == "0\n"

    def test_string_inequality(self, capsys):
        source = """
fn main() {
    if ("hello" != "world") { print(1) } else { print(0) }
}
"""
        execute(source)
        assert capsys.readouterr().out == "1\n"

    # Comparison in conditions
    def test_comparison_in_if_condition(self, capsys):
        source = """
fn main() {
    x: int = 5
    if (x == 5) {
        print(1)
    } else {
        print(0)
    }
}
"""
        execute(source)
        assert capsys.readouterr().out == "1\n"

    def test_comparison_in_if_else(self, capsys):
        source = """
fn main() {
    x: int = 3
    if (x > 5) {
        print(1)
    } else {
        print(0)
    }
}
"""
        execute(source)
        assert capsys.readouterr().out == "0\n"

    def test_comparison_with_variables(self, capsys):
        source = """
fn main() {
    x: int = 5
    y: int = 5
    if (x == y) { print(1) } else { print(0) }
}
"""
        execute(source)
        assert capsys.readouterr().out == "1\n"
