import pytest
from zero.ast import (
    Program,
    Function,
    Param,
    ReturnStmt,
    ExprStmt,
    BinaryExpr,
    Call,
    IntLiteral,
    Identifier,
)
from zero.bytecode import Op, Chunk, CompiledProgram, BUILTINS
from zero.compiler import compile_program


# =============================================================================
# Expression Compilation
# =============================================================================


class TestExpressionCompilation:
    def test_compile_int_literal(self):
        # fn main() { return 42 }
        program = Program([
            Function("main", [], None, [ReturnStmt(IntLiteral(42))])
        ])
        result = compile_program(program)

        chunk = result.chunks[result.function_index["main"]]
        assert chunk.code == [Op.CONST, 0, Op.RET]
        assert chunk.constants == [42]

    def test_compile_identifier_loads_local(self):
        # fn foo(x: int) { return x }
        program = Program([
            Function("foo", [Param("x", "int")], "int", [
                ReturnStmt(Identifier("x"))
            ])
        ])
        result = compile_program(program)

        chunk = result.chunks[result.function_index["foo"]]
        assert chunk.code == [Op.LOAD, 0, Op.RET]
        assert chunk.arity == 1

    def test_compile_second_param(self):
        # fn foo(a: int, b: int) { return b }
        program = Program([
            Function("foo", [Param("a", "int"), Param("b", "int")], "int", [
                ReturnStmt(Identifier("b"))
            ])
        ])
        result = compile_program(program)

        chunk = result.chunks[result.function_index["foo"]]
        assert chunk.code == [Op.LOAD, 1, Op.RET]
        assert chunk.arity == 2

    def test_compile_binary_addition(self):
        # fn main() { return 1 + 2 }
        program = Program([
            Function("main", [], None, [
                ReturnStmt(BinaryExpr("+", IntLiteral(1), IntLiteral(2)))
            ])
        ])
        result = compile_program(program)

        chunk = result.chunks[result.function_index["main"]]
        assert chunk.code == [Op.CONST, 0, Op.CONST, 1, Op.ADD_INT, Op.RET]
        assert chunk.constants == [1, 2]

    def test_compile_chained_addition(self):
        # fn main() { return 1 + 2 + 3 }
        # Parses as ((1 + 2) + 3)
        program = Program([
            Function("main", [], None, [
                ReturnStmt(BinaryExpr(
                    "+",
                    BinaryExpr("+", IntLiteral(1), IntLiteral(2)),
                    IntLiteral(3)
                ))
            ])
        ])
        result = compile_program(program)

        chunk = result.chunks[result.function_index["main"]]
        assert chunk.code == [
            Op.CONST, 0,  # push 1
            Op.CONST, 1,  # push 2
            Op.ADD_INT,       # 1 + 2
            Op.CONST, 2,  # push 3
            Op.ADD_INT,       # (1+2) + 3
            Op.RET
        ]
        assert chunk.constants == [1, 2, 3]

    def test_compile_add_params(self):
        # fn add(a: int, b: int): int { return a + b }
        program = Program([
            Function("add", [Param("a", "int"), Param("b", "int")], "int", [
                ReturnStmt(BinaryExpr("+", Identifier("a"), Identifier("b")))
            ])
        ])
        result = compile_program(program)

        chunk = result.chunks[result.function_index["add"]]
        assert chunk.code == [Op.LOAD, 0, Op.LOAD, 1, Op.ADD_INT, Op.RET]
        assert chunk.arity == 2


# =============================================================================
# Function Call Compilation
# =============================================================================


class TestFunctionCallCompilation:
    def test_compile_call_no_args(self):
        # fn bar() { return 1 }
        # fn main() { return bar() }
        program = Program([
            Function("bar", [], "int", [ReturnStmt(IntLiteral(1))]),
            Function("main", [], None, [ReturnStmt(Call("bar", []))])
        ])
        result = compile_program(program)

        main_chunk = result.chunks[result.function_index["main"]]
        bar_idx = result.function_index["bar"]
        assert main_chunk.code == [Op.CALL, bar_idx, 0, Op.RET]

    def test_compile_call_with_args(self):
        # fn add(a: int, b: int): int { return a + b }
        # fn main() { return add(5, 3) }
        program = Program([
            Function("add", [Param("a", "int"), Param("b", "int")], "int", [
                ReturnStmt(BinaryExpr("+", Identifier("a"), Identifier("b")))
            ]),
            Function("main", [], None, [
                ReturnStmt(Call("add", [IntLiteral(5), IntLiteral(3)]))
            ])
        ])
        result = compile_program(program)

        main_chunk = result.chunks[result.function_index["main"]]
        add_idx = result.function_index["add"]
        assert main_chunk.code == [
            Op.CONST, 0,      # push 5
            Op.CONST, 1,      # push 3
            Op.CALL, add_idx, 2,  # call add with 2 args
            Op.RET
        ]
        assert main_chunk.constants == [5, 3]


