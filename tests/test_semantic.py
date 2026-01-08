import pytest
from zero.ast import (
    Program,
    Function,
    Param,
    ReturnStmt,
    IntLiteral,
    BoolLiteral,
    ExprStmt,
    VarDecl,
    Assignment,
    Identifier,
    BinaryExpr,
    IfStmt,
    ForStmt,
    BreakStmt,
    ContinueStmt,
)
from zero.semantic import analyze, SemanticError


# =============================================================================
# Main Function Required
# =============================================================================


class TestMainRequired:
    def test_empty_program_missing_main(self):
        program = Program([])
        with pytest.raises(SemanticError, match=r"main"):
            analyze(program)

    def test_program_with_only_other_functions_missing_main(self):
        program = Program([
            Function("foo", [], None, [ReturnStmt(IntLiteral(1))]),
            Function("bar", [], None, [ReturnStmt(IntLiteral(2))]),
        ])
        with pytest.raises(SemanticError, match=r"main"):
            analyze(program)

    def test_program_with_main_passes(self):
        program = Program([
            Function("main", [], None, []),
        ])
        analyze(program)  # should not raise


# =============================================================================
# Main Signature
# =============================================================================


class TestMainSignature:
    def test_main_with_parameters_rejected(self):
        program = Program([
            Function("main", [Param("x", "int")], None, []),
        ])
        with pytest.raises(SemanticError, match=r"main.*parameter"):
            analyze(program)

    def test_main_with_multiple_parameters_rejected(self):
        program = Program([
            Function("main", [Param("a", "int"), Param("b", "int")], None, []),
        ])
        with pytest.raises(SemanticError, match=r"main.*parameter"):
            analyze(program)

    def test_main_with_return_type_rejected(self):
        program = Program([
            Function("main", [], "int", []),
        ])
        with pytest.raises(SemanticError, match=r"main.*return"):
            analyze(program)

    def test_main_with_params_and_return_type_rejected(self):
        program = Program([
            Function("main", [Param("x", "int")], "int", []),
        ])
        with pytest.raises(SemanticError):
            analyze(program)

    def test_main_correct_signature_passes(self):
        program = Program([
            Function("main", [], None, [ReturnStmt(IntLiteral(0))]),
        ])
        analyze(program)  # should not raise


# =============================================================================
# Duplicate Function Names
# =============================================================================


class TestDuplicateFunctions:
    def test_duplicate_function_names_rejected(self):
        program = Program([
            Function("foo", [], None, []),
            Function("foo", [], None, []),
        ])
        with pytest.raises(SemanticError, match=r"duplicate.*foo"):
            analyze(program)

    def test_duplicate_main_rejected(self):
        program = Program([
            Function("main", [], None, []),
            Function("main", [], None, []),
        ])
        with pytest.raises(SemanticError, match=r"duplicate.*main"):
            analyze(program)

    def test_multiple_duplicates_reports_first(self):
        program = Program([
            Function("foo", [], None, []),
            Function("bar", [], None, []),
            Function("foo", [], None, []),  # duplicate
        ])
        with pytest.raises(SemanticError, match=r"duplicate.*foo"):
            analyze(program)

    def test_function_shadows_builtin_rejected(self):
        program = Program([
            Function("main", [], None, []),
            Function("print", [], None, []),  # shadows builtin
        ])
        with pytest.raises(SemanticError, match=r"shadows.*builtin.*print"):
            analyze(program)

    def test_unique_function_names_pass(self):
        program = Program([
            Function("main", [], None, []),
            Function("foo", [], None, []),
            Function("bar", [], None, []),
        ])
        analyze(program)  # should not raise


# =============================================================================
# Combined Cases
# =============================================================================


