# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build & Run Commands

```bash
# Install dependencies
uv sync

# Run all tests
python -m pytest -v

# Execute a Zero program
zero run examples/01_hello.zr

# Compile to bytecode
zero build examples/01_hello.zr          # → examples/.zr-cache/01_hello.zrc
zero build examples/01_hello.zr -o out.zrc  # → out.zrc

# Run compiled bytecode
zero run out.zrc

# Disassemble (view bytecode)
zero disasm examples/01_hello.zr
zero disasm out.zrc
```

## Architecture

Zero is a minimalist compiled language with a classic pipeline: **Source → Lexer → Parser → Compiler → VM**

```
Source Code (.zr)
       ↓
   Lexer (lexer.py) → Tokens with line/column
       ↓
   Parser (parser.py) → AST with Span (ast.py)
       ↓
   Compiler (compiler.py) → Bytecode (bytecode.py)
       ↓
   VM (vm.py) → Execution
```

### Key Components

- **Lexer**: Tokenizes source into keywords (`fn`, `return`), identifiers, integers, and symbols
- **AST**: Frozen dataclasses representing expressions (`IntLiteral`, `Identifier`, `BinaryExpr`, `Call`) and statements (`ReturnStmt`, `ExprStmt`)
- **Parser**: Recursive descent parser producing AST; handles operator precedence for additive expressions
- **Compiler**: Single-pass bytecode emitter with constant pool and slot-based local variables (parameters become stack slots)
- **Bytecode**: 7 opcodes (`CONST`, `LOAD`, `ADD`, `CALL`, `RET`, `POP`, `CALL_BUILTIN`)
- **VM**: Stack-based execution with call frame stack for nested function calls; entry point is always `main()`

### Language Features

Currently supports: integer literals, function definitions with typed parameters, function calls, addition (`+`), and `print()` builtin.

## LSP Server

Zero includes a Language Server Protocol implementation for editor integration.

**Features:**
- Diagnostics (parse errors, semantic errors)
- Go-to-definition (jump to function definitions)
- Hover (show function signatures)

**Editor Setup:**

VS Code:
```bash
cd zero-vscode && npm install
ln -s "$(pwd)/zero-vscode" ~/.vscode/extensions/zero-language
# Reload VS Code
```

Neovim (with nvim-lspconfig):
```lua
require('lspconfig').zero.setup {
    cmd = { "uv", "run", "python", "-m", "zero.lsp" }
}
```

Helix (`languages.toml`):
```toml
[[language]]
name = "zero"
language-server = { command = "uv", args = ["run", "python", "-m", "zero.lsp"] }
```

## Conventions

- Use conventional commits: `feat:`, `fix:`, `docs:`, `chore:`, `refactor:`
- No `__init__.py` files (PEP 420 namespace packages)
- Python 3.14+ required
