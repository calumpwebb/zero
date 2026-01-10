# Bytecode Compilation Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add separate compile/run phases with `.zr` source files compiling to `.zrc` bytecode files.

**Architecture:** msgpack serializes `CompiledProgram` dataclass to binary. Typer CLI provides `build`, `run`, and `disasm` commands. Cache directory `.zr-cache/` stores compiled output.

**Tech Stack:** msgpack (serialization), typer (CLI)

---

## Task 1: Add Dependencies

**Files:**
- Modify: `pyproject.toml`

**Step 1: Add msgpack and typer to dependencies**

Edit `pyproject.toml`, change:
```toml
dependencies = []
```
to:
```toml
dependencies = [
    "msgpack>=1.0.0",
    "typer>=0.9.0",
]
```

**Step 2: Sync dependencies**

Run: `cd /Users/calum/Development/zero && uv sync`
Expected: Dependencies installed successfully

**Step 3: Verify imports work**

Run: `cd /Users/calum/Development/zero && python -c "import msgpack; import typer; print('ok')"`
Expected: `ok`

**Step 4: Commit**

```bash
cd /Users/calum/Development/zero && git add pyproject.toml uv.lock && git commit -m "chore: add msgpack and typer dependencies"
```

---

## Task 2: Bytecode Serialization - Roundtrip Test

**Files:**
- Create: `tests/test_bytecode_io.py`
- Modify: `zero/bytecode.py`

**Step 1: Write the failing test**

Create `tests/test_bytecode_io.py`:
```python
import tempfile
from pathlib import Path

from zero.bytecode import Chunk, CompiledProgram, save_program, load_program


def test_save_load_roundtrip():
    """Save then load produces identical program."""
    original = CompiledProgram(
        chunks=[
            Chunk(code=[0, 1, 10, 72], constants=[42, 7], arity=0),
            Chunk(code=[1, 0, 72], constants=[], arity=1),
        ],
        function_index={"main": 0, "helper": 1},
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "test.zrc"
        save_program(original, path)
        loaded = load_program(path)

    assert loaded.function_index == original.function_index
    assert len(loaded.chunks) == len(original.chunks)
    for orig_chunk, load_chunk in zip(original.chunks, loaded.chunks):
        assert load_chunk.code == orig_chunk.code
        assert load_chunk.constants == orig_chunk.constants
        assert load_chunk.arity == orig_chunk.arity
```

**Step 2: Run test to verify it fails**

Run: `cd /Users/calum/Development/zero && python -m pytest tests/test_bytecode_io.py::test_save_load_roundtrip -v`
Expected: FAIL with `ImportError: cannot import name 'save_program'`

**Step 3: Write minimal implementation**

Add to `zero/bytecode.py`:
```python
import dataclasses
from pathlib import Path

import msgpack

BYTECODE_VERSION = 1
MAX_BYTECODE_SIZE = 10 * 1024 * 1024  # 10MB


def save_program(program: CompiledProgram, path: Path) -> None:
    """Serialize compiled program to bytecode file."""
    data = {
        "version": BYTECODE_VERSION,
        "program": dataclasses.asdict(program),
    }
    with open(path, "wb") as f:
        msgpack.pack(data, f, use_bin_type=True)


def load_program(path: Path) -> CompiledProgram:
    """Load compiled program from bytecode file."""
    file_size = path.stat().st_size
    if file_size > MAX_BYTECODE_SIZE:
        raise ValueError(f"Bytecode file too large: {file_size} bytes (max {MAX_BYTECODE_SIZE})")

    with open(path, "rb") as f:
        data = msgpack.unpack(f, raw=False, strict_map_key=False)

    if data["version"] != BYTECODE_VERSION:
        raise ValueError(
            f"Bytecode version mismatch: file has v{data['version']}, "
            f"VM expects v{BYTECODE_VERSION}. Recompile your source."
        )

    p = data["program"]
    return CompiledProgram(
        chunks=[Chunk(**c) for c in p["chunks"]],
        function_index=p["function_index"],
    )
```

**Step 4: Run test to verify it passes**

