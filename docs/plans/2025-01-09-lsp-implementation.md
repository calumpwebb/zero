# Zero LSP Server Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a Language Server Protocol server for Zero with diagnostics, go-to-definition, and hover.

**Architecture:** Add position tracking to lexer/parser, create LSP server using pygls that reuses existing semantic analysis. Validate spans at parser boundary so tests stay unchanged.

**Tech Stack:** Python 3.14+, pygls, lsprotocol, pytest

---

## Task 1: Add Span Dataclass

**Files:**
- Modify: `zero/ast.py`
- Test: `tests/test_parser.py`

**Step 1: Write the test for Span**

Add to `tests/test_parser.py` at the top, after imports:

```python
from zero.ast import Span

class TestSpan:
    def test_span_creation(self):
        span = Span(1, 5, 1, 10)
        assert span.start_line == 1
        assert span.start_column == 5
        assert span.end_line == 1
        assert span.end_column == 10

    def test_span_equality(self):
        span1 = Span(1, 1, 1, 5)
        span2 = Span(1, 1, 1, 5)
        assert span1 == span2

    def test_span_multiline(self):
        span = Span(1, 10, 3, 5)
        assert span.start_line == 1
        assert span.end_line == 3
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_parser.py::TestSpan -v`
Expected: FAIL with "cannot import name 'Span'"

**Step 3: Write minimal implementation**

Add to `zero/ast.py` after the imports:

```python
@dataclass(frozen=True)
class Span:
    start_line: int
    start_column: int
    end_line: int
    end_column: int
```

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_parser.py::TestSpan -v`
Expected: PASS (3 tests)

**Step 5: Commit**

```bash
git add zero/ast.py tests/test_parser.py
git commit -m "feat(ast): add Span dataclass for source positions"
```

---

## Task 2: Add Node Base Class

**Files:**
- Modify: `zero/ast.py`
- Test: `tests/test_parser.py`

**Step 1: Write the test for Node base class**

Add to `tests/test_parser.py`:

```python
from zero.ast import Node

class TestNode:
    def test_node_default_span_is_none(self):
        # Node itself is abstract, test via IntLiteral
        lit = IntLiteral(42)
        assert lit.span is None

    def test_node_with_explicit_span(self):
        span = Span(1, 1, 1, 3)
        lit = IntLiteral(42, span=span)
        assert lit.span == span

    def test_existing_tests_unchanged(self):
        # Existing construction still works without span
        lit = IntLiteral(5)
        assert lit.value == 5
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_parser.py::TestNode -v`
Expected: FAIL with "cannot import name 'Node'" or "unexpected keyword argument 'span'"

**Step 3: Write minimal implementation**

Modify `zero/ast.py`. Add Node base class and update IntLiteral:

```python
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Span:
    start_line: int
    start_column: int
    end_line: int
    end_column: int


@dataclass(frozen=True)
class Node:
    span: Span | None = field(default=None, kw_only=True)


@dataclass(frozen=True)
class IntLiteral(Node):
    value: int
```

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_parser.py::TestNode -v`
Expected: PASS (3 tests)

**Step 5: Run all existing tests to ensure no regressions**

Run: `python -m pytest tests/test_parser.py -v`
Expected: All tests PASS

**Step 6: Commit**

```bash
git add zero/ast.py tests/test_parser.py
git commit -m "feat(ast): add Node base class with optional span"
```

---

## Task 3: Update All AST Nodes to Inherit from Node

**Files:**
- Modify: `zero/ast.py`

**Step 1: Run existing tests to establish baseline**

Run: `python -m pytest -v`
Expected: All tests PASS

**Step 2: Update all AST node classes**

Modify `zero/ast.py` - update each class to inherit from Node:

```python
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Span:
    start_line: int
    start_column: int
    end_line: int
    end_column: int


@dataclass(frozen=True)
class Node:
    span: Span | None = field(default=None, kw_only=True)


@dataclass(frozen=True)
class IntLiteral(Node):
    value: int


@dataclass(frozen=True)
class BoolLiteral(Node):
    value: bool


@dataclass(frozen=True)
class StringLiteral(Node):
    value: str


@dataclass(frozen=True)
class Identifier(Node):
    name: str


@dataclass(frozen=True)
class BinaryExpr(Node):
    op: str
    left: "Expr"
    right: "Expr"


@dataclass(frozen=True)
class UnaryExpr(Node):
    op: str
    operand: "Expr"


@dataclass(frozen=True)
class Call(Node):
    name: str
    args: list

    def __eq__(self, other):
        if not isinstance(other, Call):
            return NotImplemented
        return self.name == other.name and list(self.args) == list(other.args) and self.span == other.span


Expr = IntLiteral | BoolLiteral | StringLiteral | Identifier | BinaryExpr | UnaryExpr | Call


@dataclass(frozen=True)
class ReturnStmt(Node):
    expr: Expr


@dataclass(frozen=True)
class ExprStmt(Node):
    expr: Expr


@dataclass(frozen=True)
class VarDecl(Node):
    name: str
    type: str
    value: "Expr"


@dataclass(frozen=True)
class Assignment(Node):
    name: str
    value: "Expr"


@dataclass(frozen=True)
class IfStmt(Node):
    condition: "Expr"
    then_body: list
    else_body: list | None

    def __eq__(self, other):
        if not isinstance(other, IfStmt):
            return NotImplemented
        return (
            self.condition == other.condition
            and list(self.then_body) == list(other.then_body)
            and (
                (self.else_body is None and other.else_body is None)
                or (
                    self.else_body is not None
                    and other.else_body is not None
                    and list(self.else_body) == list(other.else_body)
                )
            )
            and self.span == other.span
        )


@dataclass(frozen=True)
class ForStmt(Node):
    condition: "Expr"
    body: list

    def __eq__(self, other):
        if not isinstance(other, ForStmt):
            return NotImplemented
        return self.condition == other.condition and list(self.body) == list(other.body) and self.span == other.span


@dataclass(frozen=True)
class BreakStmt(Node):
    pass


@dataclass(frozen=True)
class ContinueStmt(Node):
    pass


Stmt = ReturnStmt | ExprStmt | VarDecl | Assignment | IfStmt | ForStmt | BreakStmt | ContinueStmt


@dataclass(frozen=True)
class Param(Node):
    name: str
    type: str


@dataclass(frozen=True)
class Function(Node):
    name: str
    params: list
    return_type: str
    body: list

    def __eq__(self, other):
        if not isinstance(other, Function):
            return NotImplemented
        return (
            self.name == other.name
            and list(self.params) == list(other.params)
            and self.return_type == other.return_type
            and list(self.body) == list(other.body)
            and self.span == other.span
        )


@dataclass(frozen=True)
class Program(Node):
    functions: list

    def __eq__(self, other):
        if not isinstance(other, Program):
            return NotImplemented
        return list(self.functions) == list(other.functions) and self.span == other.span
```

