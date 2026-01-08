# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build & Run Commands

```bash
# Install dependencies
uv sync

# Run all tests
python -m pytest -v

# Run single test file
python -m pytest tests/test_lexer.py -v

# Run single test
python -m pytest tests/test_lexer.py::test_tokenize_integer -v

# Execute a Zero program
python main.py examples/add.zero

# Disassemble bytecode (view compiled output)
python main.py -d examples/add.zero
```

## Architecture

Zero is a minimalist compiled language with a classic pipeline: **Source → Lexer → Parser → Compiler → VM**

```
Source Code (.zero)
       ↓
   Lexer (lexer.py) → Tokens
       ↓
   Parser (parser.py) → AST (ast.py)
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

## Conventions

- Use conventional commits: `feat:`, `fix:`, `docs:`, `chore:`, `refactor:`
- No `__init__.py` files (PEP 420 namespace packages)
- Python 3.14+ required
