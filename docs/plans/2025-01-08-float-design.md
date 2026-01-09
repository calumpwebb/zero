# Float Type Design

## Summary

Add a `float` type to Zero, backed by f64 (IEEE 754 double precision). Strict typing with no implicit int/float coercion.

## Design Decisions

### Type Name: `float`

- User-facing name: `float`
- Implementation: f64 (64-bit IEEE 754)
- Rationale: Friendly name, but documented as f64 for when we swap to Zig backend

### Literal Syntax

```zero
x: float = 3.14
y: float = 0.5
z: float = 1.0
```

**Allowed:**
- `3.14` - standard decimal
- `0.5` - leading zero required
- `1.0` - trailing zero required

**Not allowed (for now):**
- `.5` - no leading dot (ambiguous, harder to read)
- `5.` - no trailing dot (ambiguous, harder to read)
- `1e10` - no scientific notation (can add later)
- `1.5e-3` - no scientific with decimal (can add later)

### Strict Typing (No Implicit Coercion)

```zero
x: float = 5      # ERROR: expected float, got int
y: int = 3.14     # ERROR: expected int, got float
z = 5 + 3.14      # ERROR: cannot add int and float
```

Rationale: Maps cleanly to Zig backend. Forces explicit intent. Can relax later if needed.

### Future: Explicit Casting

```zero
x: float = float(5)    # explicit cast
y: int = int(3.14)     # explicit cast (truncates)
z = float(5) + 3.14    # works
```

Not implementing casts in first pass.

## Implementation Plan

### Phase 1: Lexer

New token type: `TokenType.FLOAT`

```python
def read_number(self):
    # ... read digits ...
    if self.current() == '.' and self.peek().isdigit():
        # it's a float
```

Edge cases to handle:
- `1.2.3` - error after first `.`
- `1..` - first `.` makes float, second is error (or future range syntax)

### Phase 2: AST

```python
@dataclass(frozen=True)
class FloatLiteral:
    value: float
```

### Phase 3: Parser

```python
case TokenType.FLOAT:
    return FloatLiteral(token.value)
```

### Phase 4: Semantic Analysis

```python
def type_of(expr, ...):
    match expr:
        case FloatLiteral(_):
            return "float"
```

Type checking for binary ops:
```python
case BinaryExpr(op, left, right):
    left_type = type_of(left, ...)
    right_type = type_of(right, ...)
    if left_type != right_type:
        raise SemanticError(f"cannot {op} {left_type} and {right_type}")
```

### Phase 5: Bytecode

New opcodes:
```python
class Op(Enum):
    # ... existing ...
    ADD_FLOAT = auto()
    SUB_FLOAT = auto()
    MUL_FLOAT = auto()
    DIV_FLOAT = auto()
```

Constant pool already holds Python values, so floats work there.

### Phase 6: Compiler

Emit typed opcodes based on operand types:
```python
case BinaryExpr("+", left, right):
    # ... compile left and right ...
    if expr_type == "float":
        emit(Op.ADD_FLOAT)
    else:
        emit(Op.ADD_INT)
```

### Phase 7: VM

```python
case Op.ADD_FLOAT:
    b = self.pop()
    a = self.pop()
    self.push(a + b)
```

### Phase 8: Builtins

`print()` already uses Python's print, so floats work automatically.

## IEEE 754 Edge Cases

We inherit IEEE 754 semantics. These behaviors are expected:

| Expression | Result | Notes |
|------------|--------|-------|
| `0.0 / 0.0` | NaN | Not a number |
| `1.0 / 0.0` | Infinity | Positive infinity |
| `-1.0 / 0.0` | -Infinity | Negative infinity |
| `0.1 + 0.2` | 0.30000000000000004 | Binary float precision |
| `-0.0 == 0.0` | true | Negative zero equals zero |
| `NaN == NaN` | false | NaN is not equal to anything |

Decision: Don't hide this. Let it happen. Document it.

## Literal Overflow/Precision

- `1e309` as a literal would overflow f64 - lexer should reject or produce Infinity?
- Very precise literals like `1.123456789012345678901234567890` get truncated silently (Python does this)

Decision for now: Let Python handle it during lexing. Revisit when we move to Zig.

## Future Considerations

### Range Syntax Conflict

If we add `1..10` range syntax later, need to handle:
- `1..10` - range from 1 to 10
- `1.0..2.0` - range of floats?
- `1. .5` - float 1.0 followed by error?

Avoiding `.5` and `5.` syntax now sidesteps some of this.

### Scientific Notation

Could add later:
- `1e10` → 10000000000.0
- `1.5e-3` → 0.0015
- `1E10` → case insensitive?

### f32 Type

If memory/perf matters, could add `f32` later. For now, just `float` (f64).

## Test Cases

### Lexer
- `3.14` → FLOAT token
- `0.5` → FLOAT token
- `1.0` → FLOAT token
- `.5` → error
- `5.` → error (or INT followed by DOT?)
- `1.2.3` → error

### Semantic
- `x: float = 3.14` → ok
- `x: float = 5` → error
- `x: int = 3.14` → error
- `3.14 + 2.0` → ok, float
- `3.14 + 2` → error

### VM
- `print(3.14)` → outputs 3.14
- `print(1.5 + 2.5)` → outputs 4.0
- `print(1.0 / 0.0)` → outputs inf
