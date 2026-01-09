import pytest
from zero.ast import (
    Program,
    Function,
    Param,
    ReturnStmt,
    ExprStmt,
    BinaryExpr,
    UnaryExpr,
    Call,
    IntLiteral,
    BoolLiteral,
    StringLiteral,
    Identifier,
    VarDecl,
    Assignment,
    IfStmt,
    ForStmt,
    BreakStmt,
    ContinueStmt,
)
from zero.bytecode import Op, Chunk, CompiledProgram
from zero.builtins import BUILTIN_INDICES
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
# Multiplicative Compilation
# =============================================================================


class TestMultiplicativeCompilation:
    def test_compile_multiplication(self):
        # fn main() { return 3 * 4 }
        program = Program([
            Function("main", [], None, [
                ReturnStmt(BinaryExpr("*", IntLiteral(3), IntLiteral(4)))
            ])
        ])
        result = compile_program(program)

        chunk = result.chunks[result.function_index["main"]]
        assert chunk.code == [Op.CONST, 0, Op.CONST, 1, Op.MUL_INT, Op.RET]
        assert chunk.constants == [3, 4]

    def test_compile_modulo(self):
        # fn main() { return 10 % 3 }
        program = Program([
            Function("main", [], None, [
                ReturnStmt(BinaryExpr("%", IntLiteral(10), IntLiteral(3)))
            ])
        ])
        result = compile_program(program)

        chunk = result.chunks[result.function_index["main"]]
        assert chunk.code == [Op.CONST, 0, Op.CONST, 1, Op.MOD_INT, Op.RET]
        assert chunk.constants == [10, 3]


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
            Op.CALL_BUILTIN, BUILTIN_INDICES["print"], 1,
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
            Op.CALL_BUILTIN, BUILTIN_INDICES["print"], 1,
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
            Op.CALL_BUILTIN, BUILTIN_INDICES["print"], 1,
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
            Op.CALL_BUILTIN, BUILTIN_INDICES["print"], 1,
            Op.POP,
            Op.CONST, 1,
            Op.CALL_BUILTIN, BUILTIN_INDICES["print"], 1,
            Op.POP
        ]
        assert chunk.constants == [1, 2]


# =============================================================================
# Variable Compilation
# =============================================================================


class TestVariableCompilation:
    def test_compile_var_decl(self):
        # fn main() { x: int = 5 return x }
        program = Program([
            Function("main", [], None, [
                VarDecl("x", "int", IntLiteral(5)),
                ReturnStmt(Identifier("x")),
            ])
        ])
        result = compile_program(program)

        chunk = result.chunks[result.function_index["main"]]
        # VarDecl: push value, store to slot 0
        # Return: load slot 0, return
        assert chunk.code == [
            Op.CONST, 0,    # push 5
            Op.STORE, 0,    # store to slot 0
            Op.LOAD, 0,     # load from slot 0
            Op.RET
        ]
        assert chunk.constants == [5]

    def test_compile_assignment(self):
        # fn main() { x: int = 5 x = 10 return x }
        program = Program([
            Function("main", [], None, [
                VarDecl("x", "int", IntLiteral(5)),
                Assignment("x", IntLiteral(10)),
                ReturnStmt(Identifier("x")),
            ])
        ])
        result = compile_program(program)

        chunk = result.chunks[result.function_index["main"]]
        assert chunk.code == [
            Op.CONST, 0,    # push 5
            Op.STORE, 0,    # store to slot 0 (x = 5)
            Op.CONST, 1,    # push 10
            Op.STORE, 0,    # store to slot 0 (x = 10)
            Op.LOAD, 0,     # load x
            Op.RET
        ]
        assert chunk.constants == [5, 10]

    def test_compile_var_with_param(self):
        # fn foo(a: int) { x: int = a return x }
        # param a is slot 0, local x is slot 1
        program = Program([
            Function("foo", [Param("a", "int")], "int", [
                VarDecl("x", "int", Identifier("a")),
                ReturnStmt(Identifier("x")),
            ])
        ])
        result = compile_program(program)

        chunk = result.chunks[result.function_index["foo"]]
        assert chunk.code == [
            Op.LOAD, 0,     # load param a
            Op.STORE, 1,    # store to slot 1 (x)
            Op.LOAD, 1,     # load x
            Op.RET
        ]
        assert chunk.arity == 1


