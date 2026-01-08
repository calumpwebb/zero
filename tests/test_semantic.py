import pytest
from zero.ast import Program, Function, Param, ReturnStmt, IntLiteral
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
