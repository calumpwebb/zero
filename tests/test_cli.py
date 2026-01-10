import subprocess
import tempfile
from pathlib import Path

ZERO_ROOT = Path("/Users/calum/Development/zero")


def run_zero(*args):
    """Run zero CLI and return (stdout, stderr, returncode)."""
    result = subprocess.run(
        ["uv", "run", "python", "main.py", *args],
        capture_output=True,
        text=True,
        cwd=ZERO_ROOT,
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


def test_disasm_zrc_file():
    """Disassemble .zrc file shows bytecode."""
    with tempfile.TemporaryDirectory() as tmpdir:
        source = Path(tmpdir) / "test.zr"
        source.write_text('fn main() { print("test") }')
        output = Path(tmpdir) / "test.zrc"

        run_zero("build", str(source), "-o", str(output))

        stdout, stderr, code = run_zero("disasm", str(output))
        assert code == 0
        assert "main" in stdout


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