# =============================================================================
# Comparison Compilation
# =============================================================================


class TestComparisonCompilation:
    def test_compile_less_than(self):
        # fn main() { return 1 < 2 }
        program = Program([
            Function("main", [], None, [
                ReturnStmt(BinaryExpr("<", IntLiteral(1), IntLiteral(2)))
            ])
        ])
        result = compile_program(program)

        chunk = result.chunks[result.function_index["main"]]
        assert chunk.code == [
            Op.CONST, 0,    # push 1
            Op.CONST, 1,    # push 2
            Op.CMP_LT_INT,      # compare <
            Op.RET
        ]

    def test_compile_equals(self):
        # fn main() { return 5 == 5 }
        program = Program([
            Function("main", [], None, [
                ReturnStmt(BinaryExpr("==", IntLiteral(5), IntLiteral(5)))
            ])
        ])
        result = compile_program(program)

        chunk = result.chunks[result.function_index["main"]]
        assert chunk.code == [
            Op.CONST, 0,
            Op.CONST, 1,
            Op.CMP_EQ_INT,
            Op.RET
        ]

    def test_compile_all_comparisons(self):
        # Test that all 6 comparison operators compile to correct opcodes
        ops = [
            ("==", Op.CMP_EQ_INT),
            ("!=", Op.CMP_NE_INT),
            ("<", Op.CMP_LT_INT),
            (">", Op.CMP_GT_INT),
            ("<=", Op.CMP_LE_INT),
            (">=", Op.CMP_GE_INT),
        ]
        for op_str, op_code in ops:
            program = Program([
                Function("main", [], None, [
                    ReturnStmt(BinaryExpr(op_str, IntLiteral(1), IntLiteral(2)))
                ])
            ])
            result = compile_program(program)
            chunk = result.chunks[result.function_index["main"]]
            assert op_code in chunk.code, f"Expected {op_code} for '{op_str}'"

    def test_compile_bool_equality(self):
        # fn main() { return true == false }
        program = Program([
            Function("main", [], None, [
                ReturnStmt(BinaryExpr("==", BoolLiteral(True), BoolLiteral(False)))
            ])
        ])
        result = compile_program(program)
        chunk = result.chunks[result.function_index["main"]]
        assert Op.CMP_EQ_BOOL in chunk.code

    def test_compile_bool_inequality(self):
        # fn main() { return true != false }
        program = Program([
            Function("main", [], None, [
                ReturnStmt(BinaryExpr("!=", BoolLiteral(True), BoolLiteral(False)))
            ])
        ])
        result = compile_program(program)
        chunk = result.chunks[result.function_index["main"]]
        assert Op.CMP_NE_BOOL in chunk.code

    def test_compile_string_equality(self):
        # fn main() { return "hello" == "world" }
        program = Program([
            Function("main", [], None, [
                ReturnStmt(BinaryExpr("==", StringLiteral("hello"), StringLiteral("world")))
            ])
        ])
        result = compile_program(program)
        chunk = result.chunks[result.function_index["main"]]
        assert Op.CMP_EQ_STR in chunk.code

    def test_compile_string_inequality(self):
        # fn main() { return "hello" != "world" }
        program = Program([
            Function("main", [], None, [
                ReturnStmt(BinaryExpr("!=", StringLiteral("hello"), StringLiteral("world")))
            ])
        ])
        result = compile_program(program)
        chunk = result.chunks[result.function_index["main"]]
        assert Op.CMP_NE_STR in chunk.code

    def test_compile_cross_type_equality_error(self):
        # fn main() { return 5 == true } should fail
        program = Program([
            Function("main", [], None, [
                ReturnStmt(BinaryExpr("==", IntLiteral(5), BoolLiteral(True)))
            ])
        ])
        with pytest.raises(TypeError, match=r"Cannot compare"):
            compile_program(program)

    def test_compile_cross_type_int_str_error(self):
        # fn main() { return 5 == "hello" } should fail
        program = Program([
            Function("main", [], None, [
                ReturnStmt(BinaryExpr("==", IntLiteral(5), StringLiteral("hello")))
            ])
        ])
        with pytest.raises(TypeError, match=r"Cannot compare"):
            compile_program(program)

    def test_compile_cross_type_ordering_error(self):
        # fn main() { return true < false } should fail (no ordering for bool)
        program = Program([
            Function("main", [], None, [
                ReturnStmt(BinaryExpr("<", BoolLiteral(True), BoolLiteral(False)))
            ])
        ])
        with pytest.raises(TypeError, match=r"Cannot compare"):
            compile_program(program)


