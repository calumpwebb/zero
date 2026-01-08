# Automatic Purity Tracking for Workflow-Native Code

## The Problem

Zero is intended for writing Temporal-style workflows where:
- **Workflows** must be deterministic (replay-safe)
- **Activities** can have side effects (IO, time, network)

Traditionally, developers must manually annotate or structure code to separate these concerns. This is error-prone and adds cognitive overhead.

## The Idea

**The compiler automatically detects which functions are pure vs impure ("tainted") and treats them differently at runtime.**

Developers write normal code. The compiler figures out the rest.

## Developer Experience

```zero
fn process_order(order_id: str) {
    order: Order = fetch_order(order_id)   # compiler knows this is IO

    if (order.total > 1000) {
        send_email(order.customer, "Big order!")  # also IO
    }

    result: int = calculate_tax(order.total)  # pure math, stays in workflow

    save_result(order_id, result)  # IO again
}
```

No annotations. No special syntax. The compiler infers:
- `fetch_order` → Activity (network IO)
- `calculate_tax` → inline Workflow code (pure)
- `send_email` → Activity (IO)
- `save_result` → Activity (IO)

## Tainting Rules

A function is **tainted** if it:
1. Calls a builtin that performs IO (`http_get`, `db_query`, `now`, `random`, `print`, `read_file`, etc.)
2. Calls another tainted function (transitive)

Everything else is **pure** by default.

## Compilation Pipeline

```
Source Code
    ↓
Compiler analyzes call graph
    ↓
Marks functions as PURE or TAINTED
    ↓
TAINTED functions compile to "activity calls"
PURE functions compile to normal bytecode
    ↓
VM/Runtime handles activity dispatch + replay
```

## Open Questions

### Runtime Behavior
When a tainted function runs as an activity, what happens?
- **Temporal-style**: Activity results get stored, replays skip re-execution
- **Simpler**: Just mark the boundary, let an external runtime handle it
- **Custom runtime**: Zero provides its own workflow engine

### Explicit Override
Should developers be able to force a function to be treated as pure/tainted?
```zero
@pure  # trust me, compiler
fn cached_lookup(key: str) -> str { ... }
```

### Granularity
Is the boundary at the function level, or could we be smarter?
```zero
fn mixed() {
    x: int = pure_calc()      # inline
    y: int = fetch_thing()    # activity
    z: int = x + y            # inline again?
}
```

### Testing
How does this interact with mocking?
- Tainted builtins could be swappable at test time
- Or: test harness provides fake activity implementations

### Visibility
Should the compiler/IDE show developers what it inferred?
```
$ zero analyze process_order.zero

process_order: WORKFLOW
  ├─ fetch_order: ACTIVITY (network)
  ├─ calculate_tax: PURE
  ├─ send_email: ACTIVITY (network)
  └─ save_result: ACTIVITY (network)
```

## Related Concepts

- **Haskell IO Monad**: Explicit purity tracking, but requires manual annotation
- **Effect Systems (Koka, Unison)**: Inferred effects, powerful but complex syntax
- **Temporal Workflows**: Manual workflow/activity separation
- **Deno Permissions**: Runtime capability control

## Why This Could Be Special

Most languages make purity tracking opt-in or verbose. Zero could make it:
1. **Automatic** - inferred from what you actually call
2. **Invisible** - no syntax overhead for the common case
3. **Workflow-native** - designed for durable execution from day one

The language becomes a natural fit for reliable, replayable distributed systems.
