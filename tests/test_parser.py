import pytest
from zero.lexer import Token, TokenType
from zero.parser import parse, Parser
from zero.ast import (
    Program,
    Function,
    Param,
    ReturnStmt,
    ExprStmt,
    BinaryExpr,
    Call,
    IntLiteral,
    BoolLiteral,
    StringLiteral,
    Identifier,
)


# Helper to reduce boilerplate for manual token construction
def T(type: TokenType, value: str | int | None = None) -> Token:
    return Token(type, value)


EOF = T(TokenType.EOF)
FN = T(TokenType.FN)
RETURN = T(TokenType.RETURN)
LPAREN = T(TokenType.LPAREN)
RPAREN = T(TokenType.RPAREN)
LBRACE = T(TokenType.LBRACE)
RBRACE = T(TokenType.RBRACE)
COLON = T(TokenType.COLON)
COMMA = T(TokenType.COMMA)
PLUS = T(TokenType.PLUS)
MINUS = T(TokenType.MINUS)
TRUE = T(TokenType.TRUE)
FALSE = T(TokenType.FALSE)


def INT(n: int) -> Token:
    return T(TokenType.INT, n)


def STRING(s: str) -> Token:
    return T(TokenType.STRING, s)


def IDENT(name: str) -> Token:
    return T(TokenType.IDENT, name)


# =============================================================================
# Literals & Atoms
# =============================================================================


class TestLiterals:
    def test_parse_integer_literal(self):
        tokens = [INT(5), EOF]
        expr = Parser(tokens).parse_expression()
        assert expr == IntLiteral(5)

    def test_parse_true_literal(self):
        tokens = [TRUE, EOF]
        expr = Parser(tokens).parse_expression()
        assert expr == BoolLiteral(True)

    def test_parse_false_literal(self):
        tokens = [FALSE, EOF]
        expr = Parser(tokens).parse_expression()
        assert expr == BoolLiteral(False)

    def test_parse_string_literal(self):
        tokens = [STRING("hello"), EOF]
        expr = Parser(tokens).parse_expression()
        assert expr == StringLiteral("hello")

    def test_parse_identifier(self):
        tokens = [IDENT("foo"), EOF]
        expr = Parser(tokens).parse_expression()
        assert expr == Identifier("foo")


# =============================================================================
# Expressions - Simple
# =============================================================================


class TestBinaryExpressions:
    def test_parse_binary_addition(self):
        # 5 + 3
        tokens = [INT(5), PLUS, INT(3), EOF]
        expr = Parser(tokens).parse_expression()
        assert expr == BinaryExpr("+", IntLiteral(5), IntLiteral(3))

    def test_parse_binary_subtraction(self):
        # 5 - 3
        tokens = [INT(5), MINUS, INT(3), EOF]
        expr = Parser(tokens).parse_expression()
        assert expr == BinaryExpr("-", IntLiteral(5), IntLiteral(3))

    def test_parse_chained_addition_is_left_associative(self):
        # 1 + 2 + 3 should parse as ((1 + 2) + 3)
        tokens = [INT(1), PLUS, INT(2), PLUS, INT(3), EOF]
        expr = Parser(tokens).parse_expression()
        expected = BinaryExpr(
            "+",
            BinaryExpr("+", IntLiteral(1), IntLiteral(2)),
            IntLiteral(3),
        )
        assert expr == expected

    def test_parse_parenthesized_expression(self):
        # (5)
        tokens = [LPAREN, INT(5), RPAREN, EOF]
        expr = Parser(tokens).parse_expression()
        assert expr == IntLiteral(5)

    def test_parse_grouped_precedence(self):
        # (1 + 2) + 3
        tokens = [LPAREN, INT(1), PLUS, INT(2), RPAREN, PLUS, INT(3), EOF]
        expr = Parser(tokens).parse_expression()
        expected = BinaryExpr(
            "+",
            BinaryExpr("+", IntLiteral(1), IntLiteral(2)),
            IntLiteral(3),
        )
        assert expr == expected


# =============================================================================
# Expressions - Function Calls
# =============================================================================


