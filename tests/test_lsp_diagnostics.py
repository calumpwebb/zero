from zero.lsp.features import get_diagnostics


def test_valid_code_no_diagnostics():
    assert get_diagnostics("fn main() {}") == []


def test_lexer_error():
    diags = get_diagnostics("fn main() { @ }")
    assert len(diags) == 1
    assert "Unexpected" in diags[0].message


def test_parser_error():
    diags = get_diagnostics("fn main( {}")  # missing )
    assert len(diags) == 1


def test_semantic_error_missing_main():
    diags = get_diagnostics("fn foo() {}")
    assert len(diags) == 1
    assert "main" in diags[0].message.lower()


def test_unexpected_error_doesnt_crash(monkeypatch):
    """Internal errors become diagnostics, not crashes."""
    def raise_error(source):
        raise RuntimeError("boom")
    monkeypatch.setattr("zero.lsp.features.tokenize", raise_error)
    diags = get_diagnostics("fn main() {}")
    assert len(diags) == 1
    assert "Internal error" in diags[0].message


def test_empty_source():
    diags = get_diagnostics("")
    assert len(diags) >= 1  # Should report error, not crash


def test_binary_garbage():
    diags = get_diagnostics("\x00\x01\x02")
    assert len(diags) >= 1  # Should report error, not crash
