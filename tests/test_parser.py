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
from zero.lexer import tokenize as lex_tokenize


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
STAR = T(TokenType.STAR)
PERCENT = T(TokenType.PERCENT)
TRUE = T(TokenType.TRUE)
FALSE = T(TokenType.FALSE)
ASSIGN = T(TokenType.ASSIGN)
PLUS_EQUAL = T(TokenType.PLUS_EQUAL)
MINUS_EQUAL = T(TokenType.MINUS_EQUAL)
EQ = T(TokenType.EQ)
NE = T(TokenType.NE)
LT = T(TokenType.LT)
GT = T(TokenType.GT)
LE = T(TokenType.LE)
GE = T(TokenType.GE)
IF = T(TokenType.IF)
ELSE = T(TokenType.ELSE)
FOR = T(TokenType.FOR)
BREAK = T(TokenType.BREAK)
CONTINUE = T(TokenType.CONTINUE)


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

    def test_parse_string_with_expression_content(self):
        """String containing expression-like content should parse as literal"""
        tokens = [STRING("5 + 5"), EOF]
        expr = Parser(tokens).parse_expression()
        assert expr == StringLiteral("5 + 5")

    def test_parse_string_with_keywords(self):
        """String containing keywords should parse as literal"""
        tokens = [STRING("fn return if"), EOF]
        expr = Parser(tokens).parse_expression()
        assert expr == StringLiteral("fn return if")

    def test_parse_string_with_number(self):
        """String containing a number should parse as literal, not IntLiteral"""
        tokens = [STRING("123"), EOF]
        expr = Parser(tokens).parse_expression()
        assert expr == StringLiteral("123")

    def test_parse_string_with_boolean(self):
        """String containing 'true' should parse as literal, not BoolLiteral"""
        tokens = [STRING("true"), EOF]
        expr = Parser(tokens).parse_expression()
        assert expr == StringLiteral("true")

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
# Expressions - Multiplicative
# =============================================================================


# =============================================================================
# Expressions - Unary
# =============================================================================


class TestUnaryExpressions:
    def test_parse_unary_minus_literal(self):
        # -5
        tokens = [MINUS, INT(5), EOF]
        expr = Parser(tokens).parse_expression()
        assert expr == UnaryExpr("-", IntLiteral(5))

    def test_parse_unary_minus_identifier(self):
        # -x
        tokens = [MINUS, IDENT("x"), EOF]
        expr = Parser(tokens).parse_expression()
        assert expr == UnaryExpr("-", Identifier("x"))

    def test_parse_double_negation(self):
        # --5
        tokens = [MINUS, MINUS, INT(5), EOF]
        expr = Parser(tokens).parse_expression()
        assert expr == UnaryExpr("-", UnaryExpr("-", IntLiteral(5)))

    def test_parse_unary_in_binary(self):
        # 5 + -3
        tokens = [INT(5), PLUS, MINUS, INT(3), EOF]
        expr = Parser(tokens).parse_expression()
        assert expr == BinaryExpr("+", IntLiteral(5), UnaryExpr("-", IntLiteral(3)))

    def test_parse_unary_mul_precedence(self):
        # -5 * 3 should be (-5) * 3, not -(5 * 3)
        tokens = [MINUS, INT(5), STAR, INT(3), EOF]
        expr = Parser(tokens).parse_expression()
        assert expr == BinaryExpr("*", UnaryExpr("-", IntLiteral(5)), IntLiteral(3))

    def test_parse_unary_paren(self):
        # -(1 + 2)
        tokens = [MINUS, LPAREN, INT(1), PLUS, INT(2), RPAREN, EOF]
        expr = Parser(tokens).parse_expression()
        assert expr == UnaryExpr("-", BinaryExpr("+", IntLiteral(1), IntLiteral(2)))


# =============================================================================
# Expressions - Multiplicative
# =============================================================================