**Step 3: Run all tests to verify no regressions**

Run: `python -m pytest -v`
Expected: All tests PASS

**Step 4: Commit**

```bash
git add zero/ast.py
git commit -m "refactor(ast): update all nodes to inherit from Node base class"
```

---

## Task 4: Add Position Tracking to Token

**Files:**
- Modify: `zero/lexer.py`
- Test: `tests/test_lexer.py`

**Step 1: Write failing tests for token positions**

Add to `tests/test_lexer.py`:

```python
class TestTokenPositions:
    def test_single_token_position(self):
        tokens = tokenize("fn")
        assert tokens[0].line == 1
        assert tokens[0].column == 1

    def test_multiple_tokens_same_line(self):
        tokens = tokenize("fn main")
        # fn at column 1
        assert tokens[0].line == 1
        assert tokens[0].column == 1
        # main at column 4
        assert tokens[1].line == 1
        assert tokens[1].column == 4

    def test_multiline_positions(self):
        source = "fn main() {\n  return 1\n}"
        tokens = tokenize(source)
        # Find return token
        return_tok = [t for t in tokens if t.type == TokenType.RETURN][0]
        assert return_tok.line == 2
        assert return_tok.column == 3

    def test_position_after_spaces(self):
        tokens = tokenize("   fn")
        assert tokens[0].line == 1
        assert tokens[0].column == 4

    def test_string_token_position(self):
        tokens = tokenize('"hello"')
        assert tokens[0].line == 1
        assert tokens[0].column == 1

    def test_integer_token_position(self):
        tokens = tokenize("  42")
        assert tokens[0].line == 1
        assert tokens[0].column == 3
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_lexer.py::TestTokenPositions -v`
Expected: FAIL with "Token has no attribute 'line'"

**Step 3: Update Token dataclass**

Modify `zero/lexer.py`:

```python
@dataclass
class Token:
    type: TokenType
    value: object = None
    line: int = 1
    column: int = 1
```

**Step 4: Run test - still fails (lexer not tracking yet)**

Run: `python -m pytest tests/test_lexer.py::TestTokenPositions -v`
Expected: FAIL (positions all default to 1)

**Step 5: Update Lexer to track positions**

Modify `zero/lexer.py` - update Lexer class:

```python
class Lexer:
    def __init__(self, source):
        self.source = source
        self.pos = 0
        self.line = 1
        self.column = 1

    def tokenize(self):
        tokens = []
        while not self.at_end():
            token = self.next_token()
            if token:
                tokens.append(token)
        tokens.append(Token(TokenType.EOF, line=self.line, column=self.column))
        return tokens

    def at_end(self):
        return self.pos >= len(self.source)

    def current(self):
        return self.source[self.pos]

    def peek(self, offset=1):
        pos = self.pos + offset
        if pos >= len(self.source):
            return "\0"
        return self.source[pos]

    def advance(self):
        char = self.source[self.pos]
        self.pos += 1
        if char == "\n":
            self.line += 1
            self.column = 1
        else:
            self.column += 1
        return char

    def next_token(self):
        if self.at_end():
            return None

        char = self.current()

        if char.isspace():
            self.advance()
            return None

        if char == "#":
            self.skip_comment()
            return None

        # Record position BEFORE consuming the token
        token_line = self.line
        token_column = self.column

        if char.isdigit():
            return self.read_number(token_line, token_column)

        if char == '"':
            return self.read_string(token_line, token_column)

        if char.isalpha() or char == "_":
            return self.read_identifier(token_line, token_column)

        # Multi-character operators
        if char == "=" and self.peek() == "=":
            self.advance()
            self.advance()
            return Token(TokenType.EQ, line=token_line, column=token_column)
        if char == "!" and self.peek() == "=":
            self.advance()
            self.advance()
            return Token(TokenType.NE, line=token_line, column=token_column)
        if char == "<" and self.peek() == "=":
            self.advance()
            self.advance()
            return Token(TokenType.LE, line=token_line, column=token_column)
        if char == ">" and self.peek() == "=":
            self.advance()
            self.advance()
            return Token(TokenType.GE, line=token_line, column=token_column)
        if char == "+" and self.peek() == "=":
            self.advance()
            self.advance()
            return Token(TokenType.PLUS_EQUAL, line=token_line, column=token_column)
        if char == "-" and self.peek() == "=":
            self.advance()
            self.advance()
            return Token(TokenType.MINUS_EQUAL, line=token_line, column=token_column)

        # Single-character operators
        if char == "=":
            self.advance()
            return Token(TokenType.ASSIGN, line=token_line, column=token_column)
        if char == "<":
            self.advance()
            return Token(TokenType.LT, line=token_line, column=token_column)
        if char == ">":
            self.advance()
            return Token(TokenType.GT, line=token_line, column=token_column)

        if char in SYMBOLS:
            self.advance()
            return Token(SYMBOLS[char], line=token_line, column=token_column)

        raise SyntaxError(f"Unexpected character: {char}")

    def skip_comment(self):
        while not self.at_end() and self.current() != "\n":
            self.advance()

    def read_number(self, token_line, token_column):
        digits = ""
        while not self.at_end() and self.current().isdigit():
            digits += self.advance()
        value = int(digits)
        if value > 9223372036854775807:  # i64 max
            raise SyntaxError(f"Integer too large: {digits}")
        return Token(TokenType.INT, value, line=token_line, column=token_column)

    def read_string(self, token_line, token_column):
        self.advance()  # consume opening "
        chars = ""
        while not self.at_end() and self.current() != '"':
            chars += self.advance()
        if self.at_end():
            raise SyntaxError("Unterminated string literal")
        self.advance()  # consume closing "
        return Token(TokenType.STRING, chars, line=token_line, column=token_column)

    def read_identifier(self, token_line, token_column):
        ident = ""
        while not self.at_end() and (self.current().isalnum() or self.current() == "_"):
            ident += self.advance()
        if ident in KEYWORDS:
            return Token(KEYWORDS[ident], line=token_line, column=token_column)
        return Token(TokenType.IDENT, ident, line=token_line, column=token_column)
```

**Step 6: Run test to verify it passes**

Run: `python -m pytest tests/test_lexer.py::TestTokenPositions -v`
Expected: PASS (6 tests)

**Step 7: Run all lexer tests to check for regressions**

Run: `python -m pytest tests/test_lexer.py -v`
Expected: All tests PASS

**Step 8: Commit**

```bash
git add zero/lexer.py tests/test_lexer.py
git commit -m "feat(lexer): add line/column tracking to tokens"
```

---

## Task 5: Add Span Validation to Parser

**Files:**
- Modify: `zero/parser.py`
- Test: `tests/test_parser.py`

**Step 1: Write failing test for span validation**

Add to `tests/test_parser.py`:

```python
class TestSpanValidation:
    def test_parser_validates_spans_on_output(self):
        """Parser output should have all spans set."""
        from zero.lexer import tokenize
        from zero.parser import parse

        ast = parse(tokenize("fn main() {}"))
        # Should not raise - spans are set
        assert ast.functions[0].span is not None

    def test_validation_catches_missing_span(self):
        """_validate_spans should catch missing spans."""
        from zero.parser import _validate_spans

        # Manually construct node without span
        func = Function("test", [], None, [])
        program = Program([func])

        with pytest.raises(AssertionError, match="missing span"):
            _validate_spans(program)
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_parser.py::TestSpanValidation -v`
Expected: FAIL with "cannot import name '_validate_spans'" or span is None

**Step 3: Add _validate_spans function**

Add to `zero/parser.py` after imports:

```python
from dataclasses import fields


def _validate_spans(node):
    """Walk AST, assert any field ending in 'span' is not None."""
    if not hasattr(node, "__dataclass_fields__"):
        return

    for f in fields(node):
        value = getattr(node, f.name)

        if f.name.endswith("span") and value is None:
            raise AssertionError(f"{type(node).__name__} missing {f.name}")

        if isinstance(value, list):
            for item in value:
                _validate_spans(item)
        elif hasattr(value, "__dataclass_fields__"):
            _validate_spans(value)
```

**Step 4: Run validation test - first part should still fail**

Run: `python -m pytest tests/test_parser.py::TestSpanValidation::test_validation_catches_missing_span -v`
Expected: PASS

Run: `python -m pytest tests/test_parser.py::TestSpanValidation::test_parser_validates_spans_on_output -v`
Expected: FAIL (parser not attaching spans yet)

**Step 5: Commit validation function**

```bash
git add zero/parser.py tests/test_parser.py
git commit -m "feat(parser): add _validate_spans function"
```

---

## Task 6: Update Parser to Attach Spans

**Files:**
- Modify: `zero/parser.py`

**Step 1: Update Parser to use token positions for spans**

This is a larger change. Update `zero/parser.py` to attach spans to AST nodes:

```python
from zero.lexer import Token, TokenType
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
    Span,
)
from dataclasses import fields


def _validate_spans(node):
    """Walk AST, assert any field ending in 'span' is not None."""
    if not hasattr(node, "__dataclass_fields__"):
        return

    for f in fields(node):
        value = getattr(node, f.name)

        if f.name.endswith("span") and value is None:
            raise AssertionError(f"{type(node).__name__} missing {f.name}")

        if isinstance(value, list):
            for item in value:
                _validate_spans(item)
        elif hasattr(value, "__dataclass_fields__"):
            _validate_spans(value)


def _make_span(token: Token) -> Span:
    """Create a span from a single token."""
    # For simplicity, span covers just the token
    # End column is start + length of token (approximation)
    return Span(token.line, token.column, token.line, token.column)


def _span_from_to(start: Token, end: Token) -> Span:
    """Create a span from start token to end token."""
    return Span(start.line, start.column, end.line, end.column)


class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def current(self):
        if self.pos >= len(self.tokens):
            return Token(TokenType.EOF)
        return self.tokens[self.pos]

    def peek(self, offset=0):
        pos = self.pos + offset
        if pos >= len(self.tokens):
            return Token(TokenType.EOF)
        return self.tokens[pos]

    def advance(self):
        token = self.current()
        self.pos += 1
        return token

    def check(self, type):
        return self.current().type == type

    def match(self, type):
        if self.check(type):
            self.advance()
            return True
        return False

    def expect(self, type, message):
        if not self.check(type):
            raise SyntaxError(message)
        return self.advance()

    def at_end(self):
        return self.check(TokenType.EOF)

    def parse_expression(self):
        return self.parse_comparison()

    def parse_comparison(self):
        left = self.parse_additive()

        start_token = self.current()
        if self.check(TokenType.EQ):
            self.advance()
            right = self.parse_additive()
            return BinaryExpr("==", left, right, span=_span_from_to(start_token, self.tokens[self.pos - 1]))
        if self.check(TokenType.NE):
            self.advance()
            right = self.parse_additive()
            return BinaryExpr("!=", left, right, span=_span_from_to(start_token, self.tokens[self.pos - 1]))
        if self.check(TokenType.LT):
            self.advance()
            right = self.parse_additive()
            return BinaryExpr("<", left, right, span=_span_from_to(start_token, self.tokens[self.pos - 1]))
        if self.check(TokenType.GT):
            self.advance()
            right = self.parse_additive()
            return BinaryExpr(">", left, right, span=_span_from_to(start_token, self.tokens[self.pos - 1]))
        if self.check(TokenType.LE):
            self.advance()
            right = self.parse_additive()
            return BinaryExpr("<=", left, right, span=_span_from_to(start_token, self.tokens[self.pos - 1]))
        if self.check(TokenType.GE):
            self.advance()
            right = self.parse_additive()
            return BinaryExpr(">=", left, right, span=_span_from_to(start_token, self.tokens[self.pos - 1]))

        return left

    def parse_additive(self):
        left = self.parse_multiplicative()

        while self.check(TokenType.PLUS) or self.check(TokenType.MINUS):
            op_token = self.current()
            if self.match(TokenType.PLUS):
                right = self.parse_multiplicative()
                left = BinaryExpr("+", left, right, span=_make_span(op_token))
            elif self.match(TokenType.MINUS):
                right = self.parse_multiplicative()
                left = BinaryExpr("-", left, right, span=_make_span(op_token))

        return left

    def parse_multiplicative(self):
        left = self.parse_unary()

        while self.check(TokenType.STAR) or self.check(TokenType.PERCENT):
            op_token = self.current()
            if self.match(TokenType.STAR):
                right = self.parse_unary()
                left = BinaryExpr("*", left, right, span=_make_span(op_token))
            elif self.match(TokenType.PERCENT):
                right = self.parse_unary()
                left = BinaryExpr("%", left, right, span=_make_span(op_token))

        return left

    def parse_unary(self):
        if self.check(TokenType.MINUS):
            op_token = self.advance()
            operand = self.parse_unary()
            return UnaryExpr("-", operand, span=_make_span(op_token))
        return self.parse_call()

    def parse_call(self):
        expr = self.parse_primary()

        if isinstance(expr, Identifier) and self.match(TokenType.LPAREN):
            args = self.parse_arguments()
            self.expect(TokenType.RPAREN, "Expected ')' after arguments")
            return Call(expr.name, args, span=expr.span)

        return expr

    def parse_arguments(self):
        args = []

        if not self.check(TokenType.RPAREN):
            args.append(self.parse_expression())
            while self.match(TokenType.COMMA):
                args.append(self.parse_expression())

        return args

    def parse_primary(self):
        token = self.current()

        if token.type == TokenType.INT:
            self.advance()
            return IntLiteral(token.value, span=_make_span(token))

        if token.type == TokenType.TRUE:
            self.advance()
            return BoolLiteral(True, span=_make_span(token))

        if token.type == TokenType.FALSE:
            self.advance()
            return BoolLiteral(False, span=_make_span(token))

        if token.type == TokenType.STRING:
            self.advance()
            return StringLiteral(token.value, span=_make_span(token))

        if token.type == TokenType.IDENT:
            self.advance()
            return Identifier(token.name if hasattr(token, 'name') else token.value, span=_make_span(token))

        if self.match(TokenType.LPAREN):
            expr = self.parse_expression()
            self.expect(TokenType.RPAREN, "Expected ')' after expression")
            return expr

        raise SyntaxError(f"Unexpected token: {token.type}")

    def parse_statement(self):
        token = self.current()

        if self.match(TokenType.RETURN):
            expr = self.parse_expression()
            return ReturnStmt(expr, span=_make_span(token))

        if self.match(TokenType.IF):
            self.expect(TokenType.LPAREN, "Expected '(' after 'if'")
            condition = self.parse_expression()
            self.expect(TokenType.RPAREN, "Expected ')' after condition")
            self.expect(TokenType.LBRACE, "Expected '{' before then block")
            then_body = self.parse_block()
            self.expect(TokenType.RBRACE, "Expected '}' after then block")

            else_body = None
            if self.match(TokenType.ELSE):
                self.expect(TokenType.LBRACE, "Expected '{' before else block")
                else_body = self.parse_block()
                self.expect(TokenType.RBRACE, "Expected '}' after else block")

            return IfStmt(condition, then_body, else_body, span=_make_span(token))

        if self.match(TokenType.FOR):
            self.expect(TokenType.LPAREN, "Expected '(' after 'for'")
            condition = self.parse_expression()
            self.expect(TokenType.RPAREN, "Expected ')' after condition")
            self.expect(TokenType.LBRACE, "Expected '{' before loop body")
            body = self.parse_block()
            self.expect(TokenType.RBRACE, "Expected '}' after loop body")
            return ForStmt(condition, body, span=_make_span(token))

        if self.match(TokenType.BREAK):
            return BreakStmt(span=_make_span(token))

        if self.match(TokenType.CONTINUE):
            return ContinueStmt(span=_make_span(token))

        if self.check(TokenType.IDENT) and self.peek(1).type == TokenType.COLON:
            name_token = self.advance()
            self.expect(TokenType.COLON, "Expected ':' after variable name")
            type_token = self.expect(TokenType.IDENT, "Expected type")
            self.expect(TokenType.ASSIGN, "Expected '=' in variable declaration")
            value = self.parse_expression()
            return VarDecl(name_token.value, type_token.value, value, span=_make_span(name_token))

        if self.check(TokenType.IDENT) and self.peek(1).type == TokenType.ASSIGN:
            name_token = self.advance()
            self.expect(TokenType.ASSIGN, "Expected '='")
            value = self.parse_expression()
            return Assignment(name_token.value, value, span=_make_span(name_token))

        if self.check(TokenType.IDENT) and self.peek(1).type == TokenType.PLUS_EQUAL:
            name_token = self.advance()
            self.advance()
            value = self.parse_expression()
            return Assignment(name_token.value, BinaryExpr("+", Identifier(name_token.value, span=_make_span(name_token)), value, span=_make_span(name_token)), span=_make_span(name_token))

        if self.check(TokenType.IDENT) and self.peek(1).type == TokenType.MINUS_EQUAL:
            name_token = self.advance()
            self.advance()
            value = self.parse_expression()
            return Assignment(name_token.value, BinaryExpr("-", Identifier(name_token.value, span=_make_span(name_token)), value, span=_make_span(name_token)), span=_make_span(name_token))

        expr = self.parse_expression()
        return ExprStmt(expr, span=expr.span)

    def parse_params(self):
        params = []

        if self.check(TokenType.EOF) or self.check(TokenType.RPAREN):
            return params

        params.append(self.parse_param())

        while self.match(TokenType.COMMA):
            params.append(self.parse_param())

        return params

    def parse_param(self):
        name_token = self.expect(TokenType.IDENT, "Expected parameter name")
        self.expect(TokenType.COLON, "Expected ':' after parameter name")
        type_token = self.expect(TokenType.IDENT, "Expected parameter type")
        return Param(name_token.value, type_token.value, span=_make_span(name_token))

    def parse_function(self):
        fn_token = self.expect(TokenType.FN, "Expected 'fn'")
        name_token = self.expect(TokenType.IDENT, "Expected function name")
        name = name_token.value

        self.expect(TokenType.LPAREN, "Expected '(' after function name")
        params = self.parse_params()
        self.expect(TokenType.RPAREN, "Expected ')' after parameters")

        return_type = None
        if self.match(TokenType.COLON):
            type_token = self.expect(TokenType.IDENT, "Expected return type")
            return_type = type_token.value

        self.expect(TokenType.LBRACE, "Expected '{' before function body")
        body = self.parse_block()
        self.expect(TokenType.RBRACE, "Expected '}' after function body")

        return Function(name, params, return_type, body, span=_make_span(name_token))

    def parse_block(self):
        statements = []

        while not self.check(TokenType.RBRACE) and not self.at_end():
            statements.append(self.parse_statement())

        return statements

    def parse_program(self):
        functions = []
        start_token = self.current()

        while not self.at_end():
            functions.append(self.parse_function())

        return Program(functions, span=_make_span(start_token))


def parse(tokens):
    program = Parser(tokens).parse_program()
    _validate_spans(program)
    return program
```