Run: `cd /Users/calum/Development/zero && python -m pytest tests/test_bytecode_io.py::test_save_load_roundtrip -v`
Expected: PASS

**Step 5: Commit**

```bash
cd /Users/calum/Development/zero && git add tests/test_bytecode_io.py zero/bytecode.py && git commit -m "feat: add bytecode save/load with msgpack serialization"
```

---

## Task 3: Version Mismatch Test

**Files:**
- Modify: `tests/test_bytecode_io.py`

**Step 1: Write the failing test**

Add to `tests/test_bytecode_io.py`:
```python
import msgpack
import pytest


def test_version_mismatch_raises():
    """Wrong bytecode version fails with clear error."""
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "old.zrc"

        # Write a file with wrong version
        data = {
            "version": 999,
            "program": {"chunks": [], "function_index": {}},
        }
        with open(path, "wb") as f:
            msgpack.pack(data, f)

        with pytest.raises(ValueError, match="version mismatch"):
            load_program(path)
```

**Step 2: Run test to verify it passes**

Run: `cd /Users/calum/Development/zero && python -m pytest tests/test_bytecode_io.py::test_version_mismatch_raises -v`
Expected: PASS (implementation already handles this)

**Step 3: Commit**

```bash
cd /Users/calum/Development/zero && git add tests/test_bytecode_io.py && git commit -m "test: add version mismatch test for bytecode loading"
```

---

## Task 4: Oversized File Test

**Files:**
- Modify: `tests/test_bytecode_io.py`
- Modify: `zero/bytecode.py`

**Step 1: Write the failing test**

Add to `tests/test_bytecode_io.py`:
```python
from zero.bytecode import MAX_BYTECODE_SIZE


def test_load_oversized_file_raises():
    """Files over 10MB rejected before parsing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "huge.zrc"

        # Create file larger than limit
        with open(path, "wb") as f:
            f.write(b"x" * (MAX_BYTECODE_SIZE + 1))

        with pytest.raises(ValueError, match="too large"):
            load_program(path)
```

**Step 2: Run test to verify it passes**

Run: `cd /Users/calum/Development/zero && python -m pytest tests/test_bytecode_io.py::test_load_oversized_file_raises -v`
Expected: PASS (implementation already handles this)

**Step 3: Commit**

```bash
cd /Users/calum/Development/zero && git add tests/test_bytecode_io.py && git commit -m "test: add oversized bytecode file rejection test"
```

---

## Task 5: Corrupt File Test

**Files:**
- Modify: `tests/test_bytecode_io.py`

**Step 1: Write the failing test**

Add to `tests/test_bytecode_io.py`:
```python
def test_load_corrupt_file_raises():
    """Invalid msgpack fails gracefully."""
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "corrupt.zrc"

        with open(path, "wb") as f:
            f.write(b"not valid msgpack data!!!")

        with pytest.raises(Exception):  # msgpack.UnpackException or similar
            load_program(path)
```

**Step 2: Run test to verify it passes**

Run: `cd /Users/calum/Development/zero && python -m pytest tests/test_bytecode_io.py::test_load_corrupt_file_raises -v`
Expected: PASS (msgpack raises on invalid data)

**Step 3: Commit**

```bash
cd /Users/calum/Development/zero && git add tests/test_bytecode_io.py && git commit -m "test: add corrupt bytecode file handling test"
```

---

## Task 6: Cache Path Helper

**Files:**
- Create: `zero/cache.py`
- Create: `tests/test_cache.py`

**Step 1: Write the failing test**

Create `tests/test_cache.py`:
```python
from pathlib import Path

from zero.cache import get_cache_path


def test_cache_path_structure():
    """Cache path is .zr-cache/<name>.zrc relative to source."""
    source = Path("/project/src/main.zr")
    result = get_cache_path(source)
    assert result == Path("/project/src/.zr-cache/main.zrc")


def test_cache_path_nested():
    """Works for nested source files."""
    source = Path("/project/lib/utils/helper.zr")
    result = get_cache_path(source)
    assert result == Path("/project/lib/utils/.zr-cache/helper.zrc")
```

