# For Loop Design

## Overview

Add `for` loops with `break` and `continue` to Zero.

## Syntax

```
for_stmt = "for" "(" expr ")" block
block    = "{" stmt* "}"
```

The condition is evaluated before each iteration. Loop exits when condition is false.

```zero
i: int = 0
for (i < 10) {
    print(i)
    i += 1
}
```

### Break and Continue

```zero
for (i < 100) {
    if (i == 50) {
        break       # exit loop entirely
    }
    if (i == 13) {
        i += 1
        continue    # skip to next iteration (re-evaluate condition)
    }
    print(i)
    i += 1
}
```

- `break` - immediately exits the innermost loop
- `continue` - jumps to the condition check of the innermost loop

### Scoping

Block scoping: variables declared inside the loop body are not visible outside.

```zero
for (i < 3) {
    x: int = 10    # x only exists inside this block
    i += 1
}
print(x)           # Error: undefined variable 'x'
```

## Implementation Plan (TDD)

### Layer 1: Lexer

New tokens: `FOR`, `BREAK`, `CONTINUE`

Tests:
- `test_tokenize_for`
- `test_tokenize_break_continue`

### Layer 2: AST

New nodes:
- `ForStmt(condition: Expr, body: list[Stmt])`
- `BreakStmt()`
- `ContinueStmt()`

### Layer 3: Parser

Tests:
- `test_parse_for_loop`
- `test_parse_for_with_break`
- `test_parse_for_with_continue`
- `test_parse_nested_for`

### Layer 4: Semantic Analysis

Tests:
- `test_for_condition_must_be_bool`
- `test_break_outside_loop_error`
- `test_continue_outside_loop_error`
- `test_for_block_scoping`

### Layer 5: Compiler

New opcodes: `JUMP_BACK` (or reuse `JUMP` with backward offset)

The compiler needs to track loop context for break/continue:
- `break` compiles to `JUMP` to instruction after loop
- `continue` compiles to `JUMP` back to condition check

Tests:
- `test_compile_for_loop`
- `test_compile_break`
- `test_compile_continue`
- `test_compile_nested_loops_break`

### Layer 6: VM

No new opcodes needed if `JUMP` handles negative offsets. Otherwise add `JUMP_BACK`.

Tests:
- `test_execute_for_loop`
- `test_execute_for_with_break`
- `test_execute_for_with_continue`
- `test_execute_nested_for`

## Bytecode Structure

A `for` loop compiles to:

```
loop_start:
    <condition>
    JUMP_IF_FALSE end
    <body>
    JUMP loop_start
end:
    ...
```

With break/continue:
- `break` -> `JUMP end`
- `continue` -> `JUMP loop_start`

## Implementation Order

1. Lexer: `FOR`, `BREAK`, `CONTINUE` tokens
2. AST: `ForStmt`, `BreakStmt`, `ContinueStmt` nodes
3. Parser: for loop parsing
4. Parser: break/continue parsing
5. Semantic: condition type check
6. Semantic: break/continue must be inside loop
7. Semantic: block scoping for loop body
8. Compiler: for loop bytecode generation
9. Compiler: break/continue with loop context tracking
10. VM: execute loops (JUMP already exists)

Each step: write tests, see them fail, implement, green.
