# Zero LSP Server Design

## Overview

A Language Server Protocol (LSP) implementation for Zero, providing IDE features like error diagnostics, go-to-definition, and hover information.

## Goals

- **v1 features:** Diagnostics, go-to-definition, hover
- **Reuse existing code:** Lexer, parser, semantic analysis
- **No duplication:** Single source of truth for language logic
- **Python-only:** Use `pygls` library, defer editor-specific packaging

## Architecture

```
Source Code
     ↓
  Lexer (with positions) → Tokens with line/column
     ↓
  Parser (with spans) → AST with Span on each node
     ↓
  Semantic Analysis → Type info, errors
     ↓
  LSP Server → JSON-RPC to editor
```

## Position Tracking

### Span dataclass

```python
@dataclass(frozen=True)
class Span:
    start_line: int
    start_column: int
    end_line: int
    end_column: int
```

### Base Node class

All AST nodes inherit from `Node` with an optional span (defaults to `None` for test convenience):

```python
@dataclass(frozen=True)
class Node:
    span: Span | None = field(default=None, kw_only=True)

@dataclass(frozen=True)
class IntLiteral(Node):
    value: int

@dataclass(frozen=True)
class Function(Node):
    name: str
    params: list
    return_type: str
    body: list
    name_span: Span | None = field(default=None, kw_only=True)  # span of just the identifier
```

Nodes have two spans:
- `span` - the full node (entire function definition, full call expression)
- `name_span` - just the identifier (for highlighting on hover, precise navigation)

### Token positions

Extend `Token` to track position:

```python
@dataclass
class Token:
    type: TokenType
    value: object = None
    line: int = 1
    column: int = 1
```

Lexer tracks current line/column as it scans.

### Validation at boundary

Parser validates all spans are set before returning:

```python
def parse(tokens) -> Program:
    program = Parser(tokens).parse_program()
    _validate_spans(program)
    return program

def _validate_spans(node):
    """Walk AST, assert any field ending in 'span' is not None."""
    if not hasattr(node, '__dataclass_fields__'):
        return

    for field in fields(node):
        value = getattr(node, field.name)

        if field.name.endswith('span') and value is None:
            raise AssertionError(f"{type(node).__name__} missing {field.name}")

        if isinstance(value, list):
            for item in value:
                _validate_spans(item)
        elif hasattr(value, '__dataclass_fields__'):
            _validate_spans(value)
```

This means:
- Tests construct ASTs directly → no validation → None spans OK
- Production goes through `parse()` → validated → spans guaranteed

## Project Structure

```
zero/
├── ast.py          # Add Span, Node base class
├── lexer.py        # Track line/column in tokens
├── parser.py       # Attach spans to AST nodes, validate
├── semantic.py     # Unchanged - reuse for diagnostics
└── lsp/
    ├── server.py   # Main LSP server, pygls setup
    └── features.py # Diagnostics, hover, go-to-def handlers
```

## LSP Server Implementation

### server.py

```python
from pygls.server import LanguageServer
from lsprotocol import types

server = LanguageServer("zero-lsp", "0.1.0")

@server.feature(types.TEXT_DOCUMENT_DID_OPEN)
def did_open(params):
    publish_diagnostics(params.text_document.uri, params.text_document.text)

@server.feature(types.TEXT_DOCUMENT_DID_CHANGE)
def did_change(params):
    text = params.content_changes[0].text
    publish_diagnostics(params.text_document.uri, text)

if __name__ == "__main__":
    server.start_io()
```

### features.py

```python
def get_diagnostics(source: str) -> list[types.Diagnostic]:
    """Parse and analyze source, return any errors as diagnostics."""
    diagnostics = []

    try:
        tokens = tokenize(source)
    except SyntaxError as e:
        return [make_diagnostic(e)]

    try:
        ast = parse(tokens)
    except SyntaxError as e:
        return [make_diagnostic(e)]

    try:
        SemanticAnalyzer(ast).analyze()
    except SemanticError as e:
        return [make_diagnostic(e)]

    return diagnostics

def find_node_at_position(ast: Program, line: int, column: int) -> Node | None:
    """Walk AST, return the innermost node whose span contains the position.

    Algorithm:
    1. Traverse all nodes depth-first
    2. Collect nodes whose span contains (line, column)
    3. Return the innermost (most deeply nested) match

    Returns None if position is outside all nodes (whitespace, comments, etc).
    """
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

    def walk(node: Node) -> Node | None:
        """Return innermost matching node, or None."""
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
    """Find the definition for a reference node.

    Handles:
    - Call → Function definition
    - Identifier → Parameter or local variable (future)

    Returns None if no definition found (e.g., builtin like print).
    """
    if isinstance(node, Call):
        return find_function(ast, node.name)
    if isinstance(node, Identifier):
        # Future: look up in scope chain
        return None
    return None

def find_function(ast: Program, name: str) -> Function | None:
    """Find function definition by name."""
    for func in ast.functions:
        if func.name == name:
            return func
    return None
```

