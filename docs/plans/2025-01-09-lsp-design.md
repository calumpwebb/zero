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
```

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
        analyze(ast)
    except SemanticError as e:
        return [make_diagnostic(e)]

    return diagnostics

def find_node_at_position(ast, line, column):
    """Walk AST, find node whose span contains the position."""
    ...

def find_function(ast, name):
    """Find function definition by name."""
    ...
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

    target = find_node_at_position(ast, params.position.line, params.position.character)

    if isinstance(target, Call):
        func = find_function(ast, target.name)
        if func:
            return types.Location(uri=params.text_document.uri, range=span_to_range(func.span))

    return None
```

### Hover

Hover over a function call → show signature.

```python
@server.feature(types.TEXT_DOCUMENT_HOVER)
@safe_handler
def hover(params):
    doc = server.workspace.get_document(params.text_document.uri)
    ast = parse(tokenize(doc.source))

    target = find_node_at_position(ast, params.position.line, params.position.character)

    if isinstance(target, Call):
        func = find_function(ast, target.name)
        if func:
            sig = format_signature(func)  # "fn add(a: int, b: int): int"
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
def test_function_span():
    ast = parse(tokenize("fn main() {}"))
    func = ast.functions[0]
    assert func.span == Span(1, 4, 1, 8)  # "main"

def test_call_span():
    ast = parse(tokenize("fn main() { foo() }"))
    call = ast.functions[0].body[0].expr
    assert call.span == Span(1, 13, 1, 16)  # "foo"
```

### New LSP tests

**test_lsp_find.py** - `find_node_at_position`:

```python
def test_find_call():
    ast = parse(tokenize("fn main() { foo() }"))
    node = find_node_at_position(ast, line=1, col=13)
    assert isinstance(node, Call)
    assert node.name == "foo"

def test_position_outside_any_node():
    ast = parse(tokenize("fn main() {}"))
    node = find_node_at_position(ast, line=1, col=100)
    assert node is None
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

## Implementation Order

1. Add `Span` dataclass to `ast.py`
2. Add `Node` base class, update AST nodes to inherit
3. Add line/column tracking to `Token` and `Lexer`
4. Update parser to attach spans to AST nodes
5. Add `_validate_spans()` to parser
6. Write span tests (TDD)
7. Create `zero/lsp/server.py` with pygls
8. Implement `get_diagnostics()` with error wrapping
9. Implement `find_node_at_position()` (TDD)
10. Implement go-to-definition
11. Implement hover
12. Write LSP integration tests
