from zero.lexer import tokenize


def test_empty_string():
    tokens = tokenize("")
    assert tokens == []
