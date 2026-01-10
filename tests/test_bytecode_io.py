import tempfile
from pathlib import Path

import msgpack
import pytest

from zero.bytecode import Chunk, CompiledProgram, save_program, load_program, MAX_BYTECODE_SIZE


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


def test_load_oversized_file_raises():
    """Files over 10MB rejected before parsing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "huge.zrc"

        # Create file larger than limit
        with open(path, "wb") as f:
            f.write(b"x" * (MAX_BYTECODE_SIZE + 1))

        with pytest.raises(ValueError, match="too large"):
            load_program(path)


def test_load_corrupt_file_raises():
    """Invalid msgpack fails gracefully."""
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "corrupt.zrc"

        with open(path, "wb") as f:
            f.write(b"not valid msgpack data!!!")

        with pytest.raises(Exception):  # msgpack.UnpackException or similar
            load_program(path)
