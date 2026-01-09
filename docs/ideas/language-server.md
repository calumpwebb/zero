# Zero Language Server (LSP)

## The Idea

Build a Language Server Protocol (LSP) implementation for Zero, enabling rich IDE support in any editor.

## What LSP Provides

| Feature | Description |
|---------|-------------|
| **Diagnostics** | Real-time error/warning squiggles |
| **Autocomplete** | Suggest functions, variables, types |
| **Go to Definition** | Jump to where something is defined |
| **Find References** | Find all usages of a symbol |
| **Hover** | Show type info and docs on hover |
| **Rename** | Refactor symbol names across files |
| **Signature Help** | Show function parameters as you type |
| **Formatting** | Auto-format code |
| **Code Actions** | Quick fixes, refactorings |

## Architecture

```
┌─────────────┐         LSP (JSON-RPC)         ┌─────────────┐
│   Editor    │◄──────────────────────────────►│   Zero LS   │
│  (VS Code,  │    - textDocument/didOpen      │             │
│   Neovim,   │    - textDocument/completion   │  ┌───────┐  │
│   etc.)     │    - textDocument/definition   │  │Lexer  │  │
└─────────────┘    - textDocument/diagnostic   │  │Parser │  │
                                               │  │Semantic│  │
                                               │  └───────┘  │
                                               └─────────────┘
```

The language server reuses Zero's compiler frontend:
- **Lexer** → token positions for syntax highlighting
- **Parser** → AST for structure understanding
- **Semantic analysis** → types, scopes, errors

## Implementation Options

### Option A: Python-based (pygls)

Use the existing Python compiler directly:

```python
from pygls.server import LanguageServer
from zero.lexer import tokenize
from zero.parser import parse
from zero.semantic import analyze

server = LanguageServer("zero-ls", "0.1.0")

@server.feature("textDocument/didOpen")
def did_open(params):
    text = params.text_document.text
    tokens = tokenize(text)
    ast = parse(tokens)
    errors = analyze(ast)
    # publish diagnostics...
```

**Pros:** Fast to build, reuses existing code
**Cons:** Python startup time, memory usage

### Option B: Compile to standalone binary

Rewrite compiler frontend in Go/Rust/Zig, ship single binary:

```
$ zero-ls --stdio
```

**Pros:** Fast startup, low memory, easy distribution
**Cons:** Maintain two implementations (or rewrite compiler)

### Option C: Python with persistent process

Keep Python LS running, optimize for incremental updates:

```python
# Cache parsed files, only re-parse changed regions
class ZeroLanguageServer:
    def __init__(self):
        self.file_cache = {}  # path -> (ast, version)
```

**Pros:** Best of both - reuse Python, acceptable perf
**Cons:** More complexity

## Features by Priority

### Phase 1: Basics
- [ ] Diagnostics (syntax errors, type errors)
- [ ] Go to definition (functions)
- [ ] Hover (show type)

### Phase 2: Productivity
- [ ] Autocomplete (variables in scope, functions)
- [ ] Find all references
- [ ] Signature help

### Phase 3: Polish
- [ ] Rename symbol
- [ ] Code formatting
- [ ] Code actions (quick fixes)
- [ ] Semantic highlighting

## Editor Integration

### VS Code

Already have `zero-vscode` extension with syntax highlighting. Add LSP:

```json
// package.json
{
  "contributes": {
    "languages": [{"id": "zero", "extensions": [".zero"]}]
  },
  "main": "./extension.js"
}
```

```javascript
// extension.js
const { LanguageClient } = require('vscode-languageclient');

const client = new LanguageClient(
  'zero-ls',
  { command: 'python', args: ['-m', 'zero.ls'] },
  { documentSelector: [{ scheme: 'file', language: 'zero' }] }
);
client.start();
```

### Neovim

```lua
-- init.lua
vim.lsp.start({
  name = 'zero-ls',
  cmd = {'python', '-m', 'zero.ls'},
  root_dir = vim.fn.getcwd(),
})
```

### Other Editors

LSP is universal - Emacs, Sublime, Helix, Zed all support it.

## Incremental Parsing

For good UX, don't re-parse entire file on every keystroke:

```
User types character
       │
       ▼
┌─────────────────┐
│ Debounce 100ms  │
└─────────────────┘
       │
       ▼
┌─────────────────┐
│ Incremental     │  ← Only re-lex changed region
│ tokenize        │  ← Reuse unchanged tokens
└─────────────────┘
       │
       ▼
┌─────────────────┐
│ Incremental     │  ← tree-sitter style, or
│ parse           │  ← re-parse affected function only
└─────────────────┘
       │
       ▼
┌─────────────────┐
│ Publish         │
│ diagnostics     │
└─────────────────┘
```

## Connection to Other Ideas

### AI Docs Integration
The language server could power the AI assistant:
- User hovers over code → LS provides type info → AI explains it
- User gets error → LS provides diagnostic → AI suggests fix

### Purity Tracking
Show purity in the editor:
```
fn fetch_order(id: str) -> Order  # tainted (IO)
   ^^^^^^^^^^^^^^^^^^^^^^^^^
   ⚠️ This function performs IO - will run as Activity
```

### DST Integration
- Highlight non-deterministic operations
- Show which functions are replay-safe

## Open Questions

1. **Startup time** - Python cold start acceptable? Use daemon?

2. **Multi-file projects** - How to handle imports/modules? Project root detection?

3. **Error recovery** - Parser needs to handle incomplete/broken code gracefully

4. **Testing** - How to test LSP features? Mock editor?

## Resources

- [LSP Specification](https://microsoft.github.io/language-server-protocol/)
- [pygls](https://github.com/openlawlibrary/pygls) - Python LSP framework
- [tower-lsp](https://github.com/ebkalderon/tower-lsp) - Rust LSP framework
- [tree-sitter](https://tree-sitter.github.io/) - Incremental parsing