### Error resilience

Wrap handlers to prevent crashes:

```python
def safe_handler(fn):
    def wrapper(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except Exception as e:
            logging.exception("LSP handler error")
            return None
    return wrapper
```

For diagnostics, show internal errors to user:

```python
def get_diagnostics(source: str) -> list[types.Diagnostic]:
    try:
        # ... normal flow ...
    except Exception as e:
        return [types.Diagnostic(
            range=types.Range(start=types.Position(0, 0), end=types.Position(0, 0)),
            message=f"Internal error: {e}",
            severity=types.DiagnosticSeverity.Error,
        )]
```

## LSP Features

### Diagnostics

Show parse and semantic errors as the user types.

- Lexer errors (invalid characters, unterminated strings)
- Parser errors (missing braces, unexpected tokens)
- Semantic errors (undefined variables, type mismatches, missing main)

### Go to Definition

Click on a function call → jump to function definition.

```python
@server.feature(types.TEXT_DOCUMENT_DEFINITION)
@safe_handler
def goto_definition(params):
    doc = server.workspace.get_document(params.text_document.uri)
    ast = parse(tokenize(doc.source))

    node = find_node_at_position(ast, params.position.line, params.position.character)
    if node is None:
        return None

    definition = find_definition(ast, node)
    if definition is None:
        return None

    # Use name_span for precise navigation to the identifier
    target_span = getattr(definition, 'name_span', None) or definition.span
    return types.Location(uri=params.text_document.uri, range=span_to_range(target_span))
```

### Hover

Hover over a function call → show signature.

```python
@server.feature(types.TEXT_DOCUMENT_HOVER)
@safe_handler
def hover(params):
    doc = server.workspace.get_document(params.text_document.uri)
    ast = parse(tokenize(doc.source))

    node = find_node_at_position(ast, params.position.line, params.position.character)
    if node is None:
        return None

    definition = find_definition(ast, node)
    if definition is None:
        return None

    if isinstance(definition, Function):
        sig = format_signature(definition)  # "fn add(a: int, b: int): int"
        return types.Hover(contents=sig)

    return None
```

## Testing Strategy

### Extend existing tests

**test_lexer.py** - Add token position tests:

```python
def test_token_positions_simple():
    tokens = tokenize("fn main() {}")
    assert tokens[0].line == 1 and tokens[0].column == 1   # fn
    assert tokens[1].line == 1 and tokens[1].column == 4   # main

def test_token_positions_multiline():
    tokens = tokenize("fn main() {\n  return 1\n}")
    return_tok = [t for t in tokens if t.type == TokenType.RETURN][0]
    assert return_tok.line == 2
    assert return_tok.column == 3
```

**test_parser.py** - Add span tests:

```python
def test_function_spans():
    ast = parse(tokenize("fn main() {}"))
    func = ast.functions[0]
    assert func.name_span == Span(1, 4, 1, 7)  # "main" identifier only
    assert func.span == Span(1, 1, 1, 12)      # entire "fn main() {}"

def test_call_span():
    ast = parse(tokenize("fn main() { foo() }"))
    call = ast.functions[0].body[0].expr
    assert call.span == Span(1, 13, 1, 17)  # "foo()" - full call expression
```

### New LSP tests

**test_lsp_find.py** - `find_node_at_position` and `find_definition`:

```python
def test_find_call():
    ast = parse(tokenize("fn main() { foo() }"))
    node = find_node_at_position(ast, line=1, col=13)
    assert isinstance(node, Call)
    assert node.name == "foo"

def test_find_innermost_node():
    """Position inside nested expression returns innermost node."""
    ast = parse(tokenize("fn main() { foo(1 + 2) }"))
    # Position on the "1" - should return IntLiteral, not the Call
    node = find_node_at_position(ast, line=1, col=17)
    assert isinstance(node, IntLiteral)
    assert node.value == 1

def test_position_outside_any_node():
    ast = parse(tokenize("fn main() {}"))
    node = find_node_at_position(ast, line=1, col=100)
    assert node is None

def test_find_definition_call_to_function():
    ast = parse(tokenize("fn foo() {} fn main() { foo() }"))
    call = find_node_at_position(ast, line=1, col=25)  # the foo() call
    definition = find_definition(ast, call)
    assert isinstance(definition, Function)
    assert definition.name == "foo"

def test_find_definition_builtin_returns_none():
    ast = parse(tokenize("fn main() { print(1) }"))
    call = find_node_at_position(ast, line=1, col=13)  # print()
    definition = find_definition(ast, call)
    assert definition is None  # builtins have no definition in source
```