# =============================================================================
# If/Else Compilation
# =============================================================================


# =============================================================================
# Compound Assignment Compilation
# =============================================================================


class TestCompoundAssignmentCompilation:
    def test_compile_plus_equal(self):
        # fn main() { x: int = 5  x += 3  return x }
        # Desugars to: x = x + 3
        program = Program([
            Function("main", [], None, [
                VarDecl("x", "int", IntLiteral(5)),
                Assignment("x", BinaryExpr("+", Identifier("x"), IntLiteral(3))),
                ReturnStmt(Identifier("x")),
            ])
        ])
        result = compile_program(program)

        chunk = result.chunks[result.function_index["main"]]
        # x: int = 5  →  CONST 0, STORE 0
        # x += 3      →  LOAD 0, CONST 1, ADD_INT, STORE 0
        # return x    →  LOAD 0, RET
        assert chunk.code == [
            Op.CONST, 0,    # push 5
            Op.STORE, 0,    # store to slot 0 (x = 5)
            Op.LOAD, 0,     # load x
            Op.CONST, 1,    # push 3
            Op.ADD_INT,     # x + 3
            Op.STORE, 0,    # store result back to x
            Op.LOAD, 0,     # load x
            Op.RET
        ]
        assert chunk.constants == [5, 3]

    def test_compile_minus_equal(self):
        # fn main() { x: int = 10  x -= 4  return x }
        # Desugars to: x = x - 4
        program = Program([
            Function("main", [], None, [
                VarDecl("x", "int", IntLiteral(10)),
                Assignment("x", BinaryExpr("-", Identifier("x"), IntLiteral(4))),
                ReturnStmt(Identifier("x")),
            ])
        ])
        result = compile_program(program)

        chunk = result.chunks[result.function_index["main"]]
        assert chunk.code == [
            Op.CONST, 0,    # push 10
            Op.STORE, 0,    # store to slot 0
            Op.LOAD, 0,     # load x
            Op.CONST, 1,    # push 4
            Op.SUB_INT,     # x - 4
            Op.STORE, 0,    # store result back to x
            Op.LOAD, 0,     # load x
            Op.RET
        ]
        assert chunk.constants == [10, 4]


# =============================================================================
# If/Else Compilation
# =============================================================================