**Step 2: Run test to verify it fails**

Run: `cd /Users/calum/Development/zero && python -m pytest tests/test_cache.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'zero.cache'`

**Step 3: Write minimal implementation**

Create `zero/cache.py`:
```python
from pathlib import Path


def get_cache_path(source_path: Path) -> Path:
    """Return cache path for a source file: .zr-cache/<name>.zrc"""
    cache_dir = source_path.parent / ".zr-cache"
    return cache_dir / f"{source_path.stem}.zrc"


def ensure_cache_dir(source_path: Path) -> Path:
    """Create cache directory if needed, return cache file path."""
    cache_path = get_cache_path(source_path)
    cache_path.parent.mkdir(exist_ok=True)
    return cache_path
```

**Step 4: Run test to verify it passes**

Run: `cd /Users/calum/Development/zero && python -m pytest tests/test_cache.py -v`
Expected: PASS

**Step 5: Commit**

```bash
cd /Users/calum/Development/zero && git add zero/cache.py tests/test_cache.py && git commit -m "feat: add cache path helper for .zr-cache directory"
```

---

## Task 7: Cache Directory Creation Test

**Files:**
- Modify: `tests/test_cache.py`

**Step 1: Write the test**

Add to `tests/test_cache.py`:
```python
import tempfile

from zero.cache import ensure_cache_dir


def test_cache_dir_created():
    """ensure_cache_dir creates .zr-cache directory if missing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        source = Path(tmpdir) / "main.zr"
        source.touch()

        cache_path = ensure_cache_dir(source)

        assert cache_path.parent.exists()
        assert cache_path.parent.name == ".zr-cache"
        assert cache_path.name == "main.zrc"
```

**Step 2: Run test to verify it passes**

Run: `cd /Users/calum/Development/zero && python -m pytest tests/test_cache.py::test_cache_dir_created -v`
Expected: PASS

**Step 3: Commit**

```bash
cd /Users/calum/Development/zero && git add tests/test_cache.py && git commit -m "test: add cache directory creation test"
```

---

## Task 8: CLI Skeleton with Typer

**Files:**
- Modify: `main.py`

**Step 1: Create CLI skeleton**