# =============================================================================
# Statement Compilation
# =============================================================================


class TestStatementCompilation:
    def test_compile_expression_statement_pops(self):
        # fn main() { foo() return 1 }
        program = Program([
            Function("foo", [], None, [ReturnStmt(IntLiteral(0))]),
            Function("main", [], None, [
                ExprStmt(Call("foo", [])),
                ReturnStmt(IntLiteral(1))
            ])
        ])
        result = compile_program(program)

        main_chunk = result.chunks[result.function_index["main"]]
        foo_idx = result.function_index["foo"]
        assert main_chunk.code == [
            Op.CALL, foo_idx, 0,  # call foo
            Op.POP,              # discard result
            Op.CONST, 0,         # push 1
            Op.RET
        ]


# =============================================================================
# Program Compilation
# =============================================================================


class TestProgramCompilation:
    def test_compile_empty_program(self):
        program = Program([])
        result = compile_program(program)
        assert result.chunks == []
        assert result.function_index == {}

    def test_compile_multiple_functions(self):
        # fn add(a: int, b: int): int { return a + b }
        # fn main() { return add(5, 3) }
        program = Program([
            Function("add", [Param("a", "int"), Param("b", "int")], "int", [
                ReturnStmt(BinaryExpr("+", Identifier("a"), Identifier("b")))
            ]),
            Function("main", [], None, [
                ReturnStmt(Call("add", [IntLiteral(5), IntLiteral(3)]))
            ])
        ])
        result = compile_program(program)

        assert len(result.chunks) == 2
        assert "add" in result.function_index
        assert "main" in result.function_index

        # Verify add function
        add_chunk = result.chunks[result.function_index["add"]]
        assert add_chunk.arity == 2
        assert add_chunk.code == [Op.LOAD, 0, Op.LOAD, 1, Op.ADD_INT, Op.RET]

        # Verify main function
        main_chunk = result.chunks[result.function_index["main"]]
        add_idx = result.function_index["add"]
        assert main_chunk.code == [
            Op.CONST, 0,
            Op.CONST, 1,
            Op.CALL, add_idx, 2,
            Op.RET
        ]
        assert main_chunk.constants == [5, 3]


# =============================================================================
# Builtin Compilation
# =============================================================================


class TestBuiltinCompilation:
    def test_compile_print_literal(self):
        # fn main() { print(42) }
        program = Program([
            Function("main", [], None, [
                ExprStmt(Call("print", [IntLiteral(42)]))
            ])
        ])
        result = compile_program(program)

        chunk = result.chunks[result.function_index["main"]]
        assert chunk.code == [
            Op.CONST, 0,
            Op.CALL_BUILTIN, BUILTINS["print"], 1,
            Op.POP
        ]
        assert chunk.constants == [42]

    def test_compile_print_expression(self):
        # fn main() { print(1 + 2) }
        program = Program([
            Function("main", [], None, [
                ExprStmt(Call("print", [BinaryExpr("+", IntLiteral(1), IntLiteral(2))]))
            ])
        ])
        result = compile_program(program)

        chunk = result.chunks[result.function_index["main"]]
        assert chunk.code == [
            Op.CONST, 0,
            Op.CONST, 1,
            Op.ADD_INT,
            Op.CALL_BUILTIN, BUILTINS["print"], 1,
            Op.POP
        ]
        assert chunk.constants == [1, 2]

    def test_compile_print_function_result(self):
        # fn add(a: int, b: int): int { return a + b }
        # fn main() { print(add(5, 3)) }
        program = Program([
            Function("add", [Param("a", "int"), Param("b", "int")], "int", [
                ReturnStmt(BinaryExpr("+", Identifier("a"), Identifier("b")))
            ]),
            Function("main", [], None, [
                ExprStmt(Call("print", [Call("add", [IntLiteral(5), IntLiteral(3)])]))
            ])
        ])
        result = compile_program(program)

        main_chunk = result.chunks[result.function_index["main"]]
        add_idx = result.function_index["add"]
        assert main_chunk.code == [
            Op.CONST, 0,
            Op.CONST, 1,
            Op.CALL, add_idx, 2,
            Op.CALL_BUILTIN, BUILTINS["print"], 1,
            Op.POP
        ]
        assert main_chunk.constants == [5, 3]

    def test_compile_multiple_prints(self):
        # fn main() { print(1) print(2) }
        program = Program([
            Function("main", [], None, [
                ExprStmt(Call("print", [IntLiteral(1)])),
                ExprStmt(Call("print", [IntLiteral(2)]))
            ])
        ])
        result = compile_program(program)

        chunk = result.chunks[result.function_index["main"]]
        assert chunk.code == [
            Op.CONST, 0,
            Op.CALL_BUILTIN, BUILTINS["print"], 1,
            Op.POP,
            Op.CONST, 1,
            Op.CALL_BUILTIN, BUILTINS["print"], 1,
            Op.POP
        ]
        assert chunk.constants == [1, 2]