**Step 2: Run all tests**

Run: `python -m pytest -v`
Expected: All tests PASS (existing tests should still work, validation test should now pass)

**Step 3: Commit**

```bash
git add zero/parser.py
git commit -m "feat(parser): attach spans to all AST nodes"
```

---

## Task 7: Add Parser Span Tests

**Files:**
- Modify: `tests/test_parser.py`

**Step 1: Add specific span tests**

Add to `tests/test_parser.py`:

```python
class TestParserSpans:
    def test_function_span_points_to_name(self):
        from zero.lexer import tokenize
        ast = parse(tokenize("fn main() {}"))
        func = ast.functions[0]
        # "main" starts at column 4
        assert func.span.start_line == 1
        assert func.span.start_column == 4

    def test_call_span(self):
        from zero.lexer import tokenize
        ast = parse(tokenize("fn main() { foo() }"))
        call = ast.functions[0].body[0].expr
        assert call.span.start_line == 1
        assert call.span.start_column == 13

    def test_int_literal_span(self):
        from zero.lexer import tokenize
        ast = parse(tokenize("fn main() { return 42 }"))
        ret = ast.functions[0].body[0]
        assert ret.expr.span.start_column == 20

    def test_multiline_spans(self):
        from zero.lexer import tokenize
        source = """fn main() {
  return 1
}"""
        ast = parse(tokenize(source))
        ret = ast.functions[0].body[0]
        assert ret.span.start_line == 2
```