class TestIfElseCompilation:
    def test_compile_if_no_else(self):
        # fn main() { if (true) { return 1 } return 0 }
        # Expected bytecode:
        #   CONST 0 (true)
        #   JUMP_IF_FALSE -> after then block
        #   CONST 1 (1)
        #   RET
        #   CONST 2 (0)  <- jump target
        #   RET
        program = Program([
            Function("main", [], None, [
                IfStmt(
                    BoolLiteral(True),
                    [ReturnStmt(IntLiteral(1))],
                    None
                ),
                ReturnStmt(IntLiteral(0))
            ])
        ])
        result = compile_program(program)

        chunk = result.chunks[result.function_index["main"]]
        # Layout:
        # 0: CONST 0      (true)
        # 2: JUMP_IF_FALSE 6  (jump to index 6)
        # 4: CONST 1      (1)
        # 6: RET
        # 7: CONST 2      (0)  <- jump lands here
        # 9: RET
        assert chunk.code == [
            Op.CONST, 0,          # push true
            Op.JUMP_IF_FALSE, 7,  # jump past then block (to CONST 2)
            Op.CONST, 1,          # push 1
            Op.RET,               # return 1
            Op.CONST, 2,          # push 0
            Op.RET                # return 0
        ]
        assert chunk.constants == [True, 1, 0]

    def test_compile_if_else(self):
        # fn main() { if (true) { return 1 } else { return 0 } }
        # Expected bytecode:
        #   CONST 0 (true)
        #   JUMP_IF_FALSE -> else block
        #   CONST 1 (1)
        #   RET
        #   JUMP -> end (skip else)  <- this is where false jumps to before the else
        #   CONST 2 (0)
        #   RET
        program = Program([
            Function("main", [], None, [
                IfStmt(
                    BoolLiteral(True),
                    [ReturnStmt(IntLiteral(1))],
                    [ReturnStmt(IntLiteral(0))]
                )
            ])
        ])
        result = compile_program(program)

        chunk = result.chunks[result.function_index["main"]]
        # Layout with else:
        # 0: CONST 0           (true)
        # 2: JUMP_IF_FALSE 9   (jump to else block)
        # 4: CONST 1           (1)
        # 6: RET
        # 7: JUMP 12           (skip else - but since we RET, this won't execute)
        # Actually, when then block ends with return, we don't need the JUMP
        # But for general case (non-return statements), we need the JUMP
        # For this test with returns in both branches, the JUMP is unreachable
        # Let's test with a more general case instead
        assert chunk.code == [
            Op.CONST, 0,          # push true
            Op.JUMP_IF_FALSE, 9,  # jump to else block
            Op.CONST, 1,          # push 1
            Op.RET,               # return 1
            Op.JUMP, 12,          # skip else (unreachable but correct)
            Op.CONST, 2,          # push 0
            Op.RET                # return 0
        ]
        assert chunk.constants == [True, 1, 0]


# =============================================================================
# For Loop Compilation
# =============================================================================


