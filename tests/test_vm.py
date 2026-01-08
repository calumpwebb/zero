import pytest
from zero.bytecode import Op, Chunk, CompiledProgram, BUILTINS
from zero.vm import run


# =============================================================================
# Basic Operations
# =============================================================================


class TestBasicOperations:
    def test_return_constant(self):
        # return 42
        chunk = Chunk(
            code=[Op.CONST, 0, Op.RET],
            constants=[42],
            arity=0
        )
        program = CompiledProgram(
            chunks=[chunk],
            function_index={"main": 0}
        )
        result = run(program)
        assert result == 42

    def test_add_two_constants(self):
        # return 1 + 2
        chunk = Chunk(
            code=[Op.CONST, 0, Op.CONST, 1, Op.ADD_INT, Op.RET],
            constants=[1, 2],
            arity=0
        )
        program = CompiledProgram(
            chunks=[chunk],
            function_index={"main": 0}
        )
        result = run(program)
        assert result == 3

    def test_chained_addition(self):
        # return 1 + 2 + 3
        chunk = Chunk(
            code=[
                Op.CONST, 0,
                Op.CONST, 1,
                Op.ADD_INT,
                Op.CONST, 2,
                Op.ADD_INT,
                Op.RET
            ],
            constants=[1, 2, 3],
            arity=0
        )
        program = CompiledProgram(
            chunks=[chunk],
            function_index={"main": 0}
        )
        result = run(program)
        assert result == 6


# =============================================================================
# Function Calls
# =============================================================================


class TestFunctionCalls:
    def test_call_function_no_args(self):
        # fn bar() { return 42 }
        # fn main() { return bar() }
        bar_chunk = Chunk(
            code=[Op.CONST, 0, Op.RET],
            constants=[42],
            arity=0
        )
        main_chunk = Chunk(
            code=[Op.CALL, 0, 0, Op.RET],  # call bar (index 0), 0 args
            constants=[],
            arity=0
        )
        program = CompiledProgram(
            chunks=[bar_chunk, main_chunk],
            function_index={"bar": 0, "main": 1}
        )
        result = run(program)
        assert result == 42

    def test_call_function_with_args(self):
        # fn add(a, b) { return a + b }
        # fn main() { return add(5, 3) }
        add_chunk = Chunk(
            code=[Op.LOAD, 0, Op.LOAD, 1, Op.ADD_INT, Op.RET],
            constants=[],
            arity=2
        )
        main_chunk = Chunk(
            code=[Op.CONST, 0, Op.CONST, 1, Op.CALL, 0, 2, Op.RET],
            constants=[5, 3],
            arity=0
        )
        program = CompiledProgram(
            chunks=[add_chunk, main_chunk],
            function_index={"add": 0, "main": 1}
        )
        result = run(program)
        assert result == 8

    def test_nested_function_calls(self):
        # fn double(x) { return x + x }
        # fn quadruple(x) { return double(double(x)) }
        # fn main() { return quadruple(3) }
        double_chunk = Chunk(
            code=[Op.LOAD, 0, Op.LOAD, 0, Op.ADD_INT, Op.RET],
            constants=[],
            arity=1
        )
        quadruple_chunk = Chunk(
            code=[
                Op.LOAD, 0,      # push x
                Op.CALL, 0, 1,  # double(x)
                Op.CALL, 0, 1,  # double(result)
                Op.RET
            ],
            constants=[],
            arity=1
        )
        main_chunk = Chunk(
            code=[Op.CONST, 0, Op.CALL, 1, 1, Op.RET],
            constants=[3],
            arity=0
        )
        program = CompiledProgram(
            chunks=[double_chunk, quadruple_chunk, main_chunk],
            function_index={"double": 0, "quadruple": 1, "main": 2}
        )
        result = run(program)
        assert result == 12


# =============================================================================
# Builtin Functions
# =============================================================================


class TestBuiltinFunctions:
    def test_print_literal(self, capsys):
        # fn main() { print(42) return 0 }
        chunk = Chunk(
            code=[
                Op.CONST, 0,
                Op.CALL_BUILTIN, BUILTINS["print"], 1,
                Op.POP,
                Op.CONST, 1,
                Op.RET
            ],
            constants=[42, 0],
            arity=0
        )
        program = CompiledProgram(
            chunks=[chunk],
            function_index={"main": 0}
        )
        run(program)
        captured = capsys.readouterr()
        assert captured.out == "42\n"

    def test_print_multiple(self, capsys):
        # fn main() { print(1) print(2) return 0 }
        chunk = Chunk(
            code=[
                Op.CONST, 0,
                Op.CALL_BUILTIN, BUILTINS["print"], 1,
                Op.POP,
                Op.CONST, 1,
                Op.CALL_BUILTIN, BUILTINS["print"], 1,
                Op.POP,
                Op.CONST, 2,
                Op.RET
            ],
            constants=[1, 2, 0],
            arity=0
        )
        program = CompiledProgram(
            chunks=[chunk],
            function_index={"main": 0}
        )
        run(program)
        captured = capsys.readouterr()
        assert captured.out == "1\n2\n"

    def test_print_expression_result(self, capsys):
        # fn main() { print(1 + 2) return 0 }
        chunk = Chunk(
            code=[
                Op.CONST, 0,
                Op.CONST, 1,
                Op.ADD_INT,
                Op.CALL_BUILTIN, BUILTINS["print"], 1,
                Op.POP,
                Op.CONST, 2,
                Op.RET
            ],
            constants=[1, 2, 0],
            arity=0
        )
        program = CompiledProgram(
            chunks=[chunk],
            function_index={"main": 0}
        )
        run(program)
        captured = capsys.readouterr()
        assert captured.out == "3\n"

    def test_print_function_result(self, capsys):
        # fn add(a, b) { return a + b }
        # fn main() { print(add(5, 3)) return 0 }
        add_chunk = Chunk(
            code=[Op.LOAD, 0, Op.LOAD, 1, Op.ADD_INT, Op.RET],
            constants=[],
            arity=2
        )
        main_chunk = Chunk(
            code=[
                Op.CONST, 0,
                Op.CONST, 1,
                Op.CALL, 0, 2,
                Op.CALL_BUILTIN, BUILTINS["print"], 1,
                Op.POP,
                Op.CONST, 2,
                Op.RET
            ],
            constants=[5, 3, 0],
            arity=0
        )
        program = CompiledProgram(
            chunks=[add_chunk, main_chunk],
            function_index={"add": 0, "main": 1}
        )
        run(program)
        captured = capsys.readouterr()
        assert captured.out == "8\n"