class TestCombinedValidation:
    def test_valid_program_with_multiple_functions(self):
        program = Program([
            Function("add", [Param("a", "int"), Param("b", "int")], "int", [
                ReturnStmt(IntLiteral(0))
            ]),
            Function("main", [], None, []),
        ])
        analyze(program)  # should not raise

    def test_duplicate_checked_before_main_signature(self):
        # If there are two mains, we should report duplicate first
        program = Program([
            Function("main", [Param("x", "int")], None, []),  # bad signature
            Function("main", [], None, []),  # duplicate
        ])
        with pytest.raises(SemanticError, match=r"duplicate"):
            analyze(program)


# =============================================================================
# Variable Type Checking
# =============================================================================


class TestVariableTypeTracking:
    def test_var_decl_type_recorded(self):
        # x: int = 5 should work fine
        program = Program([
            Function("main", [], None, [
                VarDecl("x", "int", IntLiteral(5)),
            ]),
        ])
        analyze(program)  # should not raise

    def test_assignment_type_mismatch(self):
        # x: int = 5; x = "hello" should fail
        from zero.ast import StringLiteral
        program = Program([
            Function("main", [], None, [
                VarDecl("x", "int", IntLiteral(5)),
                Assignment("x", StringLiteral("hello")),
            ]),
        ])
        with pytest.raises(SemanticError, match=r"type"):
            analyze(program)

    def test_undefined_variable_in_assignment(self):
        # x = 5 without declaration should fail
        program = Program([
            Function("main", [], None, [
                Assignment("x", IntLiteral(5)),
            ]),
        ])
        with pytest.raises(SemanticError, match=r"undefined"):
            analyze(program)

    def test_undefined_variable_in_expression(self):
        # return x without declaration should fail
        program = Program([
            Function("main", [], None, [
                ReturnStmt(Identifier("x")),
            ]),
        ])
        with pytest.raises(SemanticError, match=r"undefined"):
            analyze(program)

    def test_variable_used_after_declaration(self):
        # x: int = 5; return x should work
        program = Program([
            Function("main", [], None, [
                VarDecl("x", "int", IntLiteral(5)),
                ReturnStmt(Identifier("x")),
            ]),
        ])
        analyze(program)  # should not raise

    def test_parameter_is_defined(self):
        # fn foo(x: int) { return x } should work
        program = Program([
            Function("foo", [Param("x", "int")], "int", [
                ReturnStmt(Identifier("x")),
            ]),
            Function("main", [], None, []),
        ])
        analyze(program)  # should not raise

    def test_var_decl_type_mismatch(self):
        # x: int = "hello" should fail - declaring int with string value
        from zero.ast import StringLiteral
        program = Program([
            Function("main", [], None, [
                VarDecl("x", "int", StringLiteral("hello")),
            ]),
        ])
        with pytest.raises(SemanticError, match=r"type"):
            analyze(program)


# =============================================================================
# If Condition Type Checking
# =============================================================================


class TestIfConditionTypeChecking:
    def test_if_condition_must_be_bool(self):
        # if (5) { ... } should fail - int is not bool
        program = Program([
            Function("main", [], None, [
                IfStmt(IntLiteral(5), [ReturnStmt(IntLiteral(0))], None),
            ]),
        ])
        with pytest.raises(SemanticError, match=r"condition.*bool|bool.*condition"):
            analyze(program)

    def test_if_condition_with_comparison_ok(self):
        # if (x > 0) { ... } should work - comparison returns bool
        program = Program([
            Function("main", [], None, [
                VarDecl("x", "int", IntLiteral(5)),
                IfStmt(
                    BinaryExpr(">", Identifier("x"), IntLiteral(0)),
                    [ReturnStmt(IntLiteral(1))],
                    None,
                ),
            ]),
        ])
        analyze(program)  # should not raise

    def test_if_condition_with_bool_literal_ok(self):
        # if (true) { ... } should work
        program = Program([
            Function("main", [], None, [
                IfStmt(BoolLiteral(True), [ReturnStmt(IntLiteral(1))], None),
            ]),
        ])
        analyze(program)  # should not raise

    def test_if_condition_with_string_fails(self):
        # if ("hello") { ... } should fail
        from zero.ast import StringLiteral
        program = Program([
            Function("main", [], None, [
                IfStmt(StringLiteral("hello"), [ReturnStmt(IntLiteral(1))], None),
            ]),
        ])
        with pytest.raises(SemanticError, match=r"condition.*bool|bool.*condition"):
            analyze(program)