Replace `main.py` with:
```python
from pathlib import Path

import typer

from zero.bytecode import load_program, save_program
from zero.cache import ensure_cache_dir
from zero.compiler import compile_program
from zero.lexer import tokenize
from zero.parser import parse
from zero.semantic import SemanticError, analyze
from zero.vm import run as vm_run

app = typer.Typer(help="The Zero programming language")


def compile_source(source_path: Path):
    """Compile source file to CompiledProgram."""
    source = source_path.read_text()
    tokens = tokenize(source)
    program = parse(tokens)
    analyze(program)
    return compile_program(program)


@app.command()
def build(
    file: Path = typer.Argument(..., help="Source file to compile (.zr)"),
    output: Path | None = typer.Option(None, "-o", "--output", help="Output path"),
):
    """Compile a .zr file to bytecode."""
    if file.suffix != ".zr":
        typer.echo(f"Error: expected .zr file, got {file.suffix}", err=True)
        raise typer.Exit(1)

    if not file.exists():
        typer.echo(f"Error: file not found: {file}", err=True)
        raise typer.Exit(1)

    try:
        compiled = compile_source(file)
    except SemanticError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)

    out_path = output if output else ensure_cache_dir(file)
    save_program(compiled, out_path)
    typer.echo(f"Compiled to {out_path}")


@app.command(name="run")
def run_cmd(
    file: Path = typer.Argument(..., help="File to run (.zr or .zrc)"),
):
    """Run a .zr or .zrc file."""
    if not file.exists():
        typer.echo(f"Error: file not found: {file}", err=True)
        raise typer.Exit(1)

    try:
        if file.suffix == ".zr":
            compiled = compile_source(file)
        elif file.suffix == ".zrc":
            compiled = load_program(file)
        else:
            typer.echo(f"Error: expected .zr or .zrc file, got {file.suffix}", err=True)
            raise typer.Exit(1)
    except SemanticError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)
    except ValueError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)

    vm_run(compiled)


@app.command()
def disasm(
    file: Path = typer.Argument(..., help="File to disassemble (.zr or .zrc)"),
):
    """Disassemble a .zr or .zrc file."""
    if not file.exists():
        typer.echo(f"Error: file not found: {file}", err=True)
        raise typer.Exit(1)

    try:
        if file.suffix == ".zr":
            compiled = compile_source(file)
        elif file.suffix == ".zrc":
            compiled = load_program(file)
        else:
            typer.echo(f"Error: expected .zr or .zrc file, got {file.suffix}", err=True)
            raise typer.Exit(1)
    except SemanticError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)
    except ValueError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)

    disassemble(compiled)


def disassemble(compiled):
    """Print disassembly of compiled program."""
    from zero.builtins import BUILTIN_INDICES
    from zero.bytecode import Op

    idx_to_name = {v: k for k, v in compiled.function_index.items()}

    for name, idx in compiled.function_index.items():
        chunk = compiled.chunks[idx]
        print(f"== {name} (index={idx}, arity={chunk.arity}) ==")
        if chunk.constants:
            print(f"constants: {chunk.constants}")

        i = 0
        while i < len(chunk.code):
            op = Op(chunk.code[i])
            match op:
                case Op.CONST:
                    const_idx = chunk.code[i + 1]
                    print(f"  {i:04d} CONST {const_idx} ({chunk.constants[const_idx]})")
                    i += 2
                case Op.LOAD:
                    slot = chunk.code[i + 1]
                    print(f"  {i:04d} LOAD {slot}")
                    i += 2
                case Op.STORE:
                    slot = chunk.code[i + 1]
                    print(f"  {i:04d} STORE {slot}")
                    i += 2
                case Op.ADD_INT:
                    print(f"  {i:04d} ADD_INT")
                    i += 1
                case Op.SUB_INT:
                    print(f"  {i:04d} SUB_INT")
                    i += 1
                case Op.MUL_INT:
                    print(f"  {i:04d} MUL_INT")
                    i += 1
                case Op.MOD_INT:
                    print(f"  {i:04d} MOD_INT")
                    i += 1
                case Op.ADD_STR:
                    print(f"  {i:04d} ADD_STR")
                    i += 1
                case Op.CMP_EQ_INT:
                    print(f"  {i:04d} CMP_EQ_INT")
                    i += 1
                case Op.CMP_NE_INT:
                    print(f"  {i:04d} CMP_NE_INT")
                    i += 1
                case Op.CMP_LT_INT:
                    print(f"  {i:04d} CMP_LT_INT")
                    i += 1
                case Op.CMP_GT_INT:
                    print(f"  {i:04d} CMP_GT_INT")
                    i += 1
                case Op.CMP_LE_INT:
                    print(f"  {i:04d} CMP_LE_INT")
                    i += 1
                case Op.CMP_GE_INT:
                    print(f"  {i:04d} CMP_GE_INT")
                    i += 1
                case Op.CMP_EQ_BOOL:
                    print(f"  {i:04d} CMP_EQ_BOOL")
                    i += 1
                case Op.CMP_NE_BOOL:
                    print(f"  {i:04d} CMP_NE_BOOL")
                    i += 1
                case Op.CMP_EQ_STR:
                    print(f"  {i:04d} CMP_EQ_STR")
                    i += 1
                case Op.CMP_NE_STR:
                    print(f"  {i:04d} CMP_NE_STR")
                    i += 1
                case Op.JUMP:
                    addr = chunk.code[i + 1]
                    print(f"  {i:04d} JUMP {addr}")
                    i += 2
                case Op.JUMP_IF_FALSE:
                    addr = chunk.code[i + 1]
                    print(f"  {i:04d} JUMP_IF_FALSE {addr}")
                    i += 2
                case Op.CALL:
                    func_idx = chunk.code[i + 1]
                    argc = chunk.code[i + 2]
                    func_name = idx_to_name.get(func_idx, f"<{func_idx}>")
                    print(f"  {i:04d} CALL {func_idx} ({func_name}), {argc} args")
                    i += 3
                case Op.RET:
                    print(f"  {i:04d} RET")
                    i += 1
                case Op.POP:
                    print(f"  {i:04d} POP")
                    i += 1
                case Op.CALL_BUILTIN:
                    builtin_idx = chunk.code[i + 1]
                    argc = chunk.code[i + 2]
                    builtin_name = next(
                        (k for k, v in BUILTIN_INDICES.items() if v == builtin_idx),
                        f"<builtin {builtin_idx}>"
                    )
                    print(f"  {i:04d} CALL_BUILTIN {builtin_idx} ({builtin_name}), {argc} args")
                    i += 3
        print()


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    file: Path | None = typer.Argument(None, help="File to run (.zr or .zrc)"),
):
    """The Zero programming language."""
    if ctx.invoked_subcommand is None and file is not None:
        run_cmd(file)
    elif ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())


if __name__ == "__main__":
    app()
```

