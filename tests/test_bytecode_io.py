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