# =============================================================================
# For Loop Analysis
# =============================================================================


class TestForLoopAnalysis:
    def test_for_condition_must_be_bool(self):
        # for (5) { ... } should fail
        program = Program([
            Function("main", [], None, [
                ForStmt(IntLiteral(5), [BreakStmt()]),
            ]),
        ])
        with pytest.raises(SemanticError, match=r"condition.*bool|bool.*condition"):
            analyze(program)

    def test_for_condition_with_comparison_ok(self):
        # for (i < 10) { ... } should work
        program = Program([
            Function("main", [], None, [
                VarDecl("i", "int", IntLiteral(0)),
                ForStmt(
                    BinaryExpr("<", Identifier("i"), IntLiteral(10)),
                    [BreakStmt()],
                ),
            ]),
        ])
        analyze(program)  # should not raise

    def test_for_condition_with_bool_literal_ok(self):
        # for (true) { break } should work
        program = Program([
            Function("main", [], None, [
                ForStmt(BoolLiteral(True), [BreakStmt()]),
            ]),
        ])
        analyze(program)  # should not raise

    def test_break_outside_loop_error(self):
        # fn main() { break } should fail
        program = Program([
            Function("main", [], None, [
                BreakStmt(),
            ]),
        ])
        with pytest.raises(SemanticError, match=r"break.*outside.*loop|break.*loop"):
            analyze(program)

    def test_continue_outside_loop_error(self):
        # fn main() { continue } should fail
        program = Program([
            Function("main", [], None, [
                ContinueStmt(),
            ]),
        ])
        with pytest.raises(SemanticError, match=r"continue.*outside.*loop|continue.*loop"):
            analyze(program)

    def test_break_inside_loop_ok(self):
        # for (true) { break } should work
        program = Program([
            Function("main", [], None, [
                ForStmt(BoolLiteral(True), [BreakStmt()]),
            ]),
        ])
        analyze(program)  # should not raise

    def test_continue_inside_loop_ok(self):
        # for (true) { continue } should work
        program = Program([
            Function("main", [], None, [
                ForStmt(BoolLiteral(True), [ContinueStmt()]),
            ]),
        ])
        analyze(program)  # should not raise

    def test_break_in_nested_loop_ok(self):
        # for (true) { for (true) { break } } should work
        program = Program([
            Function("main", [], None, [
                ForStmt(BoolLiteral(True), [
                    ForStmt(BoolLiteral(True), [BreakStmt()]),
                ]),
            ]),
        ])
        analyze(program)  # should not raise

    def test_for_block_scoping(self):
        # Variables declared inside loop should not be visible outside
        # for (true) { x: int = 5 }
        # return x  <-- should fail
        program = Program([
            Function("main", [], None, [
                ForStmt(BoolLiteral(True), [
                    VarDecl("x", "int", IntLiteral(5)),
                    BreakStmt(),
                ]),
                ReturnStmt(Identifier("x")),  # x not visible here
            ]),
        ])
        with pytest.raises(SemanticError, match=r"undefined"):
            analyze(program)

    def test_variable_visible_inside_loop(self):
        # x: int = 5; for (x < 10) { x = x + 1 } should work
        program = Program([
            Function("main", [], None, [
                VarDecl("x", "int", IntLiteral(5)),
                ForStmt(
                    BinaryExpr("<", Identifier("x"), IntLiteral(10)),
                    [Assignment("x", BinaryExpr("+", Identifier("x"), IntLiteral(1)))],
                ),
            ]),
        ])
        analyze(program)  # should not raise
