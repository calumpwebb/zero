from zero.lexer import Token, TokenType, tokenize


# =============================================================================
# 1. Empty/Whitespace
# =============================================================================


def test_empty_string():
    assert tokenize("") == []


def test_whitespace_only():
    assert tokenize("   \n\t") == []


# =============================================================================
# 2. Single Tokens - Literals
# =============================================================================


def test_single_digit():
    assert tokenize("5") == [Token(TokenType.INT, 5)]


def test_multi_digit():
    assert tokenize("123") == [Token(TokenType.INT, 123)]


def test_zero():
    assert tokenize("0") == [Token(TokenType.INT, 0)]


# =============================================================================
# 3. Single Tokens - Identifiers
# =============================================================================


def test_simple_ident():
    assert tokenize("foo") == [Token(TokenType.IDENT, "foo")]


def test_single_char_ident():
    assert tokenize("a") == [Token(TokenType.IDENT, "a")]


def test_ident_with_underscore():
    assert tokenize("foo_bar") == [Token(TokenType.IDENT, "foo_bar")]


def test_ident_starting_underscore():
    assert tokenize("_foo") == [Token(TokenType.IDENT, "_foo")]


def test_ident_with_digits():
    assert tokenize("x1") == [Token(TokenType.IDENT, "x1")]


# =============================================================================
# 4. Single Tokens - Keywords
# =============================================================================


def test_keyword_fn():
    assert tokenize("fn") == [Token(TokenType.FN)]


def test_keyword_return():
    assert tokenize("return") == [Token(TokenType.RETURN)]


# =============================================================================
# 5. Single Tokens - Symbols
# =============================================================================


def test_lparen():
    assert tokenize("(") == [Token(TokenType.LPAREN)]


def test_rparen():
    assert tokenize(")") == [Token(TokenType.RPAREN)]


def test_lbrace():
    assert tokenize("{") == [Token(TokenType.LBRACE)]


def test_rbrace():
    assert tokenize("}") == [Token(TokenType.RBRACE)]


def test_colon():
    assert tokenize(":") == [Token(TokenType.COLON)]


def test_comma():
    assert tokenize(",") == [Token(TokenType.COMMA)]


def test_plus():
    assert tokenize("+") == [Token(TokenType.PLUS)]


# =============================================================================
# 6. Comments
# =============================================================================


def test_comment_only():
    assert tokenize("# hello") == []


def test_comment_after_token():
    assert tokenize("fn # comment") == [Token(TokenType.FN)]


def test_code_after_comment():
    assert tokenize("fn # x\nadd") == [Token(TokenType.FN), Token(TokenType.IDENT, "add")]


# =============================================================================
# 7. Keyword vs Identifier Edge Cases
# =============================================================================


def test_keyword_prefix():
    assert tokenize("fnord") == [Token(TokenType.IDENT, "fnord")]


def test_keyword_suffix():
    assert tokenize("myfn") == [Token(TokenType.IDENT, "myfn")]


def test_keyword_with_digit():
    assert tokenize("fn1") == [Token(TokenType.IDENT, "fn1")]


# =============================================================================
# 8. Whitespace Handling
# =============================================================================


def test_spaces_between_tokens():
    assert tokenize("fn   add") == [Token(TokenType.FN), Token(TokenType.IDENT, "add")]


def test_newline_between_tokens():
    assert tokenize("fn\nadd") == [Token(TokenType.FN), Token(TokenType.IDENT, "add")]


def test_no_space_needed():
    assert tokenize("fn(") == [Token(TokenType.FN), Token(TokenType.LPAREN)]


# =============================================================================
# 9. Combinations
# =============================================================================


def test_function_signature():
    assert tokenize("fn add(a: int)") == [
        Token(TokenType.FN),
        Token(TokenType.IDENT, "add"),
        Token(TokenType.LPAREN),
        Token(TokenType.IDENT, "a"),
        Token(TokenType.COLON),
        Token(TokenType.IDENT, "int"),
        Token(TokenType.RPAREN),
    ]


def test_expression():
    assert tokenize("a + 1") == [
        Token(TokenType.IDENT, "a"),
        Token(TokenType.PLUS),
        Token(TokenType.INT, 1),
    ]


def test_function_call():
    assert tokenize("add(5, 3)") == [
        Token(TokenType.IDENT, "add"),
        Token(TokenType.LPAREN),
        Token(TokenType.INT, 5),
        Token(TokenType.COMMA),
        Token(TokenType.INT, 3),
        Token(TokenType.RPAREN),
    ]


# =============================================================================
# 10. Full Program (Integration)
# =============================================================================


def test_full_function():
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
    ]


def test_example_file():
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
    ]


# =============================================================================
# 11. Errors
# =============================================================================


def test_invalid_character():
    import pytest

    with pytest.raises(SyntaxError):
        tokenize("@")
