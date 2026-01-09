# Determinism and Predictable Memory

## Core Principle

Zero should be **fully deterministic** - given the same inputs, always produce the same outputs, same execution path, same memory behavior. This enables:

- Deterministic Simulation Testing (DST)
- Workflow replay (Temporal-style)
- Debugging via replay
- Formal reasoning about programs

## Deterministic Simulation Testing (DST)

Popularized by FoundationDB. The idea: control all non-determinism so you can:

1. **Replay** - reproduce any execution exactly
2. **Explore** - try different schedules/interleavings
3. **Shrink** - find minimal failing case

### Sources of Non-Determinism to Control

| Source | Strategy |
|--------|----------|
| Time | Virtual clock, injectable via context |
| Randomness | Seeded PRNG, passed explicitly or via context |
| IO / Network | All IO through tainted functions → activities |
| Concurrency | Deterministic scheduler (if we add concurrency) |
| Memory addresses | Never expose raw pointers - use handles/indices |
| Hash/map iteration | Deterministic ordering (insertion order or sorted) |
| Floating point | Consider restricting or requiring exact semantics |

### Connection to Purity Tracking

The automatic purity tracking idea (see `automatic-purity-tracking.md`) directly supports DST:

- Pure functions: fully deterministic, replay inline
- Tainted functions: IO boundary, results recorded for replay

## Zig-Style Memory Model

Zig's philosophy: **no hidden allocations**, explicit memory control.

### Key Ideas to Borrow

**1. Allocators are explicit**
```zig
// Zig
var list = ArrayList(u8).init(allocator);
```

Zero equivalent concept:
```zero
# Memory budget declared upfront
fn process(arena: Arena) {
    items: Array<int> = arena.array(100)  # capacity explicit
}
```

**2. No global allocator**

Every function that needs memory receives an allocator/arena. Makes memory flow visible.

**3. Comptime known sizes when possible**
```zero
buffer: [u8; 1024]  # size known at compile time, stack allocated
```

**4. Fail explicitly on OOM**

No hidden panics. Allocation returns error or requires pre-sized arena.

### Possible Zero Memory Model

```zero
# Option A: Arena-based, capacity declared upfront
fn main() {
    with arena(1MB) {
        data: Array<int> = new_array(1000)  # from arena
        # ...
    }  # arena freed here
}

# Option B: All capacities explicit
fn main() {
    data: Array<int, 1000> = []  # max 1000 elements
    push(data, 5)  # ok
    # push past 1000 → compile error or explicit error handling
}

# Option C: Handle-based with explicit pools
pool: Pool<Point, 100> = new_pool()  # 100 Points max
p: Handle<Point> = pool.alloc()
```

## How These Ideas Connect

```
┌─────────────────────────────────────────────────────┐
│                    Zero Program                      │
├─────────────────────────────────────────────────────┤
│  Pure Functions        │  Tainted Functions          │
│  (deterministic)       │  (IO, recorded for replay)  │
├─────────────────────────────────────────────────────┤
│  Stack Memory          │  Arena/Pool Memory          │
│  (locals, fixed size)  │  (explicit capacity)        │
├─────────────────────────────────────────────────────┤
│  Handles (0,1,2...)    │  No raw pointers            │
│  (deterministic IDs)   │  (no address leakage)       │
└─────────────────────────────────────────────────────┘
                         │
                         ▼
              DST: Fully replayable execution
```

## Open Questions

1. **Arena lifetime** - Lexical scope? Explicit free? Tied to workflow step?

2. **OOM handling** - Compile-time capacity checks? Runtime errors? Pre-flight validation?

3. **Concurrency model** - If added, how to make scheduling deterministic? Cooperative? Actor-based?

4. **Serialization** - For replay, all values must be serializable. Restrict types? Auto-derive?

5. **External state** - Database, files, network. All must go through recorded activity layer.

## Inspiration

- **FoundationDB** - DST pioneer, caught bugs no other technique found
- **Zig** - Explicit allocators, no hidden control flow
- **Temporal** - Workflow replay, deterministic re-execution
- **TigerBeetle** - DST + explicit memory, written in Zig
- **Unison** - Content-addressed code, reproducible by design
