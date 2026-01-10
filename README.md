# Zero

A friendly, type-safe programming language for backend systems.

## Quick Start

```bash
# Install dependencies
uv sync

# Run a program
zero run examples/01_hello.zr

# Run tests
python -m pytest -v
```

## Editor Integration

Zero includes an LSP server for editor support (diagnostics, go-to-definition, hover):

```bash
uv run python -m zero.lsp
```

See [CLAUDE.md](CLAUDE.md) for editor configuration examples.

## Examples

See [examples/](examples/) for sample programs.