class TestFunctionCalls:
    def test_parse_call_no_args(self):
        # foo()
        tokens = [IDENT("foo"), LPAREN, RPAREN, EOF]
        expr = Parser(tokens).parse_expression()
        assert expr == Call("foo", [])

    def test_parse_call_one_arg(self):
        # foo(5)
        tokens = [IDENT("foo"), LPAREN, INT(5), RPAREN, EOF]
        expr = Parser(tokens).parse_expression()
        assert expr == Call("foo", [IntLiteral(5)])

    def test_parse_call_multiple_args(self):
        # foo(1, 2, 3)
        tokens = [IDENT("foo"), LPAREN, INT(1), COMMA, INT(2), COMMA, INT(3), RPAREN, EOF]
        expr = Parser(tokens).parse_expression()
        assert expr == Call("foo", [IntLiteral(1), IntLiteral(2), IntLiteral(3)])

    def test_parse_nested_calls(self):
        # foo(bar(5))
        tokens = [IDENT("foo"), LPAREN, IDENT("bar"), LPAREN, INT(5), RPAREN, RPAREN, EOF]
        expr = Parser(tokens).parse_expression()
        expected = Call("foo", [Call("bar", [IntLiteral(5)])])
        assert expr == expected

    def test_parse_call_with_expression_arg(self):
        # foo(1 + 2)
        tokens = [IDENT("foo"), LPAREN, INT(1), PLUS, INT(2), RPAREN, EOF]
        expr = Parser(tokens).parse_expression()
        expected = Call("foo", [BinaryExpr("+", IntLiteral(1), IntLiteral(2))])
        assert expr == expected


# =============================================================================
# Statements
# =============================================================================


class TestStatements:
    def test_parse_return_with_literal(self):
        # return 5
        tokens = [RETURN, INT(5), EOF]
        stmt = Parser(tokens).parse_statement()
        assert stmt == ReturnStmt(IntLiteral(5))

    def test_parse_return_with_expression(self):
        # return a + b
        tokens = [RETURN, IDENT("a"), PLUS, IDENT("b"), EOF]
        stmt = Parser(tokens).parse_statement()
        expected = ReturnStmt(BinaryExpr("+", Identifier("a"), Identifier("b")))
        assert stmt == expected

    def test_parse_expression_statement(self):
        # print(5)
        tokens = [IDENT("print"), LPAREN, INT(5), RPAREN, EOF]
        stmt = Parser(tokens).parse_statement()
        assert stmt == ExprStmt(Call("print", [IntLiteral(5)]))


# =============================================================================
# Function Parameters
# =============================================================================


class TestParameters:
    def test_parse_single_param(self):
        # a: int
        tokens = [IDENT("a"), COLON, IDENT("int"), EOF]
        params = Parser(tokens).parse_params()
        assert params == [Param("a", "int")]

    def test_parse_multiple_params(self):
        # a: int, b: int
        tokens = [IDENT("a"), COLON, IDENT("int"), COMMA, IDENT("b"), COLON, IDENT("int"), EOF]
        params = Parser(tokens).parse_params()
        assert params == [Param("a", "int"), Param("b", "int")]

    def test_parse_no_params(self):
        # (empty)
        tokens = [EOF]
        params = Parser(tokens).parse_params()
        assert params == []


# =============================================================================
# Function Declarations
# =============================================================================


class TestFunctionDeclarations:
    def test_parse_fn_no_params_no_return_type(self):
        # fn main() { }
        tokens = [FN, IDENT("main"), LPAREN, RPAREN, LBRACE, RBRACE, EOF]
        fn = Parser(tokens).parse_function()
        assert fn == Function("main", [], None, [])

    def test_parse_fn_with_params_no_return_type(self):
        # fn foo(x: int) { }
        tokens = [FN, IDENT("foo"), LPAREN, IDENT("x"), COLON, IDENT("int"), RPAREN, LBRACE, RBRACE, EOF]
        fn = Parser(tokens).parse_function()
        assert fn == Function("foo", [Param("x", "int")], None, [])

    def test_parse_fn_with_return_type(self):
        # fn add(): int { }
        tokens = [FN, IDENT("add"), LPAREN, RPAREN, COLON, IDENT("int"), LBRACE, RBRACE, EOF]
        fn = Parser(tokens).parse_function()
        assert fn == Function("add", [], "int", [])

    def test_parse_fn_with_params_and_return_type(self):
        # fn add(a: int, b: int): int { }
        tokens = [
            FN, IDENT("add"), LPAREN,
            IDENT("a"), COLON, IDENT("int"), COMMA,
            IDENT("b"), COLON, IDENT("int"),
            RPAREN, COLON, IDENT("int"), LBRACE, RBRACE, EOF,
        ]
        fn = Parser(tokens).parse_function()
        expected = Function(
            "add",
            [Param("a", "int"), Param("b", "int")],
            "int",
            [],
        )
        assert fn == expected

    def test_parse_fn_with_single_statement_body(self):
        # fn foo() { return 5 }
        tokens = [FN, IDENT("foo"), LPAREN, RPAREN, LBRACE, RETURN, INT(5), RBRACE, EOF]
        fn = Parser(tokens).parse_function()
        assert fn == Function("foo", [], None, [ReturnStmt(IntLiteral(5))])

    def test_parse_fn_with_multi_statement_body(self):
        # fn foo() { print(1) return 2 }
        tokens = [
            FN, IDENT("foo"), LPAREN, RPAREN, LBRACE,
            IDENT("print"), LPAREN, INT(1), RPAREN,
            RETURN, INT(2),
            RBRACE, EOF,
        ]
        fn = Parser(tokens).parse_function()
        expected = Function(
            "foo",
            [],
            None,
            [
                ExprStmt(Call("print", [IntLiteral(1)])),
                ReturnStmt(IntLiteral(2)),
            ],
        )
        assert fn == expected


