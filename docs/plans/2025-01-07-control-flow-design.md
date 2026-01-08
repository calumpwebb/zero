# Control Flow & Variables Design

## Overview

Add if/else statements, comparison operators, and typed variable declarations to Zero.

## Syntax

### Variable Declaration & Assignment

```
var_decl   = IDENT ":" type "=" expr
assignment = IDENT "=" expr
```

Variables have fixed types but mutable values:

```zero
x: int = 5
x = 10          # ok - same type
x = x + 1       # ok
name: str = "hi"
name = 42       # error - type mismatch
```

### If Statements

```
if_stmt = "if" "(" expr ")" block [ "else" block ]
block   = "{" stmt* "}"
```

Parentheses around the condition are required. Else is optional.

```zero
if (x > 5) {
    return 1
} else {
    return 0
}
```

### Comparison Operators

All six: `==`, `!=`, `<`, `>`, `<=`, `>=`

```
compare = expr ( "==" | "!=" | "<" | ">" | "<=" | ">=" ) expr
```

Comparisons are non-associative (no chaining).

### Operator Precedence

Low to high:

1. Comparisons: `==`, `!=`, `<`, `>`, `<=`, `>=`
2. Additive: `+`, `-`
3. Primary: literals, identifiers, calls

## Implementation Plan (TDD)

### Layer 1: Lexer

New tokens: `IF`, `ELSE`, `EQ`, `NE`, `LT`, `GT`, `LE`, `GE`, `ASSIGN`

Tests:
- `test_tokenize_if_else`
- `test_tokenize_comparison_operators`
- `test_tokenize_assignment`

### Layer 2: AST

New nodes:
- `IfStmt(condition: Expr, then_body: list[Stmt], else_body: list[Stmt] | None)`
- `VarDecl(name: str, type: str, value: Expr)`
- `Assignment(name: str, value: Expr)`

### Layer 3: Parser

Tests:
- `test_parse_var_decl`
- `test_parse_assignment`
- `test_parse_comparison`
- `test_parse_if_no_else`
- `test_parse_if_else`
- `test_parse_comparison_precedence`

### Layer 4: Semantic Analysis

Tests:
- `test_var_decl_type_recorded`
- `test_assignment_type_mismatch`
- `test_undefined_variable`
- `test_comparison_requires_same_types`
- `test_if_condition_must_be_bool`

### Layer 5: Compiler

New opcodes: `CMP_EQ`, `CMP_NE`, `CMP_LT`, `CMP_GT`, `CMP_LE`, `CMP_GE`, `JUMP`, `JUMP_IF_FALSE`, `STORE`

Tests:
- `test_compile_comparison`
- `test_compile_var_decl`
- `test_compile_assignment`
- `test_compile_if_else`

### Layer 6: VM

Tests:
- `test_execute_comparison_ops`
- `test_execute_if_true_branch`
- `test_execute_if_false_branch`
- `test_variable_store_and_load`
- `test_variable_reassignment`

## Implementation Order

1. Lexer tokens
2. AST nodes
3. Parser: variables
4. Parser: comparisons
5. Parser: if/else
6. Semantic: variables
7. Semantic: if/else
8. Compiler: variables
9. Compiler: comparisons + jumps
10. Compiler: if/else
11. VM: new opcodes

Each step: write tests, see them fail, implement, green.