**Step 2: Run tests**

Run: `python -m pytest tests/test_parser.py::TestParserSpans -v`
Expected: PASS

**Step 3: Commit**

```bash
git add tests/test_parser.py
git commit -m "test(parser): add span position tests"
```

---

## Task 8: Install LSP Dependencies

**Files:**
- Modify: `pyproject.toml`

**Step 1: Add pygls dependency**

Run: `uv add pygls lsprotocol`

**Step 2: Verify installation**

Run: `python -c "import pygls; import lsprotocol; print('OK')"`
Expected: OK

**Step 3: Commit**

```bash
git add pyproject.toml uv.lock
git commit -m "chore: add pygls and lsprotocol dependencies"
```

---

## Task 9: Create LSP Server Skeleton

**Files:**
- Create: `zero/lsp/server.py`

**Step 1: Create the LSP server**

Create `zero/lsp/server.py`:

```python
from pygls.server import LanguageServer
from lsprotocol import types

server = LanguageServer("zero-lsp", "0.1.0")


@server.feature(types.TEXT_DOCUMENT_DID_OPEN)
def did_open(params: types.DidOpenTextDocumentParams):
    """Handle document open."""
    _publish_diagnostics(params.text_document.uri, params.text_document.text)


@server.feature(types.TEXT_DOCUMENT_DID_CHANGE)
def did_change(params: types.DidChangeTextDocumentParams):
    """Handle document change."""
    text = params.content_changes[0].text
    _publish_diagnostics(params.text_document.uri, text)


def _publish_diagnostics(uri: str, source: str):
    """Parse source and publish diagnostics."""
    from zero.lsp.features import get_diagnostics

    diagnostics = get_diagnostics(source)
    server.publish_diagnostics(uri, diagnostics)


def main():
    server.start_io()


if __name__ == "__main__":
    main()
```

**Step 2: Create `__main__.py` for module execution**

Create `zero/lsp/__main__.py`:

```python
from zero.lsp.server import main

main()
```

**Step 3: Commit**

```bash
git add zero/lsp/server.py zero/lsp/__main__.py
git commit -m "feat(lsp): add LSP server skeleton"
```

---

## Task 10: Implement get_diagnostics

**Files:**
- Create: `zero/lsp/features.py`
- Create: `tests/test_lsp_diagnostics.py`

**Step 1: Write failing tests**

Create `tests/test_lsp_diagnostics.py`:

```python
import pytest
from zero.lsp.features import get_diagnostics


class TestDiagnostics:
    def test_valid_code_no_diagnostics(self):
        diags = get_diagnostics("fn main() {}")
        assert diags == []

    def test_lexer_error(self):
        diags = get_diagnostics("fn main() { @ }")
        assert len(diags) == 1
        assert "Unexpected" in diags[0].message

    def test_parser_error(self):
        diags = get_diagnostics("fn main( {}")
        assert len(diags) == 1
        assert ")" in diags[0].message

    def test_semantic_error_missing_main(self):
        diags = get_diagnostics("fn foo() {}")
        assert len(diags) == 1
        assert "main" in diags[0].message

    def test_semantic_error_undefined_variable(self):
        diags = get_diagnostics("fn main() { return x }")
        assert len(diags) == 1
        assert "undefined" in diags[0].message.lower()
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_lsp_diagnostics.py -v`
Expected: FAIL with "No module named 'zero.lsp.features'"

**Step 3: Implement get_diagnostics**

Create `zero/lsp/features.py`:

```python
import logging
from lsprotocol import types

from zero.lexer import tokenize
from zero.parser import parse
from zero.semantic import analyze, SemanticError


def get_diagnostics(source: str) -> list[types.Diagnostic]:
    """Parse and analyze source, return diagnostics for any errors."""
    try:
        return _get_diagnostics_inner(source)
    except Exception as e:
        logging.exception("Unexpected error in get_diagnostics")
        return [
            types.Diagnostic(
                range=types.Range(
                    start=types.Position(line=0, character=0),
                    end=types.Position(line=0, character=0),
                ),
                message=f"Internal error: {e}",
                severity=types.DiagnosticSeverity.Error,
            )
        ]


def _get_diagnostics_inner(source: str) -> list[types.Diagnostic]:
    """Inner implementation without error wrapper."""
    diagnostics = []

    # Lexer errors
    try:
        tokens = tokenize(source)
    except SyntaxError as e:
        diagnostics.append(_make_diagnostic(str(e)))
        return diagnostics

    # Parser errors
    try:
        ast = parse(tokens)
    except SyntaxError as e:
        diagnostics.append(_make_diagnostic(str(e)))
        return diagnostics

    # Semantic errors
    try:
        analyze(ast)
    except SemanticError as e:
        diagnostics.append(_make_diagnostic(str(e)))
        return diagnostics

    return diagnostics


def _make_diagnostic(message: str) -> types.Diagnostic:
    """Create a diagnostic from an error message."""
    # TODO: Extract position from error message when available
    return types.Diagnostic(
        range=types.Range(
            start=types.Position(line=0, character=0),
            end=types.Position(line=0, character=0),
        ),
        message=message,
        severity=types.DiagnosticSeverity.Error,
    )
```

**Step 4: Run tests**

Run: `python -m pytest tests/test_lsp_diagnostics.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add zero/lsp/features.py tests/test_lsp_diagnostics.py
git commit -m "feat(lsp): implement get_diagnostics"
```

---

## Task 11: Add Resilience Tests

**Files:**
- Create: `tests/test_lsp_resilience.py`

**Step 1: Write resilience tests**

Create `tests/test_lsp_resilience.py`:

```python
import pytest
from zero.lsp.features import get_diagnostics


class TestResilience:
    def test_empty_source(self):
        """Empty source should produce error, not crash."""
        diags = get_diagnostics("")
        assert len(diags) >= 1

    def test_binary_garbage(self):
        """Binary garbage should produce error, not crash."""
        diags = get_diagnostics("\x00\x01\x02")
        assert len(diags) >= 1

    def test_unexpected_error_caught(self, monkeypatch):
        """Unexpected errors should be caught and reported."""

        def explode(*args):
            raise RuntimeError("boom")

        monkeypatch.setattr("zero.lsp.features.tokenize", explode)

        diags = get_diagnostics("fn main() {}")
        assert len(diags) == 1
        assert "Internal error" in diags[0].message

    def test_very_long_source(self):
        """Long source should not crash."""
        source = "fn main() { " + "x " * 10000 + "}"
        diags = get_diagnostics(source)
        # Should either parse or error, not crash
        assert isinstance(diags, list)
```

**Step 2: Run tests**

Run: `python -m pytest tests/test_lsp_resilience.py -v`
Expected: PASS

**Step 3: Commit**

```bash
git add tests/test_lsp_resilience.py
git commit -m "test(lsp): add resilience tests"
```

---

## Task 12: Implement find_node_at_position

**Files:**
- Modify: `zero/lsp/features.py`
- Create: `tests/test_lsp_find.py`

**Step 1: Write failing tests**

Create `tests/test_lsp_find.py`:

```python
import pytest
from zero.lexer import tokenize
from zero.parser import parse
from zero.ast import Call, Identifier, IntLiteral, Function
from zero.lsp.features import find_node_at_position


class TestFindNodeAtPosition:
    def test_find_call(self):
        ast = parse(tokenize("fn main() { foo() }"))
        node = find_node_at_position(ast, line=1, column=13)
        assert isinstance(node, Call)
        assert node.name == "foo"

    def test_find_identifier(self):
        ast = parse(tokenize("fn main() { return x }"))
        node = find_node_at_position(ast, line=1, column=20)
        assert isinstance(node, Identifier)
        assert node.name == "x"

    def test_find_int_literal(self):
        ast = parse(tokenize("fn main() { return 42 }"))
        node = find_node_at_position(ast, line=1, column=20)
        assert isinstance(node, IntLiteral)
        assert node.value == 42

    def test_find_function(self):
        ast = parse(tokenize("fn main() {}"))
        node = find_node_at_position(ast, line=1, column=4)
        assert isinstance(node, Function)
        assert node.name == "main"

    def test_position_outside_returns_none(self):
        ast = parse(tokenize("fn main() {}"))
        node = find_node_at_position(ast, line=100, column=1)
        assert node is None

    def test_multiline(self):
        source = """fn main() {
  foo()
}"""
        ast = parse(tokenize(source))
        node = find_node_at_position(ast, line=2, column=3)
        assert isinstance(node, Call)
        assert node.name == "foo"
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_lsp_find.py -v`
Expected: FAIL with "cannot import name 'find_node_at_position'"

**Step 3: Implement find_node_at_position**

Add to `zero/lsp/features.py`:

```python
from dataclasses import fields
from zero.ast import Node, Span


def find_node_at_position(ast, line: int, column: int):
    """Find the most specific AST node at the given position."""
    return _find_node_recursive(ast, line, column)


def _position_in_span(span: Span | None, line: int, column: int) -> bool:
    """Check if position is within span."""
    if span is None:
        return False

    if line < span.start_line or line > span.end_line:
        return False

    if line == span.start_line and column < span.start_column:
        return False

    if line == span.end_line and column > span.end_column:
        return False

    return True


def _find_node_recursive(node, line: int, column: int):
    """Recursively find the most specific node containing the position."""
    if not hasattr(node, "__dataclass_fields__"):
        return None

    # Check if this node contains the position
    if hasattr(node, "span") and node.span is not None:
        if not _position_in_span(node.span, line, column):
            return None

    # Try to find a more specific child node
    best_match = None
    if hasattr(node, "span") and node.span is not None:
        best_match = node

    for f in fields(node):
        value = getattr(node, f.name)

        if isinstance(value, list):
            for item in value:
                child_match = _find_node_recursive(item, line, column)
                if child_match is not None:
                    best_match = child_match
        elif hasattr(value, "__dataclass_fields__"):
            child_match = _find_node_recursive(value, line, column)
            if child_match is not None:
                best_match = child_match

    return best_match
```