# =============================================================================
# Program
# =============================================================================


class TestProgram:
    def test_parse_empty_program(self):
        tokens = [EOF]
        program = parse(tokens)
        assert program == Program([])

    def test_parse_single_function_program(self):
        # fn main() { }
        tokens = [FN, IDENT("main"), LPAREN, RPAREN, LBRACE, RBRACE, EOF]
        program = parse(tokens)
        assert program == Program([Function("main", [], None, [])])

    def test_parse_multi_function_program(self):
        # fn add(a: int, b: int): int { return a + b }
        # fn main() { print(add(5, 3)) }
        tokens = [
            # fn add(a: int, b: int): int {
            FN, IDENT("add"), LPAREN,
            IDENT("a"), COLON, IDENT("int"), COMMA,
            IDENT("b"), COLON, IDENT("int"),
            RPAREN, COLON, IDENT("int"), LBRACE,
            # return a + b
            RETURN, IDENT("a"), PLUS, IDENT("b"),
            # }
            RBRACE,
            # fn main() {
            FN, IDENT("main"), LPAREN, RPAREN, LBRACE,
            # print(add(5, 3))
            IDENT("print"), LPAREN,
            IDENT("add"), LPAREN, INT(5), COMMA, INT(3), RPAREN,
            RPAREN,
            # }
            RBRACE,
            EOF,
        ]
        program = parse(tokens)
        expected = Program([
            Function(
                "add",
                [Param("a", "int"), Param("b", "int")],
                "int",
                [ReturnStmt(BinaryExpr("+", Identifier("a"), Identifier("b")))],
            ),
            Function(
                "main",
                [],
                None,
                [ExprStmt(Call("print", [Call("add", [IntLiteral(5), IntLiteral(3)])]))],
            ),
        ])
        assert program == expected


# =============================================================================
# Error Cases
# =============================================================================


class TestParseErrors:
    def test_missing_closing_paren_in_call(self):
        # foo(5 <missing )>
        tokens = [IDENT("foo"), LPAREN, INT(5), EOF]
        with pytest.raises(SyntaxError, match=r"[Ee]xpected.*\)"):
            Parser(tokens).parse_expression()

    def test_missing_closing_brace_in_function(self):
        # fn foo() { <missing }>
        tokens = [FN, IDENT("foo"), LPAREN, RPAREN, LBRACE, EOF]
        with pytest.raises(SyntaxError, match=r"[Ee]xpected.*\}"):
            Parser(tokens).parse_function()

    def test_missing_colon_in_param(self):
        # fn foo(a int) { }
        tokens = [FN, IDENT("foo"), LPAREN, IDENT("a"), IDENT("int"), RPAREN, LBRACE, RBRACE, EOF]
        with pytest.raises(SyntaxError, match=r"[Ee]xpected.*:"):
            Parser(tokens).parse_function()

    def test_unexpected_token(self):
        # fn () - missing function name
        tokens = [FN, LPAREN, RPAREN, LBRACE, RBRACE, EOF]
        with pytest.raises(SyntaxError):
            Parser(tokens).parse_function()