**test_lsp_diagnostics.py** - Integration:

```python
def test_valid_code_no_diagnostics():
    assert get_diagnostics("fn main() {}") == []

def test_lexer_error():
    diags = get_diagnostics("fn main() { @ }")
    assert len(diags) == 1

def test_semantic_error():
    diags = get_diagnostics("fn foo() {}")  # missing main
    assert len(diags) == 1
    assert "main" in diags[0].message
```

**test_lsp_resilience.py** - Error handling:

```python
def test_unexpected_error_doesnt_crash(monkeypatch):
    monkeypatch.setattr("zero.parser.parse", lambda x: (_ for _ in ()).throw(RuntimeError("boom")))
    diags = get_diagnostics("fn main() {}")
    assert len(diags) == 1
    assert "Internal error" in diags[0].message

def test_empty_source():
    diags = get_diagnostics("")
    assert len(diags) >= 1

def test_binary_garbage():
    diags = get_diagnostics("\x00\x01\x02")
    assert len(diags) >= 1  # errors, not crashes
```

## Running the LSP

```bash
# Install dependencies
uv add pygls lsprotocol

# Run server (stdio mode for editors)
python -m zero.lsp
```

## Editor Setup (deferred)

VS Code extension packaging deferred. For now, use with any editor that supports LSP:

**Neovim:**
```lua
require('lspconfig').zero.setup {
    cmd = { "python", "-m", "zero.lsp" }
}
```

**Helix:**
```toml
[[language]]
name = "zero"
language-server = { command = "python", args = ["-m", "zero.lsp"] }
```

## Implementation Order (TDD)

Each step follows red-green-refactor: write failing test, implement, refactor.

### Phase 1: Position Tracking Infrastructure

**Step 1: Span dataclass**
1. Add `Span` dataclass to `ast.py`
2. Add `Node` base class with `span: Span | None` field

**Step 2: Token positions (TDD)**
1. Write `test_token_positions_simple` and `test_token_positions_multiline` → tests fail
2. Add `line`/`column` fields to `Token`
3. Update `Lexer` to track line/column as it scans → tests pass

**Step 3: AST spans (TDD)**
1. Write `test_function_spans` and `test_call_span` → tests fail
2. Update all AST nodes to inherit from `Node`
3. Add `name_span` field to `Function`
4. Update `Parser` to attach spans from token positions → tests pass

**Step 4: Span validation**
1. Write test that parsing produces valid spans (no None values)
2. Add `_validate_spans()` to parser, call from `parse()`

### Phase 2: LSP Core

**Step 5: find_node_at_position (TDD)**
1. Write `test_find_call`, `test_find_innermost_node`, `test_position_outside_any_node` → tests fail
2. Implement `find_node_at_position()` in `zero/lsp/features.py` → tests pass

**Step 6: find_definition (TDD)**
1. Write `test_find_definition_call_to_function`, `test_find_definition_builtin_returns_none` → tests fail
2. Implement `find_definition()` and `find_function()` → tests pass

**Step 7: Diagnostics (TDD)**
1. Write `test_valid_code_no_diagnostics`, `test_lexer_error`, `test_semantic_error` → tests fail
2. Create `zero/lsp/features.py` with `get_diagnostics()`
3. Add error wrapping for internal errors → tests pass

**Step 8: Resilience (TDD)**
1. Write `test_unexpected_error_doesnt_crash`, `test_empty_source`, `test_binary_garbage` → tests fail
2. Add try/except wrapper returning "Internal error" diagnostic → tests pass

### Phase 3: LSP Server

**Step 9: Server setup**
1. Create `zero/lsp/server.py` with pygls
2. Wire up `did_open`/`did_change` → `publish_diagnostics`
3. Manual test with editor

**Step 10: Go-to-definition**
1. Add `@server.feature(TEXT_DOCUMENT_DEFINITION)` handler
2. Manual test with editor

**Step 11: Hover**
1. Add `@server.feature(TEXT_DOCUMENT_HOVER)` handler
2. Implement `format_signature()`
3. Manual test with editor

### Phase 4: Integration Testing

**Step 12: LSP integration tests**
1. Test full round-trip: source → diagnostics
2. Test go-to-definition returns correct location
3. Test hover returns correct signature
