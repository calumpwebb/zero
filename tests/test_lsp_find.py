from zero.lexer import tokenize
from zero.parser import parse
from zero.ast import Call, IntLiteral, Function
from zero.lsp.features import find_node_at_position, find_definition

def test_find_call():
    ast = parse(tokenize("fn main() { foo() }"))
    node = find_node_at_position(ast, line=1, column=13)
    assert isinstance(node, Call)
    assert node.name == "foo"

def test_find_innermost_node():
    """Position inside nested expression returns innermost node."""
    ast = parse(tokenize("fn main() { foo(1 + 2) }"))
    # Position on the "1" - should return IntLiteral, not the Call
    node = find_node_at_position(ast, line=1, column=17)
    assert isinstance(node, IntLiteral)
    assert node.value == 1

def test_position_outside_any_node():
    ast = parse(tokenize("fn main() {}"))
    node = find_node_at_position(ast, line=1, column=100)
    assert node is None


def test_find_definition_call_to_function():
    ast = parse(tokenize("fn foo() {} fn main() { foo() }"))
    call = find_node_at_position(ast, line=1, column=25)  # the foo() call
    definition = find_definition(ast, call)
    assert isinstance(definition, Function)
    assert definition.name == "foo"


def test_find_definition_builtin_returns_none():
    ast = parse(tokenize("fn main() { print(1) }"))
    call = find_node_at_position(ast, line=1, column=13)  # print()
    definition = find_definition(ast, call)
    assert definition is None
