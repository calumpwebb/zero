# Bytecode Compilation Design

## Overview

Add separate compilation and execution phases. Source files (`.zr`) compile to bytecode files (`.zrc`). The VM runs bytecode directly.

## File Extensions

| Extension | Purpose |
|-----------|---------|
| `.zr` | Source code |
| `.zrc` | Compiled bytecode |

## Bytecode Format

Use msgpack for serialization. Simple, maintainable, debuggable.

```python
{
    "version": 1,
    "program": {
        "chunks": [...],
        "function_index": {...}
    }
}
```

`dataclasses.asdict()` handles serialization automatically. New fields propagate without manual updates.

### Constraints

- Version mismatch: hard fail with recompile hint
- Max file size: 10MB
- Security: `max_buffer_size` on load

## Cache Location

Compiled files go in `.zr-cache/` alongside the source:

```
project/
  main.zr
  utils.zr
  .zr-cache/
    main.zrc
    utils.zrc
```

## CLI Design

Use Typer for argument parsing and help text.

### Commands

| Command | Description |
|---------|-------------|
| `zero <file>` | Run file (compile in memory if `.zr`) |
| `zero run <file>` | Explicit run |
| `zero build <file>` | Compile to `.zr-cache/` |
| `zero build <file> -o <path>` | Compile to specific path |
| `zero disasm <file>` | Disassemble source or bytecode |

### Extension Detection

- `.zr` input: compile first (in memory or to cache)
- `.zrc` input: load and run directly

## Dependencies

Add to `pyproject.toml`:
- `msgpack` - bytecode serialization
- `typer` - CLI framework

## Implementation Plan (TDD)

### Layer 1: Bytecode Serialization

New functions in `bytecode.py`:
- `save_program(program: CompiledProgram, path: Path) -> None`
- `load_program(path: Path) -> CompiledProgram`

Tests (`tests/test_bytecode.py`):
- `test_save_load_roundtrip` - save then load produces identical program
- `test_version_mismatch_raises` - wrong version fails with clear error
- `test_load_oversized_file_raises` - files over 10MB rejected
- `test_load_corrupt_file_raises` - invalid msgpack fails gracefully

### Layer 2: Cache Directory

New module `zero/cache.py`:
- `get_cache_path(source_path: Path) -> Path` - returns `.zr-cache/<name>.zrc`
- `ensure_cache_dir(source_path: Path) -> None` - creates `.zr-cache/` if needed

Tests (`tests/test_cache.py`):
- `test_cache_path_structure` - correct path returned
- `test_cache_dir_created` - directory created if missing

### Layer 3: CLI Commands

Replace current `main.py` with Typer app.

Commands:
- `build(file: Path, output: Path | None)`
- `run_file(file: Path)`
- `disasm(file: Path)`
- `main(file: Path | None)` - default callback

Tests (`tests/test_cli.py`):
- `test_run_zr_file` - compiles and executes
- `test_run_zrc_file` - loads and executes
- `test_build_creates_cache` - `.zrc` appears in `.zr-cache/`
- `test_build_custom_output` - `-o` flag respected
- `test_disasm_zr_file` - shows bytecode from source
- `test_disasm_zrc_file` - shows bytecode from compiled
- `test_run_missing_file` - clear error message
- `test_build_invalid_source` - parse errors reported

### Layer 4: File Extension Rename

Rename `.zero` to `.zr` throughout:
- Example files in `examples/`
- VS Code extension grammar
- Documentation

Tests:
- All existing tests continue passing with new extension

## Implementation Order

1. Add `msgpack` and `typer` dependencies
2. Write serialization tests, implement `save_program`/`load_program`
3. Write cache tests, implement `cache.py`
4. Write CLI tests, implement Typer commands
5. Rename example files `.zero` → `.zr`
6. Update VS Code extension
7. Update `CLAUDE.md` and `README.md`

Each step: write tests, see them fail, implement, verify green.

## Not Included (YAGNI)

- Obfuscation
- Incremental compilation
- Watch mode
- Optimization flags
- Config files
