import pytest
from zero.lexer import Token, TokenType, tokenize


# =============================================================================
# Empty & Whitespace
# =============================================================================


class TestEmptyAndWhitespace:
    def test_empty_string(self):
        assert tokenize("") == [Token(TokenType.EOF)]

    def test_whitespace_only(self):
        assert tokenize("   \n\t") == [Token(TokenType.EOF)]


# =============================================================================
# Literals
# =============================================================================


class TestLiterals:
    def test_single_digit(self):
        assert tokenize("5") == [Token(TokenType.INT, 5), Token(TokenType.EOF)]

    def test_multi_digit(self):
        assert tokenize("123") == [Token(TokenType.INT, 123), Token(TokenType.EOF)]

    def test_zero(self):
        assert tokenize("0") == [Token(TokenType.INT, 0), Token(TokenType.EOF)]

    def test_string_literal(self):
        assert tokenize('"hello"') == [Token(TokenType.STRING, "hello"), Token(TokenType.EOF)]

    def test_string_with_spaces(self):
        assert tokenize('"hello world"') == [Token(TokenType.STRING, "hello world"), Token(TokenType.EOF)]

    def test_empty_string(self):
        assert tokenize('""') == [Token(TokenType.STRING, ""), Token(TokenType.EOF)]


# =============================================================================
# Identifiers
# =============================================================================


class TestIdentifiers:
    def test_simple_ident(self):
        assert tokenize("foo") == [Token(TokenType.IDENT, "foo"), Token(TokenType.EOF)]

    def test_single_char_ident(self):
        assert tokenize("a") == [Token(TokenType.IDENT, "a"), Token(TokenType.EOF)]

    def test_ident_with_underscore(self):
        assert tokenize("foo_bar") == [Token(TokenType.IDENT, "foo_bar"), Token(TokenType.EOF)]

    def test_ident_starting_underscore(self):
        assert tokenize("_foo") == [Token(TokenType.IDENT, "_foo"), Token(TokenType.EOF)]

    def test_ident_with_digits(self):
        assert tokenize("x1") == [Token(TokenType.IDENT, "x1"), Token(TokenType.EOF)]


# =============================================================================
# Keywords
# =============================================================================


class TestKeywords:
    def test_keyword_fn(self):
        assert tokenize("fn") == [Token(TokenType.FN), Token(TokenType.EOF)]

    def test_keyword_return(self):
        assert tokenize("return") == [Token(TokenType.RETURN), Token(TokenType.EOF)]

    def test_keyword_true(self):
        assert tokenize("true") == [Token(TokenType.TRUE), Token(TokenType.EOF)]

    def test_keyword_false(self):
        assert tokenize("false") == [Token(TokenType.FALSE), Token(TokenType.EOF)]


# =============================================================================
# Symbols
# =============================================================================


class TestSymbols:
    def test_lparen(self):
        assert tokenize("(") == [Token(TokenType.LPAREN), Token(TokenType.EOF)]

    def test_rparen(self):
        assert tokenize(")") == [Token(TokenType.RPAREN), Token(TokenType.EOF)]

    def test_lbrace(self):
        assert tokenize("{") == [Token(TokenType.LBRACE), Token(TokenType.EOF)]

    def test_rbrace(self):
        assert tokenize("}") == [Token(TokenType.RBRACE), Token(TokenType.EOF)]

    def test_colon(self):
        assert tokenize(":") == [Token(TokenType.COLON), Token(TokenType.EOF)]

    def test_comma(self):
        assert tokenize(",") == [Token(TokenType.COMMA), Token(TokenType.EOF)]

    def test_plus(self):
        assert tokenize("+") == [Token(TokenType.PLUS), Token(TokenType.EOF)]

    def test_minus(self):
        assert tokenize("-") == [Token(TokenType.MINUS), Token(TokenType.EOF)]


# =============================================================================
# Comments
# =============================================================================


class TestComments:
    def test_comment_only(self):
        assert tokenize("# hello") == [Token(TokenType.EOF)]

    def test_comment_after_token(self):
        assert tokenize("fn # comment") == [Token(TokenType.FN), Token(TokenType.EOF)]

    def test_code_after_comment(self):
        assert tokenize("fn # x\nadd") == [Token(TokenType.FN), Token(TokenType.IDENT, "add"), Token(TokenType.EOF)]


# =============================================================================
# Keyword vs Identifier Edge Cases
# =============================================================================


class TestKeywordEdgeCases:
    def test_keyword_prefix(self):
        assert tokenize("fnord") == [Token(TokenType.IDENT, "fnord"), Token(TokenType.EOF)]

    def test_keyword_suffix(self):
        assert tokenize("myfn") == [Token(TokenType.IDENT, "myfn"), Token(TokenType.EOF)]

    def test_keyword_with_digit(self):
        assert tokenize("fn1") == [Token(TokenType.IDENT, "fn1"), Token(TokenType.EOF)]