class TestMultiplicativeExpressions:
    def test_parse_multiplication(self):
        # 3 * 4
        tokens = [INT(3), STAR, INT(4), EOF]
        expr = Parser(tokens).parse_expression()
        assert expr == BinaryExpr("*", IntLiteral(3), IntLiteral(4))

    def test_parse_modulo(self):
        # 10 % 3
        tokens = [INT(10), PERCENT, INT(3), EOF]
        expr = Parser(tokens).parse_expression()
        assert expr == BinaryExpr("%", IntLiteral(10), IntLiteral(3))

    def test_multiplication_higher_precedence_than_addition(self):
        # 5 + 3 * 2 should parse as 5 + (3 * 2)
        tokens = [INT(5), PLUS, INT(3), STAR, INT(2), EOF]
        expr = Parser(tokens).parse_expression()
        expected = BinaryExpr(
            "+",
            IntLiteral(5),
            BinaryExpr("*", IntLiteral(3), IntLiteral(2)),
        )
        assert expr == expected

    def test_multiplication_before_addition_left(self):
        # 3 * 2 + 5 should parse as (3 * 2) + 5
        tokens = [INT(3), STAR, INT(2), PLUS, INT(5), EOF]
        expr = Parser(tokens).parse_expression()
        expected = BinaryExpr(
            "+",
            BinaryExpr("*", IntLiteral(3), IntLiteral(2)),
            IntLiteral(5),
        )
        assert expr == expected

    def test_chained_multiplication_left_associative(self):
        # 2 * 3 * 4 should parse as ((2 * 3) * 4)
        tokens = [INT(2), STAR, INT(3), STAR, INT(4), EOF]
        expr = Parser(tokens).parse_expression()
        expected = BinaryExpr(
            "*",
            BinaryExpr("*", IntLiteral(2), IntLiteral(3)),
            IntLiteral(4),
        )
        assert expr == expected

    def test_parentheses_override_precedence(self):
        # (5 + 3) * 2 should parse as (5 + 3) * 2
        tokens = [LPAREN, INT(5), PLUS, INT(3), RPAREN, STAR, INT(2), EOF]
        expr = Parser(tokens).parse_expression()
        expected = BinaryExpr(
            "*",
            BinaryExpr("+", IntLiteral(5), IntLiteral(3)),
            IntLiteral(2),
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


# =============================================================================
# Variable Declarations and Assignments
# =============================================================================


class TestVariables:
    def test_parse_var_decl(self):
        # x: int = 5
        tokens = [IDENT("x"), COLON, IDENT("int"), ASSIGN, INT(5), EOF]
        stmt = Parser(tokens).parse_statement()
        assert stmt == VarDecl("x", "int", IntLiteral(5))

    def test_parse_var_decl_with_expr(self):
        # y: int = 1 + 2
        tokens = [IDENT("y"), COLON, IDENT("int"), ASSIGN, INT(1), PLUS, INT(2), EOF]
        stmt = Parser(tokens).parse_statement()
        assert stmt == VarDecl("y", "int", BinaryExpr("+", IntLiteral(1), IntLiteral(2)))

    def test_parse_assignment(self):
        # x = 10
        tokens = [IDENT("x"), ASSIGN, INT(10), EOF]
        stmt = Parser(tokens).parse_statement()
        assert stmt == Assignment("x", IntLiteral(10))

    def test_parse_assignment_with_expr(self):
        # x = x + 1
        tokens = [IDENT("x"), ASSIGN, IDENT("x"), PLUS, INT(1), EOF]
        stmt = Parser(tokens).parse_statement()
        assert stmt == Assignment("x", BinaryExpr("+", Identifier("x"), IntLiteral(1)))


# =============================================================================
# Comparison Expressions
# =============================================================================


class TestComparisons:
    def test_parse_comparison_eq(self):
        # a == b
        tokens = [IDENT("a"), EQ, IDENT("b"), EOF]
        expr = Parser(tokens).parse_expression()
        assert expr == BinaryExpr("==", Identifier("a"), Identifier("b"))

    def test_parse_comparison_ne(self):
        # a != b
        tokens = [IDENT("a"), NE, IDENT("b"), EOF]
        expr = Parser(tokens).parse_expression()
        assert expr == BinaryExpr("!=", Identifier("a"), Identifier("b"))

    def test_parse_comparison_lt(self):
        # a < b
        tokens = [IDENT("a"), LT, IDENT("b"), EOF]
        expr = Parser(tokens).parse_expression()
        assert expr == BinaryExpr("<", Identifier("a"), Identifier("b"))

    def test_parse_comparison_gt(self):
        # a > b
        tokens = [IDENT("a"), GT, IDENT("b"), EOF]
        expr = Parser(tokens).parse_expression()
        assert expr == BinaryExpr(">", Identifier("a"), Identifier("b"))

    def test_parse_comparison_le(self):
        # a <= b
        tokens = [IDENT("a"), LE, IDENT("b"), EOF]
        expr = Parser(tokens).parse_expression()
        assert expr == BinaryExpr("<=", Identifier("a"), Identifier("b"))

    def test_parse_comparison_ge(self):
        # a >= b
        tokens = [IDENT("a"), GE, IDENT("b"), EOF]
        expr = Parser(tokens).parse_expression()
        assert expr == BinaryExpr(">=", Identifier("a"), Identifier("b"))

    def test_parse_comparison_precedence(self):
        # 1 + 2 < 3 + 4 should parse as (1 + 2) < (3 + 4)
        tokens = [INT(1), PLUS, INT(2), LT, INT(3), PLUS, INT(4), EOF]
        expr = Parser(tokens).parse_expression()
        expected = BinaryExpr(
            "<",
            BinaryExpr("+", IntLiteral(1), IntLiteral(2)),
            BinaryExpr("+", IntLiteral(3), IntLiteral(4)),
        )
        assert expr == expected

    def test_parse_comparison_with_literals(self):
        # 5 > 3
        tokens = [INT(5), GT, INT(3), EOF]
        expr = Parser(tokens).parse_expression()
        assert expr == BinaryExpr(">", IntLiteral(5), IntLiteral(3))


# =============================================================================
# If/Else Statements
# =============================================================================


class TestIfStatements:
    def test_parse_if_no_else(self):
        # if (x > 0) { return 1 }
        tokens = [
            IF, LPAREN, IDENT("x"), GT, INT(0), RPAREN,
            LBRACE, RETURN, INT(1), RBRACE,
            EOF,
        ]
        stmt = Parser(tokens).parse_statement()
        expected = IfStmt(
            condition=BinaryExpr(">", Identifier("x"), IntLiteral(0)),
            then_body=[ReturnStmt(IntLiteral(1))],
            else_body=None,
        )
        assert stmt == expected

    def test_parse_if_else(self):
        # if (x > 0) { return 1 } else { return 0 }
        tokens = [
            IF, LPAREN, IDENT("x"), GT, INT(0), RPAREN,
            LBRACE, RETURN, INT(1), RBRACE,
            ELSE,
            LBRACE, RETURN, INT(0), RBRACE,
            EOF,
        ]
        stmt = Parser(tokens).parse_statement()
        expected = IfStmt(
            condition=BinaryExpr(">", Identifier("x"), IntLiteral(0)),
            then_body=[ReturnStmt(IntLiteral(1))],
            else_body=[ReturnStmt(IntLiteral(0))],
        )
        assert stmt == expected

    def test_parse_if_with_multiple_statements(self):
        # if (true) { print(1) return 2 }
        tokens = [
            IF, LPAREN, TRUE, RPAREN,
            LBRACE,
            IDENT("print"), LPAREN, INT(1), RPAREN,
            RETURN, INT(2),
            RBRACE,
            EOF,
        ]
        stmt = Parser(tokens).parse_statement()
        expected = IfStmt(
            condition=BoolLiteral(True),
            then_body=[
                ExprStmt(Call("print", [IntLiteral(1)])),
                ReturnStmt(IntLiteral(2)),
            ],
            else_body=None,
        )
        assert stmt == expected

    def test_parse_if_with_comparison_condition(self):
        # if (a == b) { return 1 }
        tokens = [
            IF, LPAREN, IDENT("a"), EQ, IDENT("b"), RPAREN,
            LBRACE, RETURN, INT(1), RBRACE,
            EOF,
        ]
        stmt = Parser(tokens).parse_statement()
        expected = IfStmt(
            condition=BinaryExpr("==", Identifier("a"), Identifier("b")),
            then_body=[ReturnStmt(IntLiteral(1))],
            else_body=None,
        )
        assert stmt == expected


# =============================================================================
# Compound Assignment (Desugaring)
# =============================================================================


class TestCompoundAssignment:
    def test_parse_plus_equal(self):
        # x += 5 desugars to x = x + 5
        tokens = [IDENT("x"), PLUS_EQUAL, INT(5), EOF]
        stmt = Parser(tokens).parse_statement()
        expected = Assignment("x", BinaryExpr("+", Identifier("x"), IntLiteral(5)))
        assert stmt == expected

    def test_parse_minus_equal(self):
        # x -= 3 desugars to x = x - 3
        tokens = [IDENT("x"), MINUS_EQUAL, INT(3), EOF]
        stmt = Parser(tokens).parse_statement()
        expected = Assignment("x", BinaryExpr("-", Identifier("x"), IntLiteral(3)))
        assert stmt == expected

    def test_parse_plus_equal_with_expression(self):
        # x += 1 + 2 desugars to x = x + (1 + 2)
        tokens = [IDENT("x"), PLUS_EQUAL, INT(1), PLUS, INT(2), EOF]
        stmt = Parser(tokens).parse_statement()
        expected = Assignment(
            "x",
            BinaryExpr("+", Identifier("x"), BinaryExpr("+", IntLiteral(1), IntLiteral(2)))
        )
        assert stmt == expected

    def test_parse_minus_equal_with_identifier(self):
        # x -= y desugars to x = x - y
        tokens = [IDENT("x"), MINUS_EQUAL, IDENT("y"), EOF]
        stmt = Parser(tokens).parse_statement()
        expected = Assignment("x", BinaryExpr("-", Identifier("x"), Identifier("y")))
        assert stmt == expected

    def test_parse_compound_assignment_in_function(self):
        # fn main() { x: int = 5  x += 1 }
        tokens = [
            FN, IDENT("main"), LPAREN, RPAREN, LBRACE,
            IDENT("x"), COLON, IDENT("int"), ASSIGN, INT(5),
            IDENT("x"), PLUS_EQUAL, INT(1),
            RBRACE, EOF,
        ]
        fn = Parser(tokens).parse_function()
        expected = Function(
            "main",
            [],
            None,
            [
                VarDecl("x", "int", IntLiteral(5)),
                Assignment("x", BinaryExpr("+", Identifier("x"), IntLiteral(1))),
            ],
        )
        assert fn == expected


# =============================================================================
# For Loop Statements
# =============================================================================


class TestForLoops:
    def test_parse_for_loop(self):
        # for (i < 10) { print(i) }
        tokens = [
            FOR, LPAREN, IDENT("i"), LT, INT(10), RPAREN,
            LBRACE,
            IDENT("print"), LPAREN, IDENT("i"), RPAREN,
            RBRACE,
            EOF,
        ]
        stmt = Parser(tokens).parse_statement()
        expected = ForStmt(
            condition=BinaryExpr("<", Identifier("i"), IntLiteral(10)),
            body=[ExprStmt(Call("print", [Identifier("i")]))],
        )
        assert stmt == expected

    def test_parse_for_with_break(self):
        # for (true) { break }
        tokens = [
            FOR, LPAREN, TRUE, RPAREN,
            LBRACE, BREAK, RBRACE,
            EOF,
        ]
        stmt = Parser(tokens).parse_statement()
        expected = ForStmt(
            condition=BoolLiteral(True),
            body=[BreakStmt()],
        )
        assert stmt == expected

    def test_parse_for_with_continue(self):
        # for (true) { continue }
        tokens = [
            FOR, LPAREN, TRUE, RPAREN,
            LBRACE, CONTINUE, RBRACE,
            EOF,
        ]
        stmt = Parser(tokens).parse_statement()
        expected = ForStmt(
            condition=BoolLiteral(True),
            body=[ContinueStmt()],
        )
        assert stmt == expected

    def test_parse_nested_for(self):
        # for (i < 3) { for (j < 3) { break } }
        tokens = [
            FOR, LPAREN, IDENT("i"), LT, INT(3), RPAREN,
            LBRACE,
            FOR, LPAREN, IDENT("j"), LT, INT(3), RPAREN,
            LBRACE, BREAK, RBRACE,
            RBRACE,
            EOF,
        ]
        stmt = Parser(tokens).parse_statement()
        expected = ForStmt(
            condition=BinaryExpr("<", Identifier("i"), IntLiteral(3)),
            body=[
                ForStmt(
                    condition=BinaryExpr("<", Identifier("j"), IntLiteral(3)),
                    body=[BreakStmt()],
                )
            ],
        )
        assert stmt == expected

    def test_parse_for_with_multiple_statements(self):
        # for (i < 10) { print(i) i += 1 }
        tokens = [
            FOR, LPAREN, IDENT("i"), LT, INT(10), RPAREN,
            LBRACE,
            IDENT("print"), LPAREN, IDENT("i"), RPAREN,
            IDENT("i"), PLUS_EQUAL, INT(1),
            RBRACE,
            EOF,
        ]
        stmt = Parser(tokens).parse_statement()
        expected = ForStmt(
            condition=BinaryExpr("<", Identifier("i"), IntLiteral(10)),
            body=[
                ExprStmt(Call("print", [Identifier("i")])),
                Assignment("i", BinaryExpr("+", Identifier("i"), IntLiteral(1))),
            ],
        )
        assert stmt == expected

    def test_parse_break_statement(self):
        # break
        tokens = [BREAK, EOF]
        stmt = Parser(tokens).parse_statement()
        assert stmt == BreakStmt()

    def test_parse_continue_statement(self):
        # continue
        tokens = [CONTINUE, EOF]
        stmt = Parser(tokens).parse_statement()
        assert stmt == ContinueStmt()


# =============================================================================
# AST Span Tracking
# =============================================================================


class TestSpans:
    def test_function_spans(self):
        ast = parse(lex_tokenize("fn main() {}"))
        func = ast.functions[0]
        assert func.name_span == Span(1, 4, 1, 7)  # "main" identifier only
        assert func.span == Span(1, 1, 1, 12)      # entire "fn main() {}"

    def test_call_span(self):
        ast = parse(lex_tokenize("fn main() { foo() }"))
        call = ast.functions[0].body[0].expr
        assert call.span == Span(1, 13, 1, 17)  # "foo()" - full call expression

    def test_parse_validates_spans(self):
        """Parsing through parse() guarantees all spans are set."""
        ast = parse(lex_tokenize("fn main() { return 1 + 2 }"))
        # Validation happens inside parse() - if we get here, all spans are set
        assert ast.span is not None
        assert ast.functions[0].span is not None
        assert ast.functions[0].body[0].span is not None  # ReturnStmt
        assert ast.functions[0].body[0].expr.span is not None  # BinaryExpr
