from pygls.lsp.server import LanguageServer
from lsprotocol import types

from zero.lexer import tokenize
from zero.parser import parse
from zero.ast import Function
from zero.lsp.features import get_diagnostics, find_node_at_position, find_definition

server = LanguageServer("zero-lsp", "0.1.0")


def _publish_diagnostics(uri: str, source: str):
    """Compute and publish diagnostics for a document."""
    diagnostics = get_diagnostics(source)
    server.publish_diagnostics(uri, diagnostics)


@server.feature(types.TEXT_DOCUMENT_DID_OPEN)
def did_open(params: types.DidOpenTextDocumentParams):
    _publish_diagnostics(params.text_document.uri, params.text_document.text)


@server.feature(types.TEXT_DOCUMENT_DID_CHANGE)
def did_change(params: types.DidChangeTextDocumentParams):
    text = params.content_changes[0].text
    _publish_diagnostics(params.text_document.uri, text)


def _span_to_range(span) -> types.Range:
    """Convert a Span to LSP Range (0-indexed)."""
    return types.Range(
        start=types.Position(span.start_line - 1, span.start_column - 1),
        end=types.Position(span.end_line - 1, span.end_column - 1)
    )


@server.feature(types.TEXT_DOCUMENT_DEFINITION)
def goto_definition(params: types.TextDocumentPositionParams):
    doc = server.workspace.get_text_document(params.text_document.uri)
    try:
        ast = parse(tokenize(doc.source))
    except Exception:
        return None

    # LSP positions are 0-indexed, our spans are 1-indexed
    line = params.position.line + 1
    col = params.position.character + 1

    node = find_node_at_position(ast, line, col)
    if node is None:
        return None

    definition = find_definition(ast, node)
    if definition is None:
        return None

    # Use name_span for precise navigation if available
    target_span = getattr(definition, 'name_span', None) or definition.span
    return types.Location(uri=params.text_document.uri, range=_span_to_range(target_span))


@server.feature(types.TEXT_DOCUMENT_HOVER)
def hover(params: types.TextDocumentPositionParams):
    doc = server.workspace.get_text_document(params.text_document.uri)
    try:
        ast = parse(tokenize(doc.source))
    except Exception:
        return None

    line = params.position.line + 1
    col = params.position.character + 1

    node = find_node_at_position(ast, line, col)
    if node is None:
        return None

    definition = find_definition(ast, node)
    if definition is None:
        return None

    if isinstance(definition, Function):
        sig = _format_signature(definition)
        return types.Hover(contents=types.MarkupContent(
            kind=types.MarkupKind.PlainText,
            value=sig
        ))

    return None


def _format_signature(func: Function) -> str:
    """Format function signature for hover display."""
    params = ", ".join(f"{p.name}: {p.type}" for p in func.params)
    return f"fn {func.name}({params}): {func.return_type}"


def main():
    server.start_io()


if __name__ == "__main__":
    main()