# =============================================================================
# Whitespace Handling
# =============================================================================


class TestWhitespaceHandling:
    def test_spaces_between_tokens(self):
        assert tokenize("fn   add") == [Token(TokenType.FN), Token(TokenType.IDENT, "add"), Token(TokenType.EOF)]

    def test_newline_between_tokens(self):
        assert tokenize("fn\nadd") == [Token(TokenType.FN), Token(TokenType.IDENT, "add"), Token(TokenType.EOF)]

    def test_no_space_needed(self):
        assert tokenize("fn(") == [Token(TokenType.FN), Token(TokenType.LPAREN), Token(TokenType.EOF)]


# =============================================================================
# Combinations
# =============================================================================


class TestCombinations:
    def test_function_signature(self):
        assert tokenize("fn add(a: int)") == [
            Token(TokenType.FN),
            Token(TokenType.IDENT, "add"),
            Token(TokenType.LPAREN),
            Token(TokenType.IDENT, "a"),
            Token(TokenType.COLON),
            Token(TokenType.IDENT, "int"),
            Token(TokenType.RPAREN),
            Token(TokenType.EOF),
        ]

    def test_expression(self):
        assert tokenize("a + 1") == [
            Token(TokenType.IDENT, "a"),
            Token(TokenType.PLUS),
            Token(TokenType.INT, 1),
            Token(TokenType.EOF),
        ]

    def test_function_call(self):
        assert tokenize("add(5, 3)") == [
            Token(TokenType.IDENT, "add"),
            Token(TokenType.LPAREN),
            Token(TokenType.INT, 5),
            Token(TokenType.COMMA),
            Token(TokenType.INT, 3),
            Token(TokenType.RPAREN),
            Token(TokenType.EOF),
        ]


# =============================================================================
# Full Program (Integration)
# =============================================================================


class TestIntegration:
    def test_full_function(self):
        source = "fn add(a: int): int { return a + 1 }"
        assert tokenize(source) == [
            Token(TokenType.FN),
            Token(TokenType.IDENT, "add"),
            Token(TokenType.LPAREN),
            Token(TokenType.IDENT, "a"),
            Token(TokenType.COLON),
            Token(TokenType.IDENT, "int"),
            Token(TokenType.RPAREN),
            Token(TokenType.COLON),
            Token(TokenType.IDENT, "int"),
            Token(TokenType.LBRACE),
            Token(TokenType.RETURN),
            Token(TokenType.IDENT, "a"),
            Token(TokenType.PLUS),
            Token(TokenType.INT, 1),
            Token(TokenType.RBRACE),
            Token(TokenType.EOF),
        ]

    def test_example_file(self):
        source = """\
fn add(a: int, b: int): int {
    return a + b
}

fn main() {
    print(add(5, 3))
}
"""
        assert tokenize(source) == [
            # fn add(a: int, b: int): int {
            Token(TokenType.FN),
            Token(TokenType.IDENT, "add"),
            Token(TokenType.LPAREN),
            Token(TokenType.IDENT, "a"),
            Token(TokenType.COLON),
            Token(TokenType.IDENT, "int"),
            Token(TokenType.COMMA),
            Token(TokenType.IDENT, "b"),
            Token(TokenType.COLON),
            Token(TokenType.IDENT, "int"),
            Token(TokenType.RPAREN),
            Token(TokenType.COLON),
            Token(TokenType.IDENT, "int"),
            Token(TokenType.LBRACE),
            # return a + b
            Token(TokenType.RETURN),
            Token(TokenType.IDENT, "a"),
            Token(TokenType.PLUS),
            Token(TokenType.IDENT, "b"),
            # }
            Token(TokenType.RBRACE),
            # fn main() {
            Token(TokenType.FN),
            Token(TokenType.IDENT, "main"),
            Token(TokenType.LPAREN),
            Token(TokenType.RPAREN),
            Token(TokenType.LBRACE),
            # print(add(5, 3))
            Token(TokenType.IDENT, "print"),
            Token(TokenType.LPAREN),
            Token(TokenType.IDENT, "add"),
            Token(TokenType.LPAREN),
            Token(TokenType.INT, 5),
            Token(TokenType.COMMA),
            Token(TokenType.INT, 3),
            Token(TokenType.RPAREN),
            Token(TokenType.RPAREN),
            # }
            Token(TokenType.RBRACE),
            Token(TokenType.EOF),
        ]


# =============================================================================
# Errors
# =============================================================================


class TestErrors:
    def test_invalid_character(self):
        with pytest.raises(SyntaxError):
            tokenize("@")