**Step 2: Verify CLI works**

Run: `cd /Users/calum/Development/zero && python main.py --help`
Expected: Help text showing `build`, `run`, `disasm` commands

**Step 3: Commit**

```bash
cd /Users/calum/Development/zero && git add main.py && git commit -m "feat: replace CLI with Typer-based commands"
```

---

## Task 9: Rename Example Files

**Files:**
- Rename: `examples/*.zero` → `examples/*.zr`

**Step 1: Rename all example files**

Run:
```bash
cd /Users/calum/Development/zero/examples && for f in *.zero; do mv "$f" "${f%.zero}.zr"; done
```

**Step 2: Verify files renamed**

Run: `ls /Users/calum/Development/zero/examples/`
Expected: All files now have `.zr` extension

**Step 3: Commit**

```bash
cd /Users/calum/Development/zero && git add examples/ && git commit -m "chore: rename example files from .zero to .zr"
```

---

## Task 10: CLI Integration Tests

**Files:**
- Create: `tests/test_cli.py`

**Step 1: Write CLI tests**

Create `tests/test_cli.py`:
```python
import subprocess
import tempfile
from pathlib import Path


def run_zero(*args):
    """Run zero CLI and return (stdout, stderr, returncode)."""
    result = subprocess.run(
        ["python", "main.py", *args],
        capture_output=True,
        text=True,
        cwd="/Users/calum/Development/zero",
    )
    return result.stdout, result.stderr, result.returncode


def test_run_zr_file():
    """Running .zr file compiles and executes."""
    stdout, stderr, code = run_zero("run", "examples/01_hello.zr")
    assert code == 0
    assert "Hello, World!" in stdout


def test_build_creates_cache():
    """`zero build` creates .zrc in .zr-cache/."""
    with tempfile.TemporaryDirectory() as tmpdir:
        source = Path(tmpdir) / "test.zr"
        source.write_text('fn main() { print("hi") }')

        stdout, stderr, code = run_zero("build", str(source))
        assert code == 0

        cache_file = Path(tmpdir) / ".zr-cache" / "test.zrc"
        assert cache_file.exists()


def test_build_custom_output():
    """`zero build -o` writes to specified path."""
    with tempfile.TemporaryDirectory() as tmpdir:
        source = Path(tmpdir) / "test.zr"
        source.write_text('fn main() { print("hi") }')
        output = Path(tmpdir) / "custom.zrc"

        stdout, stderr, code = run_zero("build", str(source), "-o", str(output))
        assert code == 0
        assert output.exists()


def test_run_zrc_file():
    """Running .zrc file loads and executes."""
    with tempfile.TemporaryDirectory() as tmpdir:
        source = Path(tmpdir) / "test.zr"
        source.write_text('fn main() { print("from bytecode") }')
        output = Path(tmpdir) / "test.zrc"

        # Build first
        run_zero("build", str(source), "-o", str(output))

        # Run bytecode
        stdout, stderr, code = run_zero("run", str(output))
        assert code == 0
        assert "from bytecode" in stdout


def test_disasm_zr_file():
    """Disassemble .zr file shows bytecode."""
    stdout, stderr, code = run_zero("disasm", "examples/01_hello.zr")
    assert code == 0
    assert "main" in stdout
    assert "CALL_BUILTIN" in stdout


def test_run_missing_file():
    """Missing file gives clear error."""
    stdout, stderr, code = run_zero("run", "nonexistent.zr")
    assert code == 1
    assert "not found" in stderr


def test_build_invalid_source():
    """Parse errors reported properly."""
    with tempfile.TemporaryDirectory() as tmpdir:
        source = Path(tmpdir) / "bad.zr"
        source.write_text("this is not valid zero code {{{")

        stdout, stderr, code = run_zero("build", str(source))
        assert code == 1
```