class TestForLoopCompilation:
    def test_compile_for_loop(self):
        # fn main() { for (true) { break } }
        # Expected bytecode:
        #   loop_start:
        #   0: CONST 0 (true)
        #   2: JUMP_IF_FALSE end (7)
        #   4: JUMP end (7)      <- break
        #   6: JUMP loop_start (0)
        #   end:
        program = Program([
            Function("main", [], None, [
                ForStmt(
                    BoolLiteral(True),
                    [BreakStmt()]
                )
            ])
        ])
        result = compile_program(program)

        chunk = result.chunks[result.function_index["main"]]
        assert chunk.code == [
            Op.CONST, 0,          # push true
            Op.JUMP_IF_FALSE, 8,  # jump past loop if false
            Op.JUMP, 8,           # break: jump to end
            Op.JUMP, 0,           # loop back to start
        ]
        assert chunk.constants == [True]

    def test_compile_for_with_continue(self):
        # fn main() { for (true) { continue } }
        # Expected bytecode:
        #   loop_start:
        #   0: CONST 0 (true)
        #   2: JUMP_IF_FALSE end
        #   4: JUMP loop_start    <- continue
        #   6: JUMP loop_start
        #   end:
        program = Program([
            Function("main", [], None, [
                ForStmt(
                    BoolLiteral(True),
                    [ContinueStmt()]
                )
            ])
        ])
        result = compile_program(program)

        chunk = result.chunks[result.function_index["main"]]
        assert chunk.code == [
            Op.CONST, 0,          # push true
            Op.JUMP_IF_FALSE, 8,  # jump past loop if false
            Op.JUMP, 0,           # continue: jump to loop start
            Op.JUMP, 0,           # loop back to start
        ]

    def test_compile_for_with_body(self):
        # fn main() { x: int = 0  for (x < 3) { x += 1 } }
        # This tests a real loop with a condition and body
        program = Program([
            Function("main", [], None, [
                VarDecl("x", "int", IntLiteral(0)),
                ForStmt(
                    BinaryExpr("<", Identifier("x"), IntLiteral(3)),
                    [Assignment("x", BinaryExpr("+", Identifier("x"), IntLiteral(1)))]
                )
            ])
        ])
        result = compile_program(program)

        chunk = result.chunks[result.function_index["main"]]
        # x: int = 0
        # 0: CONST 0, 2: STORE 0
        # loop_start:
        # 4: LOAD 0, 6: CONST 1, 8: CMP_LT
        # 9: JUMP_IF_FALSE end
        # 11: LOAD 0, 13: CONST 2, 15: ADD_INT, 16: STORE 0
        # 18: JUMP loop_start (4)
        # end: (20)
        assert chunk.code == [
            Op.CONST, 0,          # push 0
            Op.STORE, 0,          # x = 0
            # loop_start:
            Op.LOAD, 0,           # push x
            Op.CONST, 1,          # push 3
            Op.CMP_LT_INT,            # x < 3
            Op.JUMP_IF_FALSE, 20, # exit loop if false
            Op.LOAD, 0,           # push x
            Op.CONST, 2,          # push 1
            Op.ADD_INT,           # x + 1
            Op.STORE, 0,          # x = x + 1
            Op.JUMP, 4,           # loop back
        ]
        assert chunk.constants == [0, 3, 1]

    def test_compile_nested_loops_break(self):
        # fn main() { for (true) { for (true) { break } break } }
        # break in inner loop should only exit inner loop
        program = Program([
            Function("main", [], None, [
                ForStmt(
                    BoolLiteral(True),
                    [
                        ForStmt(
                            BoolLiteral(True),
                            [BreakStmt()]  # break inner
                        ),
                        BreakStmt()  # break outer
                    ]
                )
            ])
        ])
        result = compile_program(program)

        chunk = result.chunks[result.function_index["main"]]
        # Outer loop:
        # 0: CONST 0 (true)
        # 2: JUMP_IF_FALSE outer_end
        # Inner loop:
        # 4: CONST 1 (true)
        # 6: JUMP_IF_FALSE inner_end
        # 8: JUMP inner_end           <- inner break
        # 10: JUMP 4                   <- inner loop back
        # inner_end: 12
        # 12: JUMP outer_end           <- outer break
        # 14: JUMP 0                   <- outer loop back
        # outer_end: 16
        assert chunk.code == [
            Op.CONST, 0,           # outer: push true
            Op.JUMP_IF_FALSE, 16,  # exit outer if false
            Op.CONST, 1,           # inner: push true
            Op.JUMP_IF_FALSE, 12,  # exit inner if false
            Op.JUMP, 12,           # inner break
            Op.JUMP, 4,            # inner loop back
            Op.JUMP, 16,           # outer break
            Op.JUMP, 0,            # outer loop back
        ]


# =============================================================================
# Unary Expression Compilation
# =============================================================================


class TestUnaryExpressionCompilation:
    def test_compile_unary_minus(self):
        # fn main() { return -5 }
        # Should compile as: CONST 0, CONST 5, SUB_INT, RET
        program = Program([
            Function("main", [], None, [
                ReturnStmt(UnaryExpr("-", IntLiteral(5)))
            ])
        ])
        result = compile_program(program)

        chunk = result.chunks[result.function_index["main"]]
        # -5 compiles as 0 - 5
        assert chunk.code == [Op.CONST, 0, Op.CONST, 1, Op.SUB_INT, Op.RET]
        assert chunk.constants == [0, 5]
