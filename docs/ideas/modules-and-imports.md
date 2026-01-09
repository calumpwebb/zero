# Modules and Imports

## The Idea

A module system for Zero inspired by Go's simplicity: `zero.mod` for project config, clean import paths, minimal ceremony.

## Goals

1. **Simple** - no complex package managers, lock files, or version resolution nightmares
2. **Explicit** - clear what code depends on what
3. **Deterministic** - same imports always resolve the same way (fits DST goals)
4. **Minimal** - don't over-engineer for v1

## zero.mod File

Project root marker and configuration:

```
// zero.mod
module github.com/user/myproject

zero 0.1
```

That's it for v1. Maybe later:

```
// zero.mod (future)
module github.com/user/myproject

zero 0.1

require (
    github.com/someone/utils v1.2.0
    github.com/other/lib v0.5.0
)
```

## Import Syntax Options

### Option A: Go-style paths

```zero
import "github.com/user/myproject/utils"
import "std/io"

fn main() {
    utils.helper()
    io.print("hello")
}
```

### Option B: Relative paths only (simpler)

```zero
import "./utils"
import "../shared/types"

fn main() {
    utils.helper()
}
```

### Option C: Named imports

```zero
import utils from "./utils"
import { helper, format } from "./utils"  // selective
import io from "std/io"

fn main() {
    helper()
}
```

### Option D: Implicit (no import statement)

Everything in project is available, namespaced by directory:

```
myproject/
  zero.mod
  main.zero        # can use utils.helper()
  utils/
    helpers.zero   # defines helper()
```

Compiler figures it out. Feels magic but removes boilerplate.

## File Organization

```
myproject/
├── zero.mod
├── main.zero
├── lib/
│   ├── math.zero      # exports: add, multiply
│   └── strings.zero   # exports: concat, split
└── internal/
    └── helpers.zero   # only visible within project
```

## What Gets Exported?

### Option A: Everything public by default

```zero
fn helper() { }        // exported
fn _private() { }      // underscore = private
```

### Option B: Explicit pub keyword

```zero
pub fn helper() { }    // exported
fn private() { }       // not exported
```

### Option C: Export list

```zero
// utils.zero
export { helper, format }

fn helper() { }
fn format() { }
fn internal() { }  // not in export list
```

## Standard Library

```
std/
├── io          # print, read (tainted - IO)
├── time        # now, sleep (tainted - IO)
├── math        # abs, min, max (pure)
├── strings     # concat, split, trim (pure)
├── random      # rand, seed (tainted - non-deterministic)
└── testing     # assert, mock utilities
```

Import as:
```zero
import "std/io"
import "std/math"
```

## Dependency Resolution

### v1: No external deps

Just local imports within your project. Keep it simple.

### v2: Git-based (like Go)

```
// zero.mod
require (
    github.com/someone/utils v1.2.0
)
```

Zero fetches the repo at that tag/commit. Cached locally.

```
~/.zero/
  cache/
    github.com/
      someone/
        utils@v1.2.0/
```

### v3: Content-addressed (like Unison/IPFS)

Imports by hash, not version:

```zero
import "sha256:abc123.../utils"
```

Fully deterministic, immutable. Exotic but interesting for DST.

## Circular Imports

### Option A: Forbid them

Compiler error if A imports B imports A. Simple, forces good design.

### Option B: Allow within module

Files in same directory can be circular, across directories forbidden.

### Option C: Lazy resolution

Allow cycles, resolve at link time. More complex.

**Recommendation:** Forbid for v1. Keeps compiler simple.

## Build Process

```bash
# Single file
zero run main.zero

# Project (finds zero.mod, builds everything)
zero build

# Output
zero build -o myapp
```

Compiler walks imports, builds dependency graph, compiles in order.

## Caching / Incremental Builds

```
.zero/
  cache/
    lib/math.zero.cache      # compiled bytecode
    lib/strings.zero.cache
```

Only recompile changed files + their dependents.

## Connection to Other Ideas

### Purity Tracking
Imports could carry purity info:

```zero
import "std/io"      // compiler knows: this module is tainted
import "std/math"    // compiler knows: this module is pure
```

Functions using tainted imports become tainted.

### Determinism
For DST, imports must be deterministic:
- Same import path → same code, always
- Version pinning or content-addressing
- No floating versions

### Language Server
LSP needs to understand imports for:
- Go to definition across files
- Autocomplete from imported modules
- Find references across project

## Open Questions

1. **One file = one module?** Or can a module span files?

2. **Init functions?** Code that runs on import? (Go has `init()`)

3. **Conditional imports?** Platform-specific code?

4. **Vendoring?** Copy deps into project?

5. **Private modules?** `internal/` convention like Go?

6. **Naming conflicts?** Two imports with same function name?

## Inspiration

- **Go** - `go.mod`, simple paths, minimal ceremony
- **Rust** - `Cargo.toml`, explicit exports with `pub`
- **Python** - file = module, `__init__.py` for packages
- **Deno** - URL imports, no package.json
- **Unison** - content-addressed, no versioning problems
