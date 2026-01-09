# Builtin Stub Files for LSP

## Problem

When a user clicks "go to definition" on `print()` or other builtins, the LSP has nowhere to navigate - builtins are implemented in Python (`zero/builtins.py`), not in Zero source code.

## Idea

Create a `builtins.zero` stub file containing signatures for all builtin functions:

```zero
# Built-in functions
# These are implemented in the VM, not Zero code

fn print(value: any) {
    # Prints value to stdout
}
```

## How Other Languages Handle This

| Language | Approach |
|----------|----------|
| TypeScript | Ships `.d.ts` declaration files with signatures |
| Python (Pyright) | Uses `.pyi` stub files |
| Rust/Go | Standard library is real source code |
| Java | Attached JDK source, or shows signature only |

## Benefits

- Go-to-definition works naturally (real file, normal parsing)
- Can include doc comments for hover
- Users can read it to learn available builtins
- No special LSP code needed - just another Zero file

## Implementation

1. Create `zero/builtins.zero` with all builtin signatures
2. LSP loads this file alongside user code when searching for definitions
3. Keep `builtins.zero` in sync with `builtins.py` (could be generated or manual)

## Open Questions

- Should it live in the zero package or be generated at runtime?
- How to handle doc comments / documentation?
- What about type `any` - does Zero need this type for builtins?
