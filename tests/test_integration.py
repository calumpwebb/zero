import pytest
from zero.lexer import tokenize
from zero.parser import parse
from zero.compiler import compile_program
from zero.vm import run


def execute(source: str) -> int:
    """Helper to run the full pipeline."""
    tokens = tokenize(source)
    ast = parse(tokens)
    bytecode = compile_program(ast)
    return run(bytecode)


# =============================================================================
# End-to-End Tests
# =============================================================================


class TestEndToEnd:
    def test_return_literal(self):
        source = """
        fn main(): int {
            return 42
        }
        """
        assert execute(source) == 42

    def test_return_addition(self):
        source = """
        fn main(): int {
            return 1 + 2
        }
        """
        assert execute(source) == 3

    def test_return_subtraction(self):
        source = """
        fn main(): int {
            return 5 - 3
        }
        """
        assert execute(source) == 2

    def test_chained_addition(self):
        source = """
        fn main(): int {
            return 1 + 2 + 3 + 4
        }
        """
        assert execute(source) == 10

    def test_call_function(self):
        source = """
        fn add(a: int, b: int): int {
            return a + b
        }
        fn main(): int {
            return add(5, 3)
        }
        """
        assert execute(source) == 8

    def test_nested_calls(self):
        source = """
        fn double(x: int): int {
            return x + x
        }
        fn quadruple(x: int): int {
            return double(double(x))
        }
        fn main(): int {
            return quadruple(3)
        }
        """
        assert execute(source) == 12

    def test_print_literal(self, capsys):
        source = """
        fn main(): int {
            print(42)
            return 0
        }
        """
        execute(source)
        assert capsys.readouterr().out == "42\n"

    def test_print_expression(self, capsys):
        source = """
        fn main(): int {
            print(1 + 2)
            return 0
        }
        """
        execute(source)
        assert capsys.readouterr().out == "3\n"

    def test_print_function_result(self, capsys):
        source = """
        fn add(a: int, b: int): int {
            return a + b
        }
        fn main(): int {
            print(add(5, 3))
            return 0
        }
        """
        execute(source)
        assert capsys.readouterr().out == "8\n"

    def test_multiple_prints(self, capsys):
        source = """
        fn main(): int {
            print(1)
            print(2)
            print(3)
            return 0
        }
        """
        execute(source)
        assert capsys.readouterr().out == "1\n2\n3\n"

    def test_example_add_zero(self, capsys):
        source = """
        fn add(a: int, b: int): int {
            return a + b
        }
        fn main(): int {
            print(add(5, 3))
            return 0
        }
        """
        result = execute(source)
        assert capsys.readouterr().out == "8\n"
        assert result == 0

    def test_return_true(self):
        source = """
        fn main(): bool {
            return true
        }
        """
        assert execute(source) == True

    def test_return_false(self):
        source = """
        fn main(): bool {
            return false
        }
        """
        assert execute(source) == False

    def test_print_bool(self, capsys):
        source = """
        fn main(): int {
            print(true)
            print(false)
            return 0
        }
        """
        execute(source)
        assert capsys.readouterr().out == "True\nFalse\n"

    def test_print_string(self, capsys):
        source = """
        fn main(): int {
            print("hello")
            return 0
        }
        """
        execute(source)
        assert capsys.readouterr().out == "hello\n"

    def test_string_concatenation(self, capsys):
        source = """
        fn main(): int {
            print("hello" + " world")
            return 0
        }
        """
        execute(source)
        assert capsys.readouterr().out == "hello world\n"


class TestTypeErrors:
    def test_cannot_add_int_and_string(self):
        source = """
        fn main(): int {
            print(1 + "hello")
            return 0
        }
        """
        with pytest.raises(TypeError, match=r"[Cc]annot add"):
            execute(source)

    def test_cannot_add_string_and_int(self):
        source = """
        fn main(): int {
            print("hello" + 1)
            return 0
        }
        """
        with pytest.raises(TypeError, match=r"[Cc]annot add"):
            execute(source)

    def test_cannot_add_booleans(self):
        source = """
        fn main(): int {
            print(true + false)
            return 0
        }
        """
        with pytest.raises(TypeError, match=r"[Cc]annot add"):
            execute(source)

    def test_cannot_add_true_true(self):
        source = """
        fn main(): int {
            print(true + true)
            return 0
        }
        """
        with pytest.raises(TypeError, match=r"[Cc]annot add"):
            execute(source)

    def test_cannot_subtract_strings(self):
        source = """
        fn main(): int {
            print("hello" - "world")
            return 0
        }
        """
        with pytest.raises(TypeError, match=r"[Cc]annot subtract"):
            execute(source)

    def test_cannot_subtract_booleans(self):
        source = """
        fn main(): int {
            print(true - false)
            return 0
        }
        """
        with pytest.raises(TypeError, match=r"[Cc]annot subtract"):
            execute(source)
