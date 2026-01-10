"""Integration tests for Zero LSP features."""
from lsprotocol import types
from zero.lsp.server import _span_to_range, _format_signature
from zero.lsp.features import get_diagnostics, find_node_at_position, find_definition
from zero.lexer import tokenize
from zero.parser import parse
from zero.ast import Span, Function, Param


class TestDiagnosticsIntegration:
    """Test full diagnostic pipeline."""

    def test_valid_program_no_errors(self):
        source = """fn add(a: int, b: int): int {
    return a + b
}

fn main() {
    print(add(1, 2))
}"""
        diags = get_diagnostics(source)
        assert diags == []

    def test_multiline_program_with_error(self):
        source = """fn foo() {
    return 1
}"""  # missing main
        diags = get_diagnostics(source)
        assert len(diags) == 1
        assert "main" in diags[0].message.lower()


class TestGoToDefinitionIntegration:
    """Test go-to-definition with parsed AST."""

    def test_goto_function_definition(self):
        source = "fn add(a: int): int { return a } fn main() { add(1) }"
        ast = parse(tokenize(source))
        # Find the call to add() - it's around column 46
        node = find_node_at_position(ast, line=1, column=46)
        definition = find_definition(ast, node)
        assert definition is not None
        assert definition.name == "add"
        assert definition.name_span is not None

    def test_goto_builtin_returns_none(self):
        source = "fn main() { print(1) }"
        ast = parse(tokenize(source))
        node = find_node_at_position(ast, line=1, column=13)
        definition = find_definition(ast, node)
        assert definition is None


class TestHoverIntegration:
    """Test hover information."""

    def test_format_signature_no_params(self):
        func = Function(name="main", params=[], return_type="void", body=[])
        sig = _format_signature(func)
        assert sig == "fn main(): void"

    def test_format_signature_with_params(self):
        func = Function(
            name="add",
            params=[Param(name="a", type="int"), Param(name="b", type="int")],
            return_type="int",
            body=[]
        )
        sig = _format_signature(func)
        assert sig == "fn add(a: int, b: int): int"


class TestSpanConversion:
    """Test span to LSP range conversion."""

    def test_span_to_range_converts_to_zero_indexed(self):
        span = Span(1, 1, 1, 5)  # 1-indexed
        range_ = _span_to_range(span)
        assert range_.start.line == 0  # 0-indexed
        assert range_.start.character == 0
        assert range_.end.line == 0
        assert range_.end.character == 4