**Step 2: Run tests**

Run: `cd /Users/calum/Development/zero && python -m pytest tests/test_cli.py -v`
Expected: All tests pass

**Step 3: Commit**

```bash
cd /Users/calum/Development/zero && git add tests/test_cli.py && git commit -m "test: add CLI integration tests"
```

---

## Task 11: Update Documentation

**Files:**
- Modify: `CLAUDE.md`
- Modify: `README.md`

**Step 1: Update CLAUDE.md**

Update the Build & Run Commands section to reflect new CLI:
```markdown
## Build & Run Commands

```bash
# Install dependencies
uv sync

# Run all tests
python -m pytest -v

# Run single test file
python -m pytest tests/test_lexer.py -v

# Execute a Zero program
zero run examples/01_hello.zr
# or directly:
zero examples/01_hello.zr

# Compile to bytecode
zero build examples/01_hello.zr          # → .zr-cache/01_hello.zrc
zero build examples/01_hello.zr -o out.zrc  # → out.zrc

# Run compiled bytecode
zero run out.zrc

# Disassemble (view bytecode)
zero disasm examples/01_hello.zr
zero disasm out.zrc
```
```

Also update file extension references from `.zero` to `.zr`.

**Step 2: Update README.md**

Update any references to `.zero` to use `.zr` extension.

**Step 3: Commit**

```bash
cd /Users/calum/Development/zero && git add CLAUDE.md README.md && git commit -m "docs: update documentation for new CLI and .zr extension"
```

---

## Task 12: Update VS Code Extension

**Files:**
- Modify: `zero-vscode/package.json`
- Modify: `zero-vscode/syntaxes/zero.tmLanguage.json`

**Step 1: Check current VS Code extension files**

Read the extension config to understand current structure.

**Step 2: Update file extension from .zero to .zr**

In `package.json`, update the `languages` section to use `.zr` instead of `.zero`.

**Step 3: Test extension locally**

Verify syntax highlighting works with `.zr` files.

**Step 4: Commit**

```bash
cd /Users/calum/Development/zero && git add zero-vscode/ && git commit -m "chore: update VS Code extension to use .zr extension"
```

---

## Task 13: Update .gitignore

**Files:**
- Modify: `.gitignore`

**Step 1: Add cache directory to gitignore**

Add to `.gitignore`:
```
.zr-cache/
*.zrc
```

**Step 2: Commit**

```bash
cd /Users/calum/Development/zero && git add .gitignore && git commit -m "chore: ignore .zr-cache directory and .zrc files"
```

---

## Task 14: Run Full Test Suite

**Step 1: Run all tests**

Run: `cd /Users/calum/Development/zero && python -m pytest -v`
Expected: All tests pass

**Step 2: Manual smoke test**

Run:
```bash
cd /Users/calum/Development/zero
zero build examples/01_hello.zr
zero run .zr-cache/01_hello.zrc
zero disasm examples/01_hello.zr
```
Expected: All commands work correctly

---

## Summary

| Task | What |
|------|------|
| 1 | Add dependencies |
| 2-5 | Bytecode serialization with tests |
| 6-7 | Cache directory helper |
| 8 | Typer CLI skeleton |
| 9 | Rename example files |
| 10 | CLI integration tests |
| 11 | Update docs |
| 12 | Update VS Code extension |
| 13 | Update gitignore |
| 14 | Full test suite |
