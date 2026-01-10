from dataclasses import fields
from lsprotocol import types
from zero.ast import Node, Span, Program, Call, Identifier, Function
from zero.lexer import tokenize
from zero.parser import parse
from zero.semantic import analyze

def find_node_at_position(ast: Program, line: int, column: int) -> Node | None:
    """Walk AST, return the innermost node whose span contains the position."""

    def contains(span: Span, line: int, col: int) -> bool:
        if span is None:
            return False
        if line < span.start_line or line > span.end_line:
            return False
        if line == span.start_line and col < span.start_column:
            return False
        if line == span.end_line and col > span.end_column:
            return False
        return True

    def walk(node) -> Node | None:
        if not hasattr(node, '__dataclass_fields__'):
            return None

        # Check children first (depth-first, find innermost)
        for field in fields(node):
            value = getattr(node, field.name)
            if isinstance(value, list):
                for item in value:
                    result = walk(item)
                    if result is not None:
                        return result
            elif hasattr(value, '__dataclass_fields__'):
                result = walk(value)
                if result is not None:
                    return result

        # No child matched, check self
        if hasattr(node, 'span') and contains(node.span, line, column):
            return node
        return None

    return walk(ast)


def find_definition(ast: Program, node: Node) -> Node | None:
    """Find the definition for a reference node."""
    if isinstance(node, Call):
        return find_function(ast, node.name)
    if isinstance(node, Identifier):
        return None  # Future: scope chain lookup
    return None


def find_function(ast: Program, name: str) -> Function | None:
    """Find function definition by name."""
    for func in ast.functions:
        if func.name == name:
            return func
    return None


def get_diagnostics(source: str) -> list[types.Diagnostic]:
    """Parse and analyze source, return any errors as diagnostics."""
    try:
        tokens = tokenize(source)
    except SyntaxError as e:
        return [_make_diagnostic(e)]
    except Exception as e:
        return [_internal_error_diagnostic(e)]

    try:
        ast = parse(tokens)
    except SyntaxError as e:
        return [_make_diagnostic(e)]
    except Exception as e:
        return [_internal_error_diagnostic(e)]

    try:
        analyze(ast)
    except Exception as e:
        return [_make_diagnostic(e)]

    return []


def _make_diagnostic(e: Exception) -> types.Diagnostic:
    return types.Diagnostic(
        range=types.Range(
            start=types.Position(0, 0),
            end=types.Position(0, 0)
        ),
        message=str(e),
        severity=types.DiagnosticSeverity.Error,
    )


def _internal_error_diagnostic(e: Exception) -> types.Diagnostic:
    return types.Diagnostic(
        range=types.Range(
            start=types.Position(0, 0),
            end=types.Position(0, 0)
        ),
        message=f"Internal error: {e}",
        severity=types.DiagnosticSeverity.Error,
    )
