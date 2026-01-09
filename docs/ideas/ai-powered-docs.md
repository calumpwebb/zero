# AI-Powered Documentation Website

## The Idea

A documentation website for Zero that:

1. **AI-generated** - docs derived from source code, always accurate
2. **Interactive tutorials** - learn Zero step by step
3. **AI assistant** - chat with a bot that knows Zero deeply

## Why AI-Generated?

Traditional docs rot. Code changes, docs don't. With AI:

- Parse the compiler source → generate language reference
- Parse example files → generate tutorial content
- Parse test files → generate "how to" guides
- Changes to Zero automatically flow to docs

## Components

### 1. Language Reference (auto-generated)

```
Source of truth: lexer.py, parser.py, ast.py

Generated pages:
  /docs/syntax/functions
  /docs/syntax/types
  /docs/syntax/operators
  /docs/builtins/print
  /docs/builtins/now
```

AI reads the compiler and generates human-friendly explanations.

### 2. Tutorials (curated + AI-enhanced)

```
/learn/getting-started
/learn/functions
/learn/control-flow
/learn/workflows        # the temporal stuff
/learn/testing          # DST, mocking
```

Could be:
- Human-written outlines, AI-expanded
- Interactive code playgrounds (WASM VM?)
- Progressive exercises

### 3. AI Chat Assistant

Embedded chatbot that can:
- Answer "how do I X in Zero?"
- Explain error messages
- Suggest code improvements
- Reference the docs contextually

### Technical Approach

```
┌─────────────────┐
│  Zero Source    │
│  (compiler,     │
│   examples,     │──────► AI Processing ──────► Markdown/MDX
│   tests)        │
└─────────────────┘
                                                      │
                                                      ▼
                                              ┌──────────────┐
                                              │  Doc Website │
                                              │  (Astro,     │
                                              │   Docusaurus,│
                                              │   etc.)      │
                                              └──────────────┘
                                                      │
                                              ┌───────┴───────┐
                                              │  AI Assistant │
                                              │  (RAG over    │
                                              │   docs +      │
                                              │   source)     │
                                              └───────────────┘
```

### AI Assistant Architecture

**Option A: RAG (Retrieval Augmented Generation)**
- Index all docs + source code
- User asks question → retrieve relevant chunks → LLM answers

**Option B: Fine-tuned model**
- Train/fine-tune on Zero specifically
- Deeper understanding, but more maintenance

**Option C: Claude with MCP**
- Claude as the assistant
- MCP server exposing Zero docs/source
- Users get Claude-quality answers with Zero context

## Possible Features

### Interactive Playground
```
┌─────────────────────────────────────┐
│ fn main() {           │  Output:   │
│     x: int = 5        │  15        │
│     print(x + 10)     │            │
│ }                     │            │
│                       │            │
│ [Run] [Share] [Ask AI]│            │
└─────────────────────────────────────┘
```

### Error Explainer
```
Error: type mismatch: expected int, got str at line 5

[Explain this error]

AI: "You're trying to assign a string to a variable
declared as int. In Zero, variables have fixed types..."
```

### Code Review Bot
```
[Paste your Zero code]

AI: "A few suggestions:
- Line 3: This loop could use a for-range instead
- Line 7: Consider extracting this to a pure function
  for easier testing..."
```

## Open Questions

1. **Hosting** - Static site (Vercel, Netlify)? Self-hosted?

2. **Generation pipeline** - CI/CD on every commit? Manual trigger?

3. **Playground backend** - WASM Zero VM? Server-side execution? Security?

4. **AI costs** - Free tier? Rate limiting? Sponsorship?

5. **Community contributions** - Can users improve docs via PR? How does AI merge with human edits?

## Inspiration

- **Rust Book** - excellent progressive tutorials
- **Zig docs** - generated from source with examples
- **Deno** - clean, modern docs with playground
- **Cursor/Copilot** - AI that knows your codebase
- **Phind/Perplexity** - conversational code search