**Step 4: Run tests**

Run: `python -m pytest tests/test_lsp_find.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add zero/lsp/features.py tests/test_lsp_find.py
git commit -m "feat(lsp): implement find_node_at_position"
```

---

## Task 13: Implement Go-to-Definition

**Files:**
- Modify: `zero/lsp/server.py`
- Modify: `zero/lsp/features.py`

**Step 1: Add find_function helper**

Add to `zero/lsp/features.py`:

```python
from zero.ast import Program, Function, Call


def find_function(ast: Program, name: str) -> Function | None:
    """Find a function definition by name."""
    for func in ast.functions:
        if func.name == name:
            return func
    return None


def span_to_range(span: Span) -> types.Range:
    """Convert a Span to an LSP Range (0-indexed)."""
    return types.Range(
        start=types.Position(line=span.start_line - 1, character=span.start_column - 1),
        end=types.Position(line=span.end_line - 1, character=span.end_column - 1),
    )
```

**Step 2: Add go-to-definition to server**

Add to `zero/lsp/server.py`:

```python
@server.feature(types.TEXT_DOCUMENT_DEFINITION)
def goto_definition(params: types.DefinitionParams):
    """Handle go-to-definition request."""
    try:
        from zero.lexer import tokenize
        from zero.parser import parse
        from zero.lsp.features import find_node_at_position, find_function, span_to_range
        from zero.ast import Call

        doc = server.workspace.get_document(params.text_document.uri)

        try:
            ast = parse(tokenize(doc.source))
        except SyntaxError:
            return None

        # LSP positions are 0-indexed, our spans are 1-indexed
        line = params.position.line + 1
        column = params.position.character + 1

        target = find_node_at_position(ast, line, column)

        if isinstance(target, Call):
            func = find_function(ast, target.name)
            if func and func.span:
                return types.Location(
                    uri=params.text_document.uri,
                    range=span_to_range(func.span),
                )

        return None
    except Exception:
        return None
```

**Step 3: Run all tests**

Run: `python -m pytest -v`
Expected: All PASS

**Step 4: Commit**

```bash
git add zero/lsp/server.py zero/lsp/features.py
git commit -m "feat(lsp): implement go-to-definition"
```

---

## Task 14: Implement Hover

**Files:**
- Modify: `zero/lsp/server.py`
- Modify: `zero/lsp/features.py`

**Step 1: Add format_signature helper**

Add to `zero/lsp/features.py`:

```python
def format_signature(func: Function) -> str:
    """Format a function signature for display."""
    params = ", ".join(f"{p.name}: {p.type}" for p in func.params)
    if func.return_type:
        return f"fn {func.name}({params}): {func.return_type}"
    return f"fn {func.name}({params})"
```

**Step 2: Add hover to server**

Add to `zero/lsp/server.py`:

```python
@server.feature(types.TEXT_DOCUMENT_HOVER)
def hover(params: types.HoverParams):
    """Handle hover request."""
    try:
        from zero.lexer import tokenize
        from zero.parser import parse
        from zero.lsp.features import find_node_at_position, find_function, format_signature
        from zero.ast import Call, Identifier
        from zero.builtins import BUILTIN_TYPES

        doc = server.workspace.get_document(params.text_document.uri)

        try:
            ast = parse(tokenize(doc.source))
        except SyntaxError:
            return None

        line = params.position.line + 1
        column = params.position.character + 1

        target = find_node_at_position(ast, line, column)

        if isinstance(target, Call):
            # Check builtins first
            if target.name in BUILTIN_TYPES:
                return types.Hover(contents=f"builtin {target.name}")

            func = find_function(ast, target.name)
            if func:
                return types.Hover(contents=format_signature(func))

        return None
    except Exception:
        return None
```

**Step 3: Run all tests**

Run: `python -m pytest -v`
Expected: All PASS

**Step 4: Commit**

```bash
git add zero/lsp/server.py zero/lsp/features.py
git commit -m "feat(lsp): implement hover"
```

---

## Task 15: Final Integration Test

**Files:**
- Run manual test

**Step 1: Test LSP server starts**

Run: `echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"capabilities":{}}}' | python -m zero.lsp`
Expected: JSON response with server capabilities (may need to ctrl+c after)

**Step 2: Run full test suite**

Run: `python -m pytest -v`
Expected: All tests PASS

**Step 3: Final commit**

```bash
git add -A
git commit -m "feat(lsp): complete v1 LSP server implementation"
```

---

## Summary

After completing all tasks, Zero will have:
- Position tracking in lexer (line/column on tokens)
- Span tracking in parser (all AST nodes have spans)
- LSP server with:
  - Real-time diagnostics (lexer, parser, semantic errors)
  - Go-to-definition (click function call → jump to definition)
  - Hover (show function signature)
- Comprehensive test coverage for all new functionality
